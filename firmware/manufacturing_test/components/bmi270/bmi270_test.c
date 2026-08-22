#include "component_registry.h"

#include "bmi270/bmi270_driver.h"
#include "stm32f4xx_hal.h"

typedef enum {
    BMI270_TEST_INITIALIZING,
    BMI270_TEST_SAMPLING,
    BMI270_TEST_FAILED,
} bmi270_test_state_t;

#define BMI270_SAMPLE_INTERVAL_MS 100U

static bmi270_test_state_t state;
static uint32_t next_sample_at;
static component_test_event_t latest_event;

void bmi270_test_start(const component_test_parameters_t *parameters)
{
    (void)parameters;
    state = BMI270_TEST_INITIALIZING;
    latest_event = (component_test_event_t){ .kind = COMPONENT_TEST_EVENT_MESSAGE,
        .name = "imu_ready" };
}

component_test_process_result_t bmi270_test_process(void)
{
    bmi270_sample_t sample;
    const uint32_t now = HAL_GetTick();

    /* Bosch configuration upload occurs once, when the main loop first services us. */
    if (state == BMI270_TEST_INITIALIZING) {
        if (!bmi270_driver_initialize()) {
            state = BMI270_TEST_FAILED;
            return COMPONENT_TEST_PROCESS_FAILED;
        }
        state = BMI270_TEST_SAMPLING;
        next_sample_at = now;
        return COMPONENT_TEST_PROCESS_EVENT;
    }
    if (state == BMI270_TEST_FAILED) {
        return COMPONENT_TEST_PROCESS_FAILED;
    }
    /* SysTick advances HAL_GetTick every millisecond: emit only every 100 ms. */
    if ((int32_t)(now - next_sample_at) < 0) {
        return COMPONENT_TEST_PROCESS_RUNNING;
    }
    next_sample_at = now + BMI270_SAMPLE_INTERVAL_MS;
    if (!bmi270_driver_read_sample(&sample)) {
        state = BMI270_TEST_FAILED;
        return COMPONENT_TEST_PROCESS_FAILED;
    }
    latest_event = (component_test_event_t){
        .kind = COMPONENT_TEST_EVENT_IMU_SAMPLE,
        .name = "imu_sample",
        .acceleration_x = sample.acceleration_x,
        .acceleration_y = sample.acceleration_y,
        .acceleration_z = sample.acceleration_z,
        .gyroscope_x = sample.gyroscope_x,
        .gyroscope_y = sample.gyroscope_y,
        .gyroscope_z = sample.gyroscope_z,
    };
    return COMPONENT_TEST_PROCESS_EVENT;
}

const component_test_event_t *bmi270_test_event(void)
{
    return &latest_event;
}

void bmi270_test_stop(void)
{
    bmi270_driver_shutdown();
}
