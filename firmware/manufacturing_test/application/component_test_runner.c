#include "component_test_runner.h"

void component_test_runner_initialize(component_test_runner_t *runner)
{
    runner->active_definition = NULL;
    runner->active_command_id = 0U;
}

bool component_test_runner_start(
    component_test_runner_t *runner,
    const component_test_definition_t *definition,
    uint32_t command_id,
    const component_test_parameters_t *parameters
)
{
    if (runner->active_definition != NULL || definition == NULL || command_id == 0U) {
        return false;
    }
    runner->active_definition = definition;
    runner->active_command_id = command_id;
    definition->start(parameters);
    return true;
}

component_test_runner_update_t component_test_runner_process(
    component_test_runner_t *runner
)
{
    const component_test_process_result_t result =
        runner->active_definition == NULL ? COMPONENT_TEST_PROCESS_RUNNING :
        runner->active_definition->process();

    if (runner->active_definition == NULL || result == COMPONENT_TEST_PROCESS_RUNNING) {
        return COMPONENT_TEST_RUNNER_UPDATE_NONE;
    }
    if (result == COMPONENT_TEST_PROCESS_EVENT) {
        return COMPONENT_TEST_RUNNER_UPDATE_EVENT;
    }
    runner->active_definition->stop();
    runner->active_definition = NULL;
    runner->active_command_id = 0U;
    return result == COMPONENT_TEST_PROCESS_PASSED ?
        COMPONENT_TEST_RUNNER_UPDATE_PASSED : COMPONENT_TEST_RUNNER_UPDATE_FAILED;
}

bool component_test_runner_stop(component_test_runner_t *runner)
{
    const component_test_definition_t *definition = runner->active_definition;

    if (definition == NULL) {
        return false;
    }
    runner->active_definition = NULL;
    runner->active_command_id = 0U;
    definition->stop();
    return true;
}

component_test_runner_state_t component_test_runner_state(
    const component_test_runner_t *runner
)
{
    return runner->active_definition == NULL ? COMPONENT_TEST_RUNNER_IDLE :
        COMPONENT_TEST_RUNNER_RUNNING;
}

const char *component_test_runner_active_type(const component_test_runner_t *runner)
{
    return runner->active_definition == NULL ? NULL : runner->active_definition->type;
}

uint32_t component_test_runner_active_command_id(
    const component_test_runner_t *runner
)
{
    return runner->active_command_id;
}

const char *component_test_runner_event(const component_test_runner_t *runner)
{
    return runner->active_definition == NULL || runner->active_definition->event == NULL ?
        NULL : runner->active_definition->event();
}
