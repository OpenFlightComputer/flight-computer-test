#include "component_registry.h"
#include "ws2812_encoder.h"

#include <stdbool.h>
#include <stddef.h>

#include "stm32f4xx_hal.h"

/*
 * Drive the single onboard WS2812 directly from the CPU.
 *
 * The Cortex-M4 DWT cycle counter provides the sub-microsecond waits, while
 * direct writes to GPIOA's BSRR register change PA1 without HAL call overhead.
 *
 * At the configured 168 MHz CPU clock, one cycle is about 5.95 ns:
 *
 *   logical 0:  48 cycles high ~= 286 ns, 150 cycles low ~= 893 ns
 *   logical 1: 105 cycles high ~= 625 ns, 105 cycles low ~= 625 ns
 *
 * GPIO writes and barriers add a few cycles. The selected values leave margin
 * within the WS2812B V5 timing windows: T0H=220..380 ns, T1H=580..1000 ns,
 * and both low intervals=580..1000 ns. Interrupts are masked only while the
 * 24 data bits are sent, approximately 30 us, then immediately restored.
 */
#define EXPECTED_CORE_CLOCK_HZ 168000000U
#define WS2812_RESET_MS 1U
#define WS2812_ZERO_HIGH_CYCLES 48U
#define WS2812_ZERO_LOW_CYCLES 150U
#define WS2812_ONE_HIGH_CYCLES 105U
#define WS2812_ONE_LOW_CYCLES 105U

typedef enum {
    RGB_TEST_COLOUR_READY,
    RGB_TEST_ACTIVE,
    RGB_TEST_FAILED,
} rgb_test_state_t;

static uint8_t frame[WS2812_FRAME_BYTES];
static bool hardware_ready;
static bool transmission_failed;
static rgb_test_state_t state;
static component_test_event_t latest_event;

__STATIC_FORCEINLINE void wait_cycles(uint32_t cycles)
{
    const uint32_t started_at = DWT->CYCCNT;

    while ((uint32_t)(DWT->CYCCNT - started_at) < cycles) {
        __NOP();
    }
}

__STATIC_FORCEINLINE void drive_din_high(void)
{
    GPIOA->BSRR = GPIO_PIN_1;
    __DSB();
}

__STATIC_FORCEINLINE void drive_din_low(void)
{
    GPIOA->BSRR = (uint32_t)GPIO_PIN_1 << 16U;
    __DSB();
}

static bool initialize_hardware(void)
{
    GPIO_InitTypeDef pin = {0};

    if (SystemCoreClock != EXPECTED_CORE_CLOCK_HZ) {
        return false;
    }

    __HAL_RCC_GPIOA_CLK_ENABLE();
    drive_din_low();

    pin.Pin = GPIO_PIN_1;
    pin.Mode = GPIO_MODE_OUTPUT_PP;
    pin.Pull = GPIO_NOPULL;
    pin.Speed = GPIO_SPEED_FREQ_VERY_HIGH;
    HAL_GPIO_Init(GPIOA, &pin);

    /* Enable and reset the Cortex-M4's free-running CPU cycle counter. */
    CoreDebug->DEMCR |= CoreDebug_DEMCR_TRCENA_Msk;
    DWT->CYCCNT = 0U;
    DWT->CTRL |= DWT_CTRL_CYCCNTENA_Msk;
    if ((DWT->CTRL & DWT_CTRL_CYCCNTENA_Msk) == 0U) {
        return false;
    }

    /* A known low interval resets the LED before its first 24-bit frame. */
    HAL_Delay(WS2812_RESET_MS);
    return true;
}

static bool transmit(uint8_t red, uint8_t green, uint8_t blue)
{
    if (!hardware_ready) {
        return false;
    }

    ws2812_encode(red, green, blue, frame);
    drive_din_low();
    HAL_Delay(WS2812_RESET_MS);

    /*
     * Preserve the prior interrupt state instead of unconditionally enabling
     * interrupts afterward. A delayed USB/SysTick interrupt cannot split a
     * WS2812 pulse while PRIMASK is set.
     */
    const uint32_t previous_primask = __get_PRIMASK();
    __disable_irq();

    for (size_t index = 0U; index < WS2812_DATA_BITS; index++) {
        const uint8_t mask = (uint8_t)(0x80U >> (index % 8U));
        const bool one = (frame[index / 8U] & mask) != 0U;

        drive_din_high();
        wait_cycles(
            one ? WS2812_ONE_HIGH_CYCLES : WS2812_ZERO_HIGH_CYCLES
        );
        drive_din_low();
        wait_cycles(
            one ? WS2812_ONE_LOW_CYCLES : WS2812_ZERO_LOW_CYCLES
        );
    }

    __set_PRIMASK(previous_primask);

    /* Keep DIN low long enough for the LED to latch the received colour. */
    HAL_Delay(WS2812_RESET_MS);
    return true;
}

static void message(const char *name)
{
    latest_event = (component_test_event_t){
        .kind = COMPONENT_TEST_EVENT_MESSAGE,
        .name = name,
    };
}

void rgb_led_test_start(const component_test_parameters_t *parameters)
{
    hardware_ready = false;
    transmission_failed = parameters == NULL ||
        !parameters->rgb_colour_present;
    if (transmission_failed) {
        state = RGB_TEST_FAILED;
        return;
    }

    hardware_ready = initialize_hardware();
    transmission_failed = !hardware_ready || !transmit(
        parameters->red,
        parameters->green,
        parameters->blue
    );
    state = transmission_failed ? RGB_TEST_FAILED : RGB_TEST_COLOUR_READY;
}

component_test_process_result_t rgb_led_test_process(void)
{
    if (transmission_failed || state == RGB_TEST_FAILED) {
        return COMPONENT_TEST_PROCESS_FAILED;
    }

    if (state == RGB_TEST_COLOUR_READY) {
        message("rgb_colour_active");
        state = RGB_TEST_ACTIVE;
        return COMPONENT_TEST_PROCESS_EVENT;
    }

    return COMPONENT_TEST_PROCESS_RUNNING;
}

const component_test_event_t *rgb_led_test_event(void)
{
    return &latest_event;
}

void rgb_led_test_stop(void)
{
    if (!hardware_ready) {
        return;
    }

    (void)transmit(0U, 0U, 0U);
}
