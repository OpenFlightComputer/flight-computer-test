#include "json_protocol.h"

#include <stdio.h>

#define UINT64_DECIMAL_CAPACITY 21U

static void format_uint64(uint64_t value, char destination[UINT64_DECIMAL_CAPACITY])
{
    char reversed[UINT64_DECIMAL_CAPACITY - 1U];
    size_t digits = 0U;

    do {
        reversed[digits++] = (char)('0' + value % 10U);
        value /= 10U;
    } while (value > 0U);

    for (size_t index = 0U; index < digits; index++) {
        destination[index] = reversed[digits - index - 1U];
    }
    destination[digits] = '\0';
}

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

static int build_sd_card_event(
    uint32_t command_id, const char *test_type, const component_test_event_t *event,
    char *destination, size_t capacity
)
{
    char sector_count[UINT64_DECIMAL_CAPACITY];

    /* newlib-nano does not reliably provide long-long printf conversion. */
    format_uint64(event->sector_count, sector_count);
    return snprintf(destination, capacity,
        "{\"protocol_version\":1,\"type\":\"TEST_EVENT\",\"command_id\":%lu,"
        "\"test_type\":\"%s\",\"event\":\"%s\",\"data\":{"
        "\"card_type\":\"%s\",\"sector_count\":%s,\"test_sector\":%lu,"
        "\"checksum\":%lu}}",
        (unsigned long)command_id, test_type, event->name,
        event->high_capacity ? "SDHC/SDXC" : "SDSC",
        sector_count, (unsigned long)event->test_sector,
        (unsigned long)event->checksum);
}

static int build_failure_event(
    uint32_t command_id, const char *test_type, const component_test_event_t *event,
    char *destination, size_t capacity
)
{
    return snprintf(destination, capacity,
        "{\"protocol_version\":1,\"type\":\"TEST_EVENT\",\"command_id\":%lu,"
        "\"test_type\":\"%s\",\"event\":\"%s\",\"data\":{"
        "\"stage\":\"%s\",\"reason\":\"%s\",\"code\":%ld}}",
        (unsigned long)command_id, test_type, event->name,
        event->failure_stage, event->failure_reason, (long)event->failure_code);
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
    } else if (event->kind == COMPONENT_TEST_EVENT_SD_CARD_INFO) {
        written = build_sd_card_event(command_id, test_type, event, destination, capacity);
    } else if (event->kind == COMPONENT_TEST_EVENT_FAILURE) {
        if (event->failure_stage == NULL || event->failure_reason == NULL) {
            return false;
        }
        written = build_failure_event(
            command_id, test_type, event, destination, capacity
        );
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
