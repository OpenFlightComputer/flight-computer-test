#include "component_registry.h"
#include "ws2812_encoder.h"

#include <stdbool.h>

#include "stm32f4xx_hal.h"

/*
 * Clock derivation for TIM2:
 *   16 MHz HSE -> PLL -> 168 MHz SYSCLK/HCLK.
 *   APB1 is HCLK/4 = 42 MHz. STM32F4 timers receive twice the APB clock
 *   whenever the APB prescaler is greater than one, so TIM2 runs at 84 MHz.
 *   84 MHz / 800 kHz = 105 timer ticks per 1.25 us WS2812 bit.
 *
 * The V5 LED datasheet permits T0H=220..380 ns and T1H=580..1000 ns.
 * At 84 MHz, 29 ticks = 345 ns and 59 ticks = 702 ns. Both are comfortably
 * inside those ranges. The 256 trailing zero-duty periods hold PA1 low for
 * 256 * 1.25 us = 320 us. This exceeds the required reset time >280 us with
 * some margin instead of relying on exactly the datasheet minimum.
 */
#define WS2812_TIMER_PERIOD_TICKS 105U

static TIM_HandleTypeDef timer;
static DMA_HandleTypeDef dma;
static uint16_t frame[WS2812_FRAME_VALUES];
static volatile bool transfer_complete;
static volatile bool transmission_failed;

static bool initialize_hardware(void)
{
    GPIO_InitTypeDef pin = {0};
    TIM_OC_InitTypeDef pwm = {0};

    __HAL_RCC_GPIOA_CLK_ENABLE();
    __HAL_RCC_TIM2_CLK_ENABLE();
    __HAL_RCC_DMA1_CLK_ENABLE();

    /* PA1 AF1 connects the physical WS2812 DIN net to TIM2 channel 2. */
    pin.Pin = GPIO_PIN_1;
    pin.Mode = GPIO_MODE_AF_PP;
    pin.Pull = GPIO_NOPULL;
    pin.Speed = GPIO_SPEED_FREQ_VERY_HIGH;
    pin.Alternate = GPIO_AF1_TIM2;
    HAL_GPIO_Init(GPIOA, &pin);

    timer.Instance = TIM2;
    timer.Init.Prescaler = 0U;
    timer.Init.CounterMode = TIM_COUNTERMODE_UP;
    timer.Init.Period = WS2812_TIMER_PERIOD_TICKS - 1U;
    timer.Init.ClockDivision = TIM_CLOCKDIVISION_DIV1;
    timer.Init.AutoReloadPreload = TIM_AUTORELOAD_PRELOAD_DISABLE;
    if (HAL_TIM_PWM_Init(&timer) != HAL_OK) {
        return false;
    }

    pwm.OCMode = TIM_OCMODE_PWM1;
    pwm.Pulse = 0U;
    pwm.OCPolarity = TIM_OCPOLARITY_HIGH;
    pwm.OCFastMode = TIM_OCFAST_DISABLE;
    if (HAL_TIM_PWM_ConfigChannel(&timer, &pwm, TIM_CHANNEL_2) != HAL_OK) {
        return false;
    }

    /*
     * DMA is a hardware copy engine. On each TIM2 channel-2 request it reads
     * the next 16-bit compare value from frame[] in SRAM and writes it to the
     * TIM2 CCR2 peripheral register. RM0090's DMA1 request-mapping table maps
     * TIM2_CH2 to stream 6/channel 3. The CPU and main loop remain available.
     */
    dma.Instance = DMA1_Stream6;
    dma.Init.Channel = DMA_CHANNEL_3;
    dma.Init.Direction = DMA_MEMORY_TO_PERIPH;
    dma.Init.PeriphInc = DMA_PINC_DISABLE;
    dma.Init.MemInc = DMA_MINC_ENABLE;
    dma.Init.PeriphDataAlignment = DMA_PDATAALIGN_HALFWORD;
    dma.Init.MemDataAlignment = DMA_MDATAALIGN_HALFWORD;
    dma.Init.Mode = DMA_NORMAL;
    dma.Init.Priority = DMA_PRIORITY_HIGH;
    dma.Init.FIFOMode = DMA_FIFOMODE_DISABLE;
    if (HAL_DMA_Init(&dma) != HAL_OK) {
        return false;
    }
    __HAL_LINKDMA(&timer, hdma[TIM_DMA_ID_CC2], dma);

    HAL_NVIC_SetPriority(DMA1_Stream6_IRQn, 7U, 0U);
    HAL_NVIC_EnableIRQ(DMA1_Stream6_IRQn);
    return true;
}

static bool transmit(uint8_t red, uint8_t green, uint8_t blue)
{
    (void)HAL_TIM_PWM_Stop_DMA(&timer, TIM_CHANNEL_2);
    ws2812_encode(red, green, blue, frame);
    transfer_complete = false;
    return HAL_TIM_PWM_Start_DMA(
        &timer, TIM_CHANNEL_2, (const uint32_t *)frame, WS2812_FRAME_VALUES
    ) == HAL_OK;
}

void rgb_led_test_start(const component_test_parameters_t *parameters)
{
    transmission_failed = !initialize_hardware();
    if (!transmission_failed && parameters != NULL &&
        parameters->rgb_colour_present) {
        transmission_failed = !transmit(
            parameters->red,
            parameters->green,
            parameters->blue
        );
    } else {
        transmission_failed = true;
    }
}

component_test_process_result_t rgb_led_test_process(void)
{
    if (transmission_failed) {
        return COMPONENT_TEST_PROCESS_FAILED;
    }

    /* DMA completion leaves the color latched; only the operator ends it. */
    return COMPONENT_TEST_PROCESS_RUNNING;
}

void rgb_led_test_stop(void)
{
    if (transmission_failed || !transmit(0U, 0U, 0U)) {
        return;
    }

    /*
     * Stopping is the one bounded wait in this driver. The zero frame lasts
     * about 350 us and must reach the LED before another test can reuse PA1.
     * Interrupts remain enabled while the main loop waits, so USB still works.
     */
    const uint32_t started_at = HAL_GetTick();
    while (!transfer_complete && (HAL_GetTick() - started_at) < 2U) {
    }
    (void)HAL_TIM_PWM_Stop_DMA(&timer, TIM_CHANNEL_2);
}

void rgb_led_dma_irq_handler(void)
{
    HAL_DMA_IRQHandler(&dma);
}

void HAL_TIM_PWM_PulseFinishedCallback(TIM_HandleTypeDef *completed_timer)
{
    if (completed_timer->Instance == TIM2) {
        /* Interrupt code only records completion; test policy stays in main. */
        transfer_complete = true;
    }
}

void HAL_TIM_ErrorCallback(TIM_HandleTypeDef *failed_timer)
{
    if (failed_timer->Instance == TIM2) {
        /* The main loop turns this interrupt fact into a failed test result. */
        transmission_failed = true;
    }
}
