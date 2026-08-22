#include "imu_spi.h"

#include "stm32f4xx_hal.h"

static SPI_HandleTypeDef imu_spi;
static bool imu_spi_ready;

static bool initialize_imu_spi(void)
{
    GPIO_InitTypeDef gpio = {0};

    if (imu_spi_ready) {
        return true;
    }
    __HAL_RCC_GPIOB_CLK_ENABLE();
    __HAL_RCC_GPIOD_CLK_ENABLE();
    __HAL_RCC_SPI3_CLK_ENABLE();

    /* PB3/PB4/PB5 are the board's resolved SPI3 AF6 IMU route. */
    gpio.Pin = GPIO_PIN_3 | GPIO_PIN_4 | GPIO_PIN_5;
    gpio.Mode = GPIO_MODE_AF_PP;
    gpio.Pull = GPIO_NOPULL;
    gpio.Speed = GPIO_SPEED_FREQ_VERY_HIGH;
    gpio.Alternate = GPIO_AF6_SPI3;
    HAL_GPIO_Init(GPIOB, &gpio);

    /* The BMI270 is selected only for the duration of each SPI transfer. */
    gpio.Pin = GPIO_PIN_2;
    gpio.Mode = GPIO_MODE_OUTPUT_PP;
    gpio.Pull = GPIO_NOPULL;
    gpio.Speed = GPIO_SPEED_FREQ_VERY_HIGH;
    HAL_GPIO_Init(GPIOD, &gpio);
    HAL_GPIO_WritePin(GPIOD, GPIO_PIN_2, GPIO_PIN_SET);

    imu_spi.Instance = SPI3;
    imu_spi.Init.Mode = SPI_MODE_MASTER;
    imu_spi.Init.Direction = SPI_DIRECTION_2LINES;
    imu_spi.Init.DataSize = SPI_DATASIZE_8BIT;
    imu_spi.Init.CLKPolarity = SPI_POLARITY_LOW;
    imu_spi.Init.CLKPhase = SPI_PHASE_1EDGE;
    imu_spi.Init.NSS = SPI_NSS_SOFT;
    /* APB1 is 42 MHz. 42 MHz / 64 = 656.25 kHz, a cautious bring-up rate. */
    imu_spi.Init.BaudRatePrescaler = SPI_BAUDRATEPRESCALER_64;
    imu_spi.Init.FirstBit = SPI_FIRSTBIT_MSB;
    imu_spi.Init.TIMode = SPI_TIMODE_DISABLE;
    imu_spi.Init.CRCCalculation = SPI_CRCCALCULATION_DISABLE;
    imu_spi.Init.CRCPolynomial = 7U;
    if (HAL_SPI_Init(&imu_spi) != HAL_OK) {
        return false;
    }
    imu_spi_ready = true;
    return true;
}

bool flightcomputer_v1_imu_spi_transfer(
    const uint8_t *transmit,
    uint8_t *receive,
    size_t length
)
{
    if (transmit == NULL || receive == NULL || length == 0U || length > UINT16_MAX ||
        !initialize_imu_spi()) {
        return false;
    }
    HAL_GPIO_WritePin(GPIOD, GPIO_PIN_2, GPIO_PIN_RESET);
    const HAL_StatusTypeDef status = HAL_SPI_TransmitReceive(
        &imu_spi, (uint8_t *)transmit, receive, (uint16_t)length, 20U
    );
    HAL_GPIO_WritePin(GPIOD, GPIO_PIN_2, GPIO_PIN_SET);
    return status == HAL_OK;
}

void flightcomputer_v1_delay_us(uint32_t microseconds)
{
    /* DWT CYCCNT counts CPU cycles independently of the main loop/SysTick. */
    CoreDebug->DEMCR |= CoreDebug_DEMCR_TRCENA_Msk;
    DWT->CTRL |= DWT_CTRL_CYCCNTENA_Msk;
    const uint32_t start = DWT->CYCCNT;
    const uint32_t cycles = (SystemCoreClock / 1000000U) * microseconds;
    while ((uint32_t)(DWT->CYCCNT - start) < cycles) {
        __NOP();
    }
}
