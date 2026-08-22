#ifndef OPENFLIGHTCOMPUTER_COMPONENT_TEST_RUNNER_H
#define OPENFLIGHTCOMPUTER_COMPONENT_TEST_RUNNER_H

#include "component_registry.h"

#include <stdbool.h>
#include <stdint.h>

typedef enum {
    COMPONENT_TEST_RUNNER_IDLE = 0,
    COMPONENT_TEST_RUNNER_RUNNING = 1,
} component_test_runner_state_t;

typedef enum {
    COMPONENT_TEST_RUNNER_UPDATE_NONE = 0,
    COMPONENT_TEST_RUNNER_UPDATE_EVENT = 1,
    COMPONENT_TEST_RUNNER_UPDATE_PASSED = 2,
    COMPONENT_TEST_RUNNER_UPDATE_FAILED = 3,
} component_test_runner_update_t;

typedef struct {
    const component_test_definition_t *active_definition;
    uint32_t active_command_id;
} component_test_runner_t;

void component_test_runner_initialize(component_test_runner_t *runner);
bool component_test_runner_start(
    component_test_runner_t *runner,
    const component_test_definition_t *definition,
    uint32_t command_id,
    const component_test_parameters_t *parameters
);
component_test_runner_update_t component_test_runner_process(
    component_test_runner_t *runner
);
bool component_test_runner_stop(component_test_runner_t *runner);
component_test_runner_state_t component_test_runner_state(
    const component_test_runner_t *runner
);
const char *component_test_runner_active_type(const component_test_runner_t *runner);
uint32_t component_test_runner_active_command_id(
    const component_test_runner_t *runner
);
const component_test_event_t *component_test_runner_event(
    const component_test_runner_t *runner
);

#endif
