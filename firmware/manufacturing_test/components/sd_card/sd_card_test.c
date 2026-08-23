#include "component_registry.h"

#include "sd_card/sd_card_driver.h"
#include "spi_devices.h"
#include "stm32f4xx_hal.h"

/*
 * This test deliberately has no operator pass/fail decision.  It begins from
 * a known no-card state, then the firmware owns initialization, eight raw
 * sector writes, byte-for-byte verification, and zero-fill cleanup.
 */
typedef enum {
    SD_CARD_ANNOUNCE_REMOVAL,
    SD_CARD_WAITING_FOR_REMOVAL,
    SD_CARD_ANNOUNCE_INSERTION,
    SD_CARD_WAITING_FOR_INSERTION,
    SD_CARD_INITIALIZING,
    SD_CARD_WRITING,
    SD_CARD_VERIFYING,
    SD_CARD_CLEANING_UP,
    SD_CARD_COMPLETE,
    SD_CARD_FAILED,
} sd_card_test_state_t;

#define SD_CARD_POLL_INTERVAL_MS 20U
#define SD_CARD_STABLE_POLLS 3U

static sd_card_test_state_t state;
static uint32_t next_poll_at;
static uint8_t matching_polls;
static uint32_t current_block;
static component_test_event_t latest_event;
static sd_card_information_t information;

static void message(const char *name)
{
    latest_event = (component_test_event_t){
        .kind = COMPONENT_TEST_EVENT_MESSAGE,
        .name = name,
    };
}

static void card_information_event(const char *name)
{
    latest_event = (component_test_event_t){
        .kind = COMPONENT_TEST_EVENT_SD_CARD_INFO,
        .name = name,
        .sector_count = information.sector_count,
        .test_sector = information.test_sector,
        .checksum = information.checksum,
        .high_capacity = information.high_capacity,
    };
}

static bool stable_card_state(bool inserted)
{
    const uint32_t now = HAL_GetTick();
    if ((int32_t)(now - next_poll_at) < 0) {
        return false;
    }
    next_poll_at = now + SD_CARD_POLL_INTERVAL_MS;
    if (flightcomputer_v1_sd_card_inserted() == inserted) {
        matching_polls++;
    } else {
        matching_polls = 0U;
    }
    return matching_polls >= SD_CARD_STABLE_POLLS;
}

static bool card_is_present(void)
{
    return flightcomputer_v1_sd_card_inserted();
}

void sd_card_test_start(const component_test_parameters_t *parameters)
{
    (void)parameters;
    information = (sd_card_information_t){0};
    matching_polls = 0U;
    current_block = 0U;
    next_poll_at = HAL_GetTick();
    if (card_is_present()) {
        state = SD_CARD_ANNOUNCE_REMOVAL;
    } else {
        state = SD_CARD_ANNOUNCE_INSERTION;
    }
}

component_test_process_result_t sd_card_test_process(void)
{
    switch (state) {
    case SD_CARD_ANNOUNCE_REMOVAL:
        state = SD_CARD_WAITING_FOR_REMOVAL;
        message("sd_card_remove_required");
        return COMPONENT_TEST_PROCESS_EVENT;

    case SD_CARD_WAITING_FOR_REMOVAL:
        if (!stable_card_state(false)) {
            return COMPONENT_TEST_PROCESS_RUNNING;
        }
        state = SD_CARD_ANNOUNCE_INSERTION;
        matching_polls = 0U;
        message("sd_card_removed");
        return COMPONENT_TEST_PROCESS_EVENT;

    case SD_CARD_ANNOUNCE_INSERTION:
        state = SD_CARD_WAITING_FOR_INSERTION;
        message("sd_card_insert_required");
        return COMPONENT_TEST_PROCESS_EVENT;

    case SD_CARD_WAITING_FOR_INSERTION:
        if (!stable_card_state(true)) {
            return COMPONENT_TEST_PROCESS_RUNNING;
        }
        state = SD_CARD_INITIALIZING;
        message("sd_card_detected");
        return COMPONENT_TEST_PROCESS_EVENT;

    case SD_CARD_INITIALIZING:
        if (!card_is_present() || !sd_card_driver_initialize(&information)) {
            state = SD_CARD_FAILED;
            return COMPONENT_TEST_PROCESS_FAILED;
        }
        state = SD_CARD_WRITING;
        card_information_event("sd_card_initialized");
        return COMPONENT_TEST_PROCESS_EVENT;

    case SD_CARD_WRITING:
        if (!card_is_present() ||
            !sd_card_driver_write_test_block(&information, current_block)) {
            state = SD_CARD_FAILED;
            return COMPONENT_TEST_PROCESS_FAILED;
        }
        if (++current_block < SD_CARD_TEST_BLOCK_COUNT) {
            return COMPONENT_TEST_PROCESS_RUNNING;
        }
        state = SD_CARD_VERIFYING;
        current_block = 0U;
        card_information_event("sd_card_written");
        return COMPONENT_TEST_PROCESS_EVENT;

    case SD_CARD_VERIFYING:
        if (!card_is_present() ||
            !sd_card_driver_verify_test_block(&information, current_block)) {
            state = SD_CARD_FAILED;
            return COMPONENT_TEST_PROCESS_FAILED;
        }
        if (++current_block < SD_CARD_TEST_BLOCK_COUNT) {
            return COMPONENT_TEST_PROCESS_RUNNING;
        }
        state = SD_CARD_CLEANING_UP;
        current_block = 0U;
        card_information_event("sd_card_verified");
        return COMPONENT_TEST_PROCESS_EVENT;

    case SD_CARD_CLEANING_UP:
        if (!card_is_present() ||
            !sd_card_driver_clear_test_block(&information, current_block)) {
            state = SD_CARD_FAILED;
            return COMPONENT_TEST_PROCESS_FAILED;
        }
        if (++current_block < SD_CARD_TEST_BLOCK_COUNT) {
            return COMPONENT_TEST_PROCESS_RUNNING;
        }
        state = SD_CARD_COMPLETE;
        card_information_event("sd_card_cleaned_up");
        return COMPONENT_TEST_PROCESS_EVENT;

    case SD_CARD_COMPLETE:
        return COMPONENT_TEST_PROCESS_PASSED;

    case SD_CARD_FAILED:
        return COMPONENT_TEST_PROCESS_FAILED;
    }
    return COMPONENT_TEST_PROCESS_FAILED;
}

const component_test_event_t *sd_card_test_event(void)
{
    return &latest_event;
}

void sd_card_test_stop(void)
{
    sd_card_driver_shutdown();
}
