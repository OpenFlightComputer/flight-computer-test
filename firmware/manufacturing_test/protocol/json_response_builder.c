#include "json_protocol.h"

#include <stdarg.h>
#include <stdio.h>

static bool append_format(
    char *destination, size_t capacity, size_t *offset, const char *format, ...
)
{
    va_list arguments;
    int written;

    if (*offset >= capacity) {
        return false;
    }
    va_start(arguments, format);
    written = vsnprintf(&destination[*offset], capacity - *offset, format, arguments);
    va_end(arguments);
    if (written < 0 || (size_t)written >= capacity - *offset) {
        return false;
    }
    *offset += (size_t)written;
    return true;
}

bool json_protocol_build_start_test_response(
    uint32_t command_id, const session_metadata_t *metadata, char *destination,
    size_t capacity, size_t *length
)
{
    size_t offset = 0U;

    if (!append_format(destination, capacity, &offset,
        "{\"protocol_version\":1,\"type\":\"START_TEST_RESPONSE\","
        "\"command_id\":%lu,\"status\":\"ok\",\"device\":{"
        "\"uid\":\"%s\",\"mcu\":\"%s\",\"board_id\":\"%s\","
        "\"board_name\":\"%s\",\"board_revision\":\"%s\"},"
        "\"firmware\":{\"version\":\"%s\",\"git_revision\":\"%s\"},"
        "\"capabilities\":[", (unsigned long)command_id, metadata->uid,
        metadata->mcu_model, metadata->board_id, metadata->board_name,
        metadata->board_revision, metadata->firmware_version,
        metadata->firmware_git_revision)) {
        return false;
    }
    for (size_t index = 0U; index < metadata->capability_count; index++) {
        if (!append_format(destination, capacity, &offset, "%s\"%s\"",
            index == 0U ? "" : ",", metadata->capability_at(index))) {
            return false;
        }
    }
    if (!append_format(destination, capacity, &offset, "]}")) {
        return false;
    }
    *length = offset;
    return true;
}

bool json_protocol_build_error_response(
    uint32_t command_id, const char *error_code, char *destination, size_t capacity,
    size_t *length
)
{
    const int written = snprintf(destination, capacity,
        "{\"protocol_version\":1,\"type\":\"ERROR\",\"command_id\":%lu,"
        "\"error\":\"%s\"}", (unsigned long)command_id, error_code);
    if (written < 0 || (size_t)written >= capacity) {
        return false;
    }
    *length = (size_t)written;
    return true;
}

bool json_protocol_build_test_response(
    const char *response_type, uint32_t command_id, const char *test_type,
    const char *status, char *destination, size_t capacity, size_t *length
)
{
    const int written = snprintf(destination, capacity,
        "{\"protocol_version\":1,\"type\":\"%s\",\"command_id\":%lu,"
        "\"test_type\":\"%s\",\"status\":\"%s\"}", response_type,
        (unsigned long)command_id, test_type, status);
    if (written < 0 || (size_t)written >= capacity) {
        return false;
    }
    *length = (size_t)written;
    return true;
}
