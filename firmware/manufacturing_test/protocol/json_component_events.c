#include "json_protocol.h"

#include <stdio.h>

static int build_imu_event(
    uint32_t command_id, const char *test_type, const component_test_event_t *event,
    char *destination, size_t capacity
)
{
    return snprintf(destination, capacity,
        "{\"protocol_version\":1,\"type\":\"TEST_EVENT\",\"command_id\":%lu,"
        "\"test_type\":\"%s\",\"event\":\"%s\",\"data\":{"
        "\"acceleration_raw\":{\"x\":%d,\"y\":%d,\"z\":%d},"
        "\"gyroscope_raw\":{\"x\":%d,\"y\":%d,\"z\":%d}}}",
        (unsigned long)command_id, test_type, event->name,
        event->acceleration_x, event->acceleration_y, event->acceleration_z,
        event->gyroscope_x, event->gyroscope_y, event->gyroscope_z);
}

static int build_barometer_event(
    uint32_t command_id, const char *test_type, const component_test_event_t *event,
    char *destination, size_t capacity
)
{
    return snprintf(destination, capacity,
        "{\"protocol_version\":1,\"type\":\"TEST_EVENT\",\"command_id\":%lu,"
        "\"test_type\":\"%s\",\"event\":\"%s\",\"data\":{"
        "\"pressure_centi_pa\":%ld,\"temperature_centi_c\":%ld}}",
        (unsigned long)command_id, test_type, event->name,
        (long)event->pressure_centi_pa, (long)event->temperature_centi_c);
}

bool json_protocol_build_test_event(
    uint32_t command_id, const char *test_type, const component_test_event_t *event,
    char *destination, size_t capacity, size_t *length
)
{
    int written;

    if (test_type == NULL || event == NULL || event->name == NULL) {
        return false;
    }
    if (event->kind == COMPONENT_TEST_EVENT_IMU_SAMPLE) {
        written = build_imu_event(command_id, test_type, event, destination, capacity);
    } else if (event->kind == COMPONENT_TEST_EVENT_BAROMETER_SAMPLE) {
        written = build_barometer_event(command_id, test_type, event, destination, capacity);
    } else {
        written = snprintf(destination, capacity,
            "{\"protocol_version\":1,\"type\":\"TEST_EVENT\","
            "\"command_id\":%lu,\"test_type\":\"%s\",\"event\":\"%s\"}",
            (unsigned long)command_id, test_type, event->name);
    }
    if (written < 0 || (size_t)written >= capacity) {
        return false;
    }
    *length = (size_t)written;
    return true;
}
