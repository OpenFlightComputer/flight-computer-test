#include "component_registry.h"

#include "stm32f4xx_hal.h"

static void leds_off(void)
{
    HAL_GPIO_WritePin(GPIOB, GPIO_PIN_13 | GPIO_PIN_14, GPIO_PIN_SET);
}

static void initialize_pins(void)
{
    GPIO_InitTypeDef configuration = {0};

    __HAL_RCC_GPIOB_CLK_ENABLE();
    configuration.Pin = GPIO_PIN_13 | GPIO_PIN_14;
    configuration.Mode = GPIO_MODE_OUTPUT_PP;
    configuration.Pull = GPIO_NOPULL;
    configuration.Speed = GPIO_SPEED_FREQ_LOW;
    HAL_GPIO_Init(GPIOB, &configuration);
    leds_off();
}

void status_led_red_start(const component_test_parameters_t *parameters)
{
    (void)parameters;
    initialize_pins();
    HAL_GPIO_WritePin(GPIOB, GPIO_PIN_13, GPIO_PIN_RESET);
}

void status_led_green_start(const component_test_parameters_t *parameters)
{
    (void)parameters;
    initialize_pins();
    HAL_GPIO_WritePin(GPIOB, GPIO_PIN_14, GPIO_PIN_RESET);
}

component_test_process_result_t status_led_process(void)
{
    return COMPONENT_TEST_PROCESS_RUNNING;
}

void status_led_stop(void) { leds_off(); }
