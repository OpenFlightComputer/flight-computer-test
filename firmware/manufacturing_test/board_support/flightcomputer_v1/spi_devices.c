#include "spi_devices.h"

#include "stm32f4xx_hal.h"

typedef struct {
    SPI_HandleTypeDef handle;
    GPIO_TypeDef *port;
    uint16_t pins;
    uint8_t alternate;
    GPIO_TypeDef *cs_port;
    uint16_t cs_pin;
    SPI_TypeDef *instance;
    uint32_t prescaler;
    bool ready;
} flightcomputer_spi_context_t;

static flightcomputer_spi_context_t imu_context = {
    .port = GPIOB, .pins = GPIO_PIN_3 | GPIO_PIN_4 | GPIO_PIN_5,
    .alternate = GPIO_AF6_SPI3, .cs_port = GPIOD, .cs_pin = GPIO_PIN_2,
    .instance = SPI3, .prescaler = SPI_BAUDRATEPRESCALER_64,
};
static flightcomputer_spi_context_t sd_context = {
    .port = GPIOA, .pins = GPIO_PIN_5 | GPIO_PIN_6 | GPIO_PIN_7,
    .alternate = GPIO_AF5_SPI1, .cs_port = GPIOC, .cs_pin = GPIO_PIN_4,
    .instance = SPI1, .prescaler = SPI_BAUDRATEPRESCALER_256,
};
static bool sd_card_detect_ready;

static void enable_peripheral_clocks(const flightcomputer_spi_context_t *context)
{
    if (context->port == GPIOA) {
        __HAL_RCC_GPIOA_CLK_ENABLE();
    }
    if (context->port == GPIOB) {
        __HAL_RCC_GPIOB_CLK_ENABLE();
    }
    if (context->cs_port == GPIOC) {
        __HAL_RCC_GPIOC_CLK_ENABLE();
    }
    if (context->cs_port == GPIOD) {
        __HAL_RCC_GPIOD_CLK_ENABLE();
    }
    if (context->instance == SPI1) {
        __HAL_RCC_SPI1_CLK_ENABLE();
    }
    if (context->instance == SPI3) {
        __HAL_RCC_SPI3_CLK_ENABLE();
    }
}

static bool initialize(spi_device_t *device)
{
    flightcomputer_spi_context_t *context = device->context;
    GPIO_InitTypeDef gpio = {0};
    if (context->ready) {
        return true;
    }
    enable_peripheral_clocks(context);
    gpio.Pin = context->pins;
    gpio.Mode = GPIO_MODE_AF_PP;
    gpio.Pull = GPIO_NOPULL;
    gpio.Speed = GPIO_SPEED_FREQ_VERY_HIGH;
    gpio.Alternate = context->alternate;
    HAL_GPIO_Init(context->port, &gpio);
    gpio.Pin = context->cs_pin;
    gpio.Mode = GPIO_MODE_OUTPUT_PP;
    gpio.Pull = GPIO_NOPULL;
    gpio.Speed = GPIO_SPEED_FREQ_VERY_HIGH;
    HAL_GPIO_Init(context->cs_port, &gpio);
    HAL_GPIO_WritePin(context->cs_port, context->cs_pin, GPIO_PIN_SET);
    context->handle.Instance = context->instance;
    context->handle.Init.Mode = SPI_MODE_MASTER;
    context->handle.Init.Direction = SPI_DIRECTION_2LINES;
    context->handle.Init.DataSize = SPI_DATASIZE_8BIT;
    context->handle.Init.CLKPolarity = SPI_POLARITY_LOW;
    context->handle.Init.CLKPhase = SPI_PHASE_1EDGE;
    context->handle.Init.NSS = SPI_NSS_SOFT;
    context->handle.Init.BaudRatePrescaler = context->prescaler;
    context->handle.Init.FirstBit = SPI_FIRSTBIT_MSB;
    context->handle.Init.TIMode = SPI_TIMODE_DISABLE;
    context->handle.Init.CRCCalculation = SPI_CRCCALCULATION_DISABLE;
    context->handle.Init.CRCPolynomial = 7U;
    context->ready = HAL_SPI_Init(&context->handle) == HAL_OK;
    return context->ready;
}

static bool select_device(spi_device_t *device)
{
    flightcomputer_spi_context_t *context = device->context;
    if (!initialize(device)) { return false; }
    HAL_GPIO_WritePin(context->cs_port, context->cs_pin, GPIO_PIN_RESET);
    return true;
}
static void deselect_device(spi_device_t *device)
{
    flightcomputer_spi_context_t *context = device->context;
    HAL_GPIO_WritePin(context->cs_port, context->cs_pin, GPIO_PIN_SET);
}

static bool transfer(spi_device_t *device, const uint8_t *tx, uint8_t *rx, size_t length)
{
    flightcomputer_spi_context_t *context = device->context;
    return tx != NULL && rx != NULL && length > 0U && length <= UINT16_MAX &&
        initialize(device) && HAL_SPI_TransmitReceive(
            &context->handle, (uint8_t *)tx, rx, (uint16_t)length, 20U
        ) == HAL_OK;
}
static bool set_prescaler(spi_device_t *device, uint32_t prescaler)
{
    flightcomputer_spi_context_t *context = device->context;
    if (!context->ready) {
        context->prescaler = prescaler;
        return true;
    }
    if (HAL_SPI_DeInit(&context->handle) != HAL_OK) {
        return false;
    }
    context->ready = false;
    context->prescaler = prescaler;
    return initialize(device);
}
static const spi_device_operations_t operations = {
    initialize, select_device, deselect_device, transfer, set_prescaler
};
static spi_device_t imu_device = { &operations, &imu_context };
static spi_device_t sd_device = { &operations, &sd_context };

spi_device_t *flightcomputer_v1_imu_spi_device(void) { return &imu_device; }
spi_device_t *flightcomputer_v1_sd_spi_device(void) { return &sd_device; }
bool flightcomputer_v1_sd_card_inserted(void)
{
    if (!sd_card_detect_ready) {
        GPIO_InitTypeDef gpio = {0};

        __HAL_RCC_GPIOC_CLK_ENABLE();
        gpio.Pin = GPIO_PIN_5;
        gpio.Mode = GPIO_MODE_INPUT;
        gpio.Pull = GPIO_NOPULL;
        HAL_GPIO_Init(GPIOC, &gpio);
        sd_card_detect_ready = true;
    }
    return HAL_GPIO_ReadPin(GPIOC, GPIO_PIN_5) == GPIO_PIN_RESET;
}

void flightcomputer_v1_delay_us(uint32_t microseconds)
{
    CoreDebug->DEMCR |= CoreDebug_DEMCR_TRCENA_Msk;
    DWT->CTRL |= DWT_CTRL_CYCCNTENA_Msk;
    const uint32_t start = DWT->CYCCNT;
    const uint32_t cycles = (SystemCoreClock / 1000000U) * microseconds;
    while ((uint32_t)(DWT->CYCCNT - start) < cycles) { __NOP(); }
}
