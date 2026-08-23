#include "barometer_i2c.h"

#include "stm32f4xx_hal.h"

static I2C_HandleTypeDef barometer_i2c;
static bool barometer_i2c_ready;

static bool initialize_barometer_i2c(void)
{
    GPIO_InitTypeDef gpio = {0};

    if (barometer_i2c_ready) {
        return true;
    }
    __HAL_RCC_GPIOB_CLK_ENABLE();
    __HAL_RCC_I2C2_CLK_ENABLE();
    /* PB10/PB11 are I2C2 AF4. Open-drain lets the pull-up resistors set a '1'. */
    gpio.Pin = GPIO_PIN_10 | GPIO_PIN_11;
    gpio.Mode = GPIO_MODE_AF_OD;
    gpio.Pull = GPIO_NOPULL;
    gpio.Speed = GPIO_SPEED_FREQ_VERY_HIGH;
    gpio.Alternate = GPIO_AF4_I2C2;
    HAL_GPIO_Init(GPIOB, &gpio);

    barometer_i2c.Instance = I2C2;
    barometer_i2c.Init.ClockSpeed = 100000U;
    barometer_i2c.Init.DutyCycle = I2C_DUTYCYCLE_2;
    barometer_i2c.Init.OwnAddress1 = 0U;
    barometer_i2c.Init.AddressingMode = I2C_ADDRESSINGMODE_7BIT;
    barometer_i2c.Init.DualAddressMode = I2C_DUALADDRESS_DISABLE;
    barometer_i2c.Init.OwnAddress2 = 0U;
    barometer_i2c.Init.GeneralCallMode = I2C_GENERALCALL_DISABLE;
    barometer_i2c.Init.NoStretchMode = I2C_NOSTRETCH_DISABLE;
    if (HAL_I2C_Init(&barometer_i2c) != HAL_OK) {
        return false;
    }
    barometer_i2c_ready = true;
    return true;
}

bool flightcomputer_v1_barometer_i2c_read(
    uint8_t address, uint8_t register_address, uint8_t *data, size_t length
)
{
    return data != NULL && length > 0U && length <= UINT16_MAX &&
        initialize_barometer_i2c() && HAL_I2C_Mem_Read(
            &barometer_i2c, (uint16_t)address << 1U, register_address,
            I2C_MEMADD_SIZE_8BIT, data, (uint16_t)length, 20U
        ) == HAL_OK;
}

bool flightcomputer_v1_barometer_i2c_write(
    uint8_t address, uint8_t register_address, const uint8_t *data, size_t length
)
{
    return data != NULL && length > 0U && length <= UINT16_MAX &&
        initialize_barometer_i2c() && HAL_I2C_Mem_Write(
            &barometer_i2c, (uint16_t)address << 1U, register_address,
            I2C_MEMADD_SIZE_8BIT, (uint8_t *)data, (uint16_t)length, 20U
        ) == HAL_OK;
}
