#include "sd_card_driver.h"

#include "sd_card_csd.h"

#include "spi_devices.h"
#include "stm32f4xx_hal.h"

#include <string.h>

/* SD cards expose a fixed 512-byte logical sector in SPI mode. */
#define SD_BLOCK_SIZE 512U

/* SPI command indexes from the SD Physical Layer specification. */
#define SD_COMMAND_GO_IDLE_STATE 0U       /* CMD0 */
#define SD_COMMAND_SEND_IF_COND 8U        /* CMD8 */
#define SD_COMMAND_SEND_CSD 9U            /* CMD9 */
#define SD_COMMAND_SET_BLOCKLEN 16U       /* CMD16 */
#define SD_COMMAND_READ_SINGLE_BLOCK 17U  /* CMD17 */
#define SD_COMMAND_WRITE_SINGLE_BLOCK 24U /* CMD24 */
#define SD_COMMAND_APP_COMMAND 55U        /* CMD55 */
#define SD_COMMAND_READ_OCR 58U           /* CMD58 */
#define SD_ACOMMAND_SEND_OP_COND 41U      /* ACMD41, after CMD55 */

#define SD_RESPONSE_ATTEMPTS 16U
#define SD_READY_TIMEOUT_MS 1000U
#define SD_DATA_TIMEOUT_MS 250U
#define SD_DATA_START_TOKEN 0xFEU
#define SD_DATA_ACCEPTED 0x05U
#define SD_TEST_AREA_DISTANCE_FROM_END 16U

static spi_device_t *device;
static bool high_capacity;

/* One sector is enough RAM: operations are intentionally one sector per call. */
static uint8_t test_block[SD_BLOCK_SIZE];
static uint8_t received_block[SD_BLOCK_SIZE];
static uint32_t write_checksum;
static uint32_t verify_checksum;

/* CRC-32 records the complete deterministic data set, independent of the card. */
static uint32_t checksum_update(uint32_t checksum, const uint8_t *buffer, uint32_t length)
{
    for (uint32_t index = 0U; index < length; index++) {
        checksum ^= buffer[index];
        for (uint32_t bit = 0U; bit < 8U; bit++) {
            checksum = (checksum >> 1U) ^
                ((checksum & 1U) ? 0xEDB88320U : 0U);
        }
    }
    return checksum;
}

/* Every SPI byte simultaneously sends one byte and receives one byte. */
static bool transfer_byte(uint8_t transmitted, uint8_t *received)
{
    return spi_device_transfer(device, &transmitted, received, 1U);
}

/*
 * Clock arbitrary bytes.  Sending 0xFF is the normal idle value and lets an
 * SD card return a response or data while the MCU supplies the clock edges.
 */
static bool clock_bytes(uint8_t value, uint32_t count)
{
    uint8_t received;

    for (uint32_t index = 0U; index < count; index++) {
        if (!transfer_byte(value, &received)) {
            return false;
        }
    }
    return true;
}

/* Read bytes by generating one byte of idle clocks for each received byte. */
static bool read_bytes(uint8_t *buffer, uint32_t length)
{
    for (uint32_t index = 0U; index < length; index++) {
        if (!transfer_byte(0xFFU, &buffer[index])) {
            return false;
        }
    }
    return true;
}

/*
 * A card returns 0xFF on MISO when it is not busy.  Programming internal flash
 * after a write may keep MISO low for a short time, so poll with a hard limit.
 */
static bool wait_ready(uint32_t timeout_ms)
{
    const uint32_t started = HAL_GetTick();
    uint8_t value;

    do {
        if (!transfer_byte(0xFFU, &value)) {
            return false;
        }
        if (value == 0xFFU) {
            return true;
        }
    } while ((uint32_t)(HAL_GetTick() - started) < timeout_ms);

    return false;
}

/*
 * Send a six-byte SD SPI command frame: 01 + command index, four big-endian
 * argument bytes, and a CRC byte.  The caller has already selected the card.
 * The response can be delayed by a few bytes, hence the 16 idle-byte polls.
 */
static bool command(uint8_t index, uint32_t argument, uint8_t crc, uint8_t *response)
{
    uint8_t frame[6] = {
        (uint8_t)(0x40U | index),
        (uint8_t)(argument >> 24U),
        (uint8_t)(argument >> 16U),
        (uint8_t)(argument >> 8U),
        (uint8_t)argument,
        crc,
    };
    uint8_t discarded_during_command[sizeof(frame)];

    if (!spi_device_transfer(device, frame, discarded_during_command, sizeof(frame))) {
        return false;
    }
    for (uint32_t attempt = 0U; attempt < SD_RESPONSE_ATTEMPTS; attempt++) {
        if (!transfer_byte(0xFFU, response)) {
            return false;
        }
        /* An R1 response has bit 7 clear; 0xFF still means no response. */
        if ((*response & 0x80U) == 0U) {
            return true;
        }
    }
    return false;
}

/* SDHC/SDXC commands use sector addresses; SDSC commands use byte addresses. */
static uint32_t wire_address(uint32_t sector)
{
    return high_capacity ? sector : sector * SD_BLOCK_SIZE;
}

/* Selecting a normal, initialized card also requires it to be ready. */
static bool select_card(void)
{
    return spi_device_select(device) && wait_ready(SD_READY_TIMEOUT_MS);
}

/* An extra byte clocked with CS high is required between independent commands. */
static void deselect_card(void)
{
    spi_device_deselect(device);
    (void)clock_bytes(0xFFU, 1U);
}

/* Wait for the 0xFE token that announces a CSD or sector data payload. */
static bool wait_for_data_token(void)
{
    const uint32_t started = HAL_GetTick();
    uint8_t token;

    do {
        if (!transfer_byte(0xFFU, &token)) {
            return false;
        }
    } while (token == 0xFFU &&
             (uint32_t)(HAL_GetTick() - started) < SD_DATA_TIMEOUT_MS);

    return token == SD_DATA_START_TOKEN;
}

/* CMD9 obtains the CSD register, from which the usable sector count is derived. */
static bool read_csd(sd_card_information_t *information)
{
    uint8_t response;
    uint8_t csd[16];
    uint8_t discarded_card_crc[2];

    if (!select_card() ||
        !command(SD_COMMAND_SEND_CSD, 0U, 0xFFU, &response) ||
        response != 0U ||
        !wait_for_data_token() ||
        !read_bytes(csd, sizeof(csd)) ||
        !read_bytes(discarded_card_crc, sizeof(discarded_card_crc))) {
        deselect_card();
        return false;
    }
    deselect_card();

    if (!sd_card_parse_csd(csd, &information->sector_count)) {
        return false;
    }

    /* The test starts 16 sectors before the end and consumes eight sectors. */
    return information->sector_count > SD_TEST_AREA_DISTANCE_FROM_END;
}

bool sd_card_driver_initialize(sd_card_information_t *information)
{
    uint8_t response;
    uint8_t r7[4];
    uint8_t ocr[4];
    bool version_two;

    if (information == NULL) {
        return false;
    }

    device = flightcomputer_v1_sd_spi_device();
    if (!spi_device_initialize(device)) {
        return false;
    }

    /* 1. With CS high, give the card at least 74 initial SPI clock edges. */
    if (!clock_bytes(0xFFU, 10U)) {
        return false;
    }

    /* 2. CMD0 resets the card and must return R1=0x01 (idle state). */
    if (!spi_device_select(device) ||
        !command(SD_COMMAND_GO_IDLE_STATE, 0U, 0x95U, &response) ||
        response != 1U) {
        deselect_card();
        return false;
    }
    deselect_card();

    /* 3. CMD8 distinguishes v2 cards and verifies the voltage/check pattern. */
    if (!select_card() ||
        !command(SD_COMMAND_SEND_IF_COND, 0x1AAU, 0x87U, &response)) {
        deselect_card();
        return false;
    }
    if (response == 1U) {
        version_two = read_bytes(r7, sizeof(r7)) &&
            r7[2] == 1U &&
            r7[3] == 0xAAU;
        if (!version_two) {
            deselect_card();
            return false;
        }
    } else if (response == 5U) {
        /* R1=idle+illegal-command is the expected CMD8 response from a v1 card. */
        version_two = false;
    } else {
        deselect_card();
        return false;
    }
    deselect_card();

    /*
     * 4. CMD55 makes the following ACMD41 an application command.  Repeat the
     * pair until the card changes from idle R1=0x01 to ready R1=0x00.
     */
    const uint32_t started = HAL_GetTick();
    do {
        uint8_t application_response;

        if (!select_card() ||
            !command(
                SD_COMMAND_APP_COMMAND, 0U, 0xFFU, &application_response
            ) ||
            (application_response != 0U && application_response != 1U) ||
            !command(
                SD_ACOMMAND_SEND_OP_COND,
                version_two ? 0x40000000U : 0U,
                0xFFU,
                &response
            )) {
            deselect_card();
            return false;
        }
        deselect_card();
        if (response == 0U) {
            break;
        }
    } while ((uint32_t)(HAL_GetTick() - started) < SD_READY_TIMEOUT_MS);

    /* 5. CMD58 returns OCR; its CCS bit identifies block versus byte addressing. */
    if (response != 0U ||
        !select_card() ||
        !command(SD_COMMAND_READ_OCR, 0U, 0xFFU, &response) ||
        response != 0U ||
        !read_bytes(ocr, sizeof(ocr))) {
        deselect_card();
        return false;
    }
    high_capacity = version_two && (ocr[0] & 0x40U) != 0U;
    deselect_card();

    /* 6. SDSC needs CMD16 to select 512-byte blocks; SDHC/SDXC already use them. */
    if (!high_capacity &&
        (!select_card() ||
         !command(SD_COMMAND_SET_BLOCKLEN, SD_BLOCK_SIZE, 0xFFU, &response) ||
         response != 0U)) {
        deselect_card();
        return false;
    }
    deselect_card();

    /* 7. CMD9 provides capacity and lets us choose a safe raw test location. */
    information->high_capacity = high_capacity;
    if (!read_csd(information)) {
        return false;
    }
    information->test_sector = (uint32_t)(
        information->sector_count - SD_TEST_AREA_DISTANCE_FROM_END
    );

    /* 8. Initialization is done: raise SPI1 from 328.125 kHz to 21 MHz. */
    return spi_device_set_prescaler(device, SPI_BAUDRATEPRESCALER_4);
}

/* Recreate one unique, deterministic sector without holding all eight in RAM. */
static void pattern(uint8_t *buffer, uint32_t sector)
{
    for (uint32_t index = 0U; index < SD_BLOCK_SIZE; index++) {
        buffer[index] = (uint8_t)(sector + index * 37U);
    }
}

/* CMD24 followed by one complete 512-byte data block. */
static bool write_block(uint32_t sector, const uint8_t *buffer)
{
    uint8_t response;

    if (!select_card() ||
        !command(SD_COMMAND_WRITE_SINGLE_BLOCK, wire_address(sector), 0xFFU, &response) ||
        response != 0U ||
        !wait_ready(SD_READY_TIMEOUT_MS)) {
        deselect_card();
        return false;
    }

    /* Data token, payload, two ignored card-CRC bytes, then acceptance response. */
    if (!transfer_byte(SD_DATA_START_TOKEN, &response) ||
        !spi_device_transfer(device, buffer, received_block, SD_BLOCK_SIZE) ||
        !transfer_byte(0xFFU, &response) ||
        !transfer_byte(0xFFU, &response) ||
        !transfer_byte(0xFFU, &response) ||
        (response & 0x1FU) != SD_DATA_ACCEPTED ||
        !wait_ready(SD_READY_TIMEOUT_MS)) {
        deselect_card();
        return false;
    }

    deselect_card();
    return true;
}

/* CMD17 followed by one complete 512-byte data block. */
static bool read_block(uint32_t sector, uint8_t *buffer)
{
    uint8_t response;
    uint8_t discarded_card_crc[2];

    if (!select_card() ||
        !command(SD_COMMAND_READ_SINGLE_BLOCK, wire_address(sector), 0xFFU, &response) ||
        response != 0U ||
        !wait_for_data_token() ||
        !read_bytes(buffer, SD_BLOCK_SIZE) ||
        !read_bytes(discarded_card_crc, sizeof(discarded_card_crc))) {
        deselect_card();
        return false;
    }

    deselect_card();
    return true;
}

bool sd_card_driver_write_test_block(sd_card_information_t *information, uint32_t block)
{
    if (information == NULL || block >= SD_CARD_TEST_BLOCK_COUNT) {
        return false;
    }
    if (block == 0U) {
        write_checksum = 0xFFFFFFFFU;
    }

    pattern(test_block, information->test_sector + block);
    write_checksum = checksum_update(write_checksum, test_block, sizeof(test_block));
    if (!write_block(information->test_sector + block, test_block)) {
        return false;
    }

    if (block == SD_CARD_TEST_BLOCK_COUNT - 1U) {
        information->checksum = ~write_checksum;
    }
    return true;
}

bool sd_card_driver_verify_test_block(const sd_card_information_t *information, uint32_t block)
{
    if (information == NULL || block >= SD_CARD_TEST_BLOCK_COUNT) {
        return false;
    }
    if (block == 0U) {
        verify_checksum = 0xFFFFFFFFU;
    }

    pattern(test_block, information->test_sector + block);
    if (!read_block(information->test_sector + block, received_block) ||
        memcmp(test_block, received_block, SD_BLOCK_SIZE) != 0) {
        return false;
    }

    verify_checksum = checksum_update(
        verify_checksum, received_block, sizeof(received_block)
    );
    return block != SD_CARD_TEST_BLOCK_COUNT - 1U ||
        ~verify_checksum == information->checksum;
}

bool sd_card_driver_clear_test_block(const sd_card_information_t *information, uint32_t block)
{
    if (information == NULL || block >= SD_CARD_TEST_BLOCK_COUNT) {
        return false;
    }

    memset(test_block, 0, sizeof(test_block));
    return write_block(information->test_sector + block, test_block);
}

void sd_card_driver_shutdown(void)
{
    if (device != NULL) {
        deselect_card();
    }
}
