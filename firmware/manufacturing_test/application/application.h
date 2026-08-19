#ifndef OPENFLIGHTCOMPUTER_APPLICATION_H
#define OPENFLIGHTCOMPUTER_APPLICATION_H

#include <stdint.h>

typedef enum {
    APPLICATION_STATE_BOOTING = 0,
    APPLICATION_STATE_READY = 1,
    APPLICATION_STATE_CLOCK_ERROR = 2,
    APPLICATION_STATE_USB_ERROR = 3,
} application_state_t;

extern volatile application_state_t application_state;
extern volatile uint32_t application_loop_iterations;

void application_run(void) __attribute__((noreturn));
void application_stop(application_state_t failure_state) __attribute__((noreturn));

#endif
