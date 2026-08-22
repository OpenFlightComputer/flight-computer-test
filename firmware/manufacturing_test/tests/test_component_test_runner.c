#include "component_test_runner.h"

#include <assert.h>
#include <string.h>

static unsigned int start_count;
static unsigned int process_count;
static unsigned int stop_count;
static component_test_process_result_t next_result;

static void fake_start(const component_test_parameters_t *parameters)
{
    (void)parameters;
    start_count++;
}

static component_test_process_result_t fake_process(void)
{
    process_count++;
    return next_result;
}

static void fake_stop(void)
{
    stop_count++;
}

static const char *fake_event(void)
{
    return "operator_confirmation_required";
}

static const component_test_definition_t fake_definition = {
    .type = "fake_test",
    .start = fake_start,
    .process = fake_process,
    .event = fake_event,
    .stop = fake_stop,
};

static void reset_fake(void)
{
    start_count = 0U;
    process_count = 0U;
    stop_count = 0U;
    next_result = COMPONENT_TEST_PROCESS_RUNNING;
}

static void test_runner_keeps_one_test_active_until_completion(void)
{
    component_test_runner_t runner;

    reset_fake();
    component_test_runner_initialize(&runner);
    assert(component_test_runner_start(&runner, &fake_definition, 7U, NULL));
    assert(start_count == 1U);
    assert(!component_test_runner_start(&runner, &fake_definition, 8U, NULL));
    assert(component_test_runner_process(&runner) == COMPONENT_TEST_RUNNER_UPDATE_NONE);
    assert(process_count == 1U);
    assert(stop_count == 0U);

    next_result = COMPONENT_TEST_PROCESS_EVENT;
    assert(component_test_runner_process(&runner) == COMPONENT_TEST_RUNNER_UPDATE_EVENT);
    assert(process_count == 2U);
    assert(strcmp(component_test_runner_event(&runner),
        "operator_confirmation_required") == 0);

    next_result = COMPONENT_TEST_PROCESS_PASSED;
    assert(component_test_runner_process(&runner) == COMPONENT_TEST_RUNNER_UPDATE_PASSED);
    assert(stop_count == 1U);
    assert(component_test_runner_state(&runner) == COMPONENT_TEST_RUNNER_IDLE);
}

static void test_stop_clears_active_test_before_cleanup(void)
{
    component_test_runner_t runner;

    reset_fake();
    component_test_runner_initialize(&runner);
    assert(component_test_runner_start(&runner, &fake_definition, 7U, NULL));
    assert(component_test_runner_stop(&runner));
    assert(component_test_runner_state(&runner) == COMPONENT_TEST_RUNNER_IDLE);
    assert(stop_count == 1U);
    assert(!component_test_runner_stop(&runner));
}

int main(void)
{
    test_runner_keeps_one_test_active_until_completion();
    test_stop_clears_active_test_before_cleanup();
    return 0;
}
