#include "bmp388_driver.h"

#include "barometer_i2c.h"
#include "bmp3.h"
#include "stm32f4xx_hal.h"

#include <limits.h>
#include <string.h>

#define BMP388_I2C_ADDRESS 0x76U

static uint8_t bmp388_address = BMP388_I2C_ADDRESS;
static struct bmp3_dev bmp388_device;
static bool bmp388_ready;
static bmp388_failure_t last_failure;

static const char *failure_reason(int8_t result)
{
    switch (result) {
    case BMP3_E_COMM_FAIL:
        return "i2c_communication_failed";
    case BMP3_E_DEV_NOT_FOUND:
        return "unexpected_or_missing_chip_id";
    case BMP3_E_INVALID_ODR_OSR_SETTINGS:
        return "invalid_sampling_settings";
    case BMP3_E_CMD_EXEC_FAILED:
        return "sensor_command_failed";
    case BMP3_E_CONFIGURATION_ERR:
        return "sensor_configuration_error";
    default:
        return "bosch_driver_error";
    }
}

static bool driver_failed(const char *stage, int8_t result)
{
    last_failure = (bmp388_failure_t){
        .stage = stage,
        .reason = failure_reason(result),
        .code = result,
    };
    return false;
}

static BMP3_INTF_RET_TYPE i2c_read(
    uint8_t register_address, uint8_t *data, uint32_t length, void *context
)
{
    const uint8_t *address = context;
    return address != NULL && data != NULL && length <= UINT16_MAX &&
        flightcomputer_v1_barometer_i2c_read(
            *address, register_address, data, (size_t)length
        ) ? BMP3_OK : BMP3_E_COMM_FAIL;
}

static BMP3_INTF_RET_TYPE i2c_write(
    uint8_t register_address, const uint8_t *data, uint32_t length, void *context
)
{
    const uint8_t *address = context;
    return address != NULL && data != NULL && length <= UINT16_MAX &&
        flightcomputer_v1_barometer_i2c_write(
            *address, register_address, data, (size_t)length
        ) ? BMP3_OK : BMP3_E_COMM_FAIL;
}

static void delay_us(uint32_t period, void *context)
{
    (void)context;
    /* BMP388 initialization only needs millisecond-scale waits in this test. */
    HAL_Delay((period + 999U) / 1000U);
}

bool bmp388_driver_initialize(void)
{
    struct bmp3_settings settings = {0};
    int8_t result;
    uint32_t hal_error;
    const uint16_t selected_settings = BMP3_SEL_PRESS_EN | BMP3_SEL_TEMP_EN |
        BMP3_SEL_PRESS_OS | BMP3_SEL_TEMP_OS | BMP3_SEL_ODR;

    bmp388_ready = false;
    last_failure = (bmp388_failure_t){0};
    memset(&bmp388_device, 0, sizeof(bmp388_device));
    bmp388_device.intf = BMP3_I2C_INTF;
    bmp388_device.read = i2c_read;
    bmp388_device.write = i2c_write;
    bmp388_device.delay_us = delay_us;
    /* Bosch requires a non-null bus context and passes it to every callback. */
    bmp388_device.intf_ptr = &bmp388_address;
    if (!flightcomputer_v1_barometer_i2c_probe(
            BMP388_I2C_ADDRESS, &hal_error
        )) {
        last_failure = (bmp388_failure_t){
            .stage = "i2c_address_probe",
            .reason = "no_acknowledgement_at_0x76",
            .code = (int32_t)hal_error,
        };
        return false;
    }
    result = bmp3_init(&bmp388_device);
    if (result != BMP3_OK) {
        return driver_failed("chip_id_and_calibration", result);
    }

    /* 25 Hz is faster than the 5 Hz tester display and leaves fresh samples. */
    settings.press_en = BMP3_ENABLE;
    settings.temp_en = BMP3_ENABLE;
    settings.odr_filter.press_os = BMP3_OVERSAMPLING_4X;
    settings.odr_filter.temp_os = BMP3_NO_OVERSAMPLING;
    settings.odr_filter.odr = BMP3_ODR_25_HZ;
    result = bmp3_set_sensor_settings(
        selected_settings, &settings, &bmp388_device
    );
    if (result != BMP3_OK) {
        return driver_failed("sampling_configuration", result);
    }
    settings.op_mode = BMP3_MODE_NORMAL;
    result = bmp3_set_op_mode(&settings, &bmp388_device);
    if (result != BMP3_OK) {
        return driver_failed("normal_mode", result);
    }
    bmp388_ready = true;
    return true;
}

bool bmp388_driver_read_sample(bmp388_sample_t *sample)
{
    struct bmp3_data data = {0};
    int8_t result;

    if (!bmp388_ready || sample == NULL) {
        last_failure = (bmp388_failure_t){
            .stage = "sample_read",
            .reason = "driver_not_ready_or_null_destination",
            .code = 0,
        };
        return false;
    }
    result = bmp3_get_sensor_data(BMP3_PRESS_TEMP, &data, &bmp388_device);
    if (result != BMP3_OK) {
        return driver_failed("sample_read", result);
    }
    if (data.pressure > INT32_MAX || data.temperature > INT32_MAX ||
        data.temperature < INT32_MIN) {
        last_failure = (bmp388_failure_t){
            .stage = "sample_conversion",
            .reason = "compensated_value_out_of_range",
            .code = 0,
        };
        return false;
    }
    sample->pressure_centi_pa = (int32_t)data.pressure;
    sample->temperature_centi_c = (int32_t)data.temperature;
    return true;
}

void bmp388_driver_shutdown(void)
{
    struct bmp3_settings settings = {0};

    if (bmp388_ready) {
        settings.op_mode = BMP3_MODE_SLEEP;
        (void)bmp3_set_op_mode(&settings, &bmp388_device);
    }
    bmp388_ready = false;
}

const bmp388_failure_t *bmp388_driver_last_failure(void)
{
    return &last_failure;
}
