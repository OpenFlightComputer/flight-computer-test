#include "bmp388_driver.h"

#include "barometer_i2c.h"
#include "bmp3.h"
#include "stm32f4xx_hal.h"

#include <limits.h>
#include <string.h>

#define BMP388_I2C_ADDRESS 0x76U

static struct bmp3_dev bmp388_device;
static bool bmp388_ready;

static BMP3_INTF_RET_TYPE i2c_read(
    uint8_t register_address, uint8_t *data, uint32_t length, void *context
)
{
    (void)context;
    return data != NULL && length <= UINT16_MAX &&
        flightcomputer_v1_barometer_i2c_read(
            BMP388_I2C_ADDRESS, register_address, data, (size_t)length
        ) ? BMP3_OK : BMP3_E_COMM_FAIL;
}

static BMP3_INTF_RET_TYPE i2c_write(
    uint8_t register_address, const uint8_t *data, uint32_t length, void *context
)
{
    (void)context;
    return data != NULL && length <= UINT16_MAX &&
        flightcomputer_v1_barometer_i2c_write(
            BMP388_I2C_ADDRESS, register_address, data, (size_t)length
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
    const uint16_t selected_settings = BMP3_SEL_PRESS_EN | BMP3_SEL_TEMP_EN |
        BMP3_SEL_PRESS_OS | BMP3_SEL_TEMP_OS | BMP3_SEL_ODR;

    bmp388_ready = false;
    memset(&bmp388_device, 0, sizeof(bmp388_device));
    bmp388_device.intf = BMP3_I2C_INTF;
    bmp388_device.read = i2c_read;
    bmp388_device.write = i2c_write;
    bmp388_device.delay_us = delay_us;
    if (bmp3_init(&bmp388_device) != BMP3_OK) {
        return false;
    }

    /* 25 Hz is faster than the 5 Hz tester display and leaves fresh samples. */
    settings.press_en = BMP3_ENABLE;
    settings.temp_en = BMP3_ENABLE;
    settings.odr_filter.press_os = BMP3_OVERSAMPLING_4X;
    settings.odr_filter.temp_os = BMP3_NO_OVERSAMPLING;
    settings.odr_filter.odr = BMP3_ODR_25_HZ;
    if (bmp3_set_sensor_settings(selected_settings, &settings, &bmp388_device) !=
        BMP3_OK) {
        return false;
    }
    settings.op_mode = BMP3_MODE_NORMAL;
    if (bmp3_set_op_mode(&settings, &bmp388_device) != BMP3_OK) {
        return false;
    }
    bmp388_ready = true;
    return true;
}

bool bmp388_driver_read_sample(bmp388_sample_t *sample)
{
    struct bmp3_data data = {0};

    if (!bmp388_ready || sample == NULL ||
        bmp3_get_sensor_data(BMP3_PRESS_TEMP, &data, &bmp388_device) != BMP3_OK ||
        data.pressure > INT32_MAX || data.temperature > INT32_MAX ||
        data.temperature < INT32_MIN) {
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
