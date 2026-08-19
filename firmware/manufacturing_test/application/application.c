#include "application.h"

#include "stm32f4xx.h"

volatile application_state_t application_state = APPLICATION_STATE_BOOTING;
volatile uint32_t application_loop_iterations = 0U;

void application_run(void)
{
    application_state = APPLICATION_STATE_READY;

    for (;;) {
        application_loop_iterations++;
        __NOP();
    }
}

void application_stop(application_state_t failure_state)
{
    __disable_irq();
    application_state = failure_state;

    for (;;) {
        __NOP();
    }
}
