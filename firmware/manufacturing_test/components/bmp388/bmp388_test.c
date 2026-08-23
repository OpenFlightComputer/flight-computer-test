#include "component_registry.h"

#include "bmp388/bmp388_driver.h"
#include "stm32f4xx_hal.h"

typedef enum {
    BMP388_TEST_INITIALIZING,
    BMP388_TEST_SAMPLING,
    BMP388_TEST_FAILED,
} bmp388_test_state_t;

#define BMP388_SAMPLE_INTERVAL_MS 200U

static bmp388_test_state_t state;
static uint32_t next_sample_at;
static component_test_event_t latest_event;

void bmp388_test_start(const component_test_parameters_t *parameters)
{
    (void)parameters;
    state = BMP388_TEST_INITIALIZING;
    latest_event = (component_test_event_t){ .kind = COMPONENT_TEST_EVENT_MESSAGE,
        .name = "barometer_ready" };
}

component_test_process_result_t bmp388_test_process(void)
{
    bmp388_sample_t sample;
    const uint32_t now = HAL_GetTick();

    if (state == BMP388_TEST_INITIALIZING) {
        if (!bmp388_driver_initialize()) {
            state = BMP388_TEST_FAILED;
            return COMPONENT_TEST_PROCESS_FAILED;
        }
        state = BMP388_TEST_SAMPLING;
        next_sample_at = now;
        return COMPONENT_TEST_PROCESS_EVENT;
    }
    if (state == BMP388_TEST_FAILED) {
        return COMPONENT_TEST_PROCESS_FAILED;
    }
    if ((int32_t)(now - next_sample_at) < 0) {
        return COMPONENT_TEST_PROCESS_RUNNING;
    }
    next_sample_at = now + BMP388_SAMPLE_INTERVAL_MS;
    if (!bmp388_driver_read_sample(&sample)) {
        state = BMP388_TEST_FAILED;
        return COMPONENT_TEST_PROCESS_FAILED;
    }
    latest_event = (component_test_event_t){
        .kind = COMPONENT_TEST_EVENT_BAROMETER_SAMPLE,
        .name = "barometer_sample",
        .pressure_centi_pa = sample.pressure_centi_pa,
        .temperature_centi_c = sample.temperature_centi_c,
    };
    return COMPONENT_TEST_PROCESS_EVENT;
}

const component_test_event_t *bmp388_test_event(void)
{
    return &latest_event;
}

void bmp388_test_stop(void)
{
    bmp388_driver_shutdown();
}
