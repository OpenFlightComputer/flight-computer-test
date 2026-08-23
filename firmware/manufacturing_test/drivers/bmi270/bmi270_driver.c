#include "bmi270_driver.h"

#include "spi_devices.h"
#include "bmi270.h"

#include <string.h>

#define BMI270_SPI_BUFFER_CAPACITY 64U

static struct bmi2_dev bmi270_device;
static bool bmi270_ready;

static int8_t spi_read(uint8_t register_address, uint8_t *data, uint32_t length, void *context)
{
    uint8_t transmit[BMI270_SPI_BUFFER_CAPACITY] = {0};
    uint8_t receive[BMI270_SPI_BUFFER_CAPACITY] = {0};
    (void)context;
    if (data == NULL || length + 1U > sizeof(transmit)) {
        return BMI2_E_COM_FAIL;
    }
    /* Bit 7 requests a BMI270 SPI read; following bytes generate dummy clocks. */
    transmit[0] = register_address | BMI2_SPI_RD_MASK;
    spi_device_t *device = flightcomputer_v1_imu_spi_device();
    if (!spi_device_select(device) || !spi_device_transfer(
            device, transmit, receive, length + 1U
        )) {
        spi_device_deselect(device);
        return BMI2_E_COM_FAIL;
    }
    spi_device_deselect(device);
    memcpy(data, &receive[1], length);
    return BMI2_OK;
}

static int8_t spi_write(uint8_t register_address, const uint8_t *data, uint32_t length, void *context)
{
    uint8_t transmit[BMI270_SPI_BUFFER_CAPACITY] = {0};
    uint8_t receive[BMI270_SPI_BUFFER_CAPACITY] = {0};
    (void)context;
    if (data == NULL || length + 1U > sizeof(transmit)) {
        return BMI2_E_COM_FAIL;
    }
    transmit[0] = register_address & (uint8_t)~BMI2_SPI_RD_MASK;
    memcpy(&transmit[1], data, length);
    spi_device_t *device = flightcomputer_v1_imu_spi_device();
    const bool success = spi_device_select(device) && spi_device_transfer(
        device, transmit, receive, length + 1U
    );
    spi_device_deselect(device);
    return success ? BMI2_OK : BMI2_E_COM_FAIL;
}

static void delay_us(uint32_t period, void *context)
{
    (void)context;
    flightcomputer_v1_delay_us(period);
}

bool bmi270_driver_initialize(void)
{
    struct bmi2_sens_config configuration[2] = {0};
    uint8_t sensors[] = { BMI2_ACCEL, BMI2_GYRO };

    bmi270_ready = false;
    memset(&bmi270_device, 0, sizeof(bmi270_device));
    bmi270_device.intf = BMI2_SPI_INTF;
    bmi270_device.read = spi_read;
    bmi270_device.write = spi_write;
    bmi270_device.delay_us = delay_us;
    bmi270_device.read_write_len = 32U;
    bmi270_device.config_file_ptr = NULL;

    if (bmi270_init(&bmi270_device) != BMI2_OK) {
        return false;
    }
    configuration[0].type = BMI2_ACCEL;
    configuration[0].cfg.acc.odr = BMI2_ACC_ODR_100HZ;
    configuration[0].cfg.acc.range = BMI2_ACC_RANGE_2G;
    configuration[0].cfg.acc.bwp = BMI2_ACC_NORMAL_AVG4;
    configuration[0].cfg.acc.filter_perf = BMI2_PERF_OPT_MODE;
    configuration[1].type = BMI2_GYRO;
    configuration[1].cfg.gyr.odr = BMI2_GYR_ODR_100HZ;
    configuration[1].cfg.gyr.range = BMI2_GYR_RANGE_2000;
    configuration[1].cfg.gyr.bwp = BMI2_GYR_NORMAL_MODE;
    configuration[1].cfg.gyr.noise_perf = BMI2_POWER_OPT_MODE;
    configuration[1].cfg.gyr.filter_perf = BMI2_PERF_OPT_MODE;
    if (bmi2_set_sensor_config(configuration, 2U, &bmi270_device) != BMI2_OK ||
        bmi2_sensor_enable(sensors, 2U, &bmi270_device) != BMI2_OK) {
        return false;
    }
    bmi270_ready = true;
    return true;
}

bool bmi270_driver_read_sample(bmi270_sample_t *sample)
{
    struct bmi2_sens_data data = {0};
    if (!bmi270_ready || sample == NULL ||
        bmi2_get_sensor_data(&data, &bmi270_device) != BMI2_OK) {
        return false;
    }
    sample->acceleration_x = data.acc.x;
    sample->acceleration_y = data.acc.y;
    sample->acceleration_z = data.acc.z;
    sample->gyroscope_x = data.gyr.x;
    sample->gyroscope_y = data.gyr.y;
    sample->gyroscope_z = data.gyr.z;
    return true;
}

void bmi270_driver_shutdown(void)
{
    bmi270_ready = false;
}
