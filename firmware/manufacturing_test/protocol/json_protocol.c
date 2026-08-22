#include "json_protocol.h"

#define JSMN_STATIC
#include "third_party/jsmn.h"

#include <stdio.h>
#include <stdarg.h>
#include <string.h>

/*
 * The firmware remains allocation-free. 64 tokens allow nested component
 * parameter objects beyond the current RGB triplet without adding a heap.
 */
#define JSON_PROTOCOL_TOKEN_CAPACITY 64U

static bool token_equals(const char *line, const jsmntok_t *token, const char *value)
{
    const size_t value_length = strlen(value);
    const size_t token_length = (size_t)(token->end - token->start);

    return token->type == JSMN_STRING && token_length == value_length &&
        memcmp(&line[token->start], value, value_length) == 0;
}

static bool parse_positive_uint32(
    const char *line,
    const jsmntok_t *token,
    uint32_t *value
)
{
    uint64_t parsed = 0U;

    if (token->type != JSMN_PRIMITIVE || token->start == token->end) {
        return false;
    }
    for (int index = token->start; index < token->end; index++) {
        const char character = line[index];
        if (character < '0' || character > '9') {
            return false;
        }
        parsed = parsed * 10U + (uint64_t)(character - '0');
        if (parsed > UINT32_MAX) {
            return false;
        }
    }
    if (parsed == 0U) {
        return false;
    }
    *value = (uint32_t)parsed;
    return true;
}

static bool parse_uint8(
    const char *line,
    const jsmntok_t *token,
    uint8_t *value
)
{
    uint32_t parsed = 0U;

    if (token->type != JSMN_PRIMITIVE || token->start == token->end) {
        return false;
    }
    for (int index = token->start; index < token->end; index++) {
        const char character = line[index];
        if (character < '0' || character > '9') {
            return false;
        }
        parsed = parsed * 10U + (uint32_t)(character - '0');
        if (parsed > UINT8_MAX) {
            return false;
        }
    }
    *value = (uint8_t)parsed;
    return true;
}

static bool parse_rgb_parameters(
    const char *line,
    const jsmntok_t *tokens,
    int token_count,
    int *next_index,
    json_protocol_request_t *request
)
{
    const jsmntok_t *object = &tokens[*next_index - 1];
    bool red_seen = false;
    bool green_seen = false;
    bool blue_seen = false;
    int index = *next_index;

    if (object->type != JSMN_OBJECT) {
        return false;
    }
    while (index + 1 < token_count && tokens[index].start < object->end) {
        const jsmntok_t *key = &tokens[index];
        const jsmntok_t *value = &tokens[index + 1];

        if (token_equals(line, key, "red")) {
            if (red_seen || !parse_uint8(line, value, &request->red)) {
                return false;
            }
            red_seen = true;
        } else if (token_equals(line, key, "green")) {
            if (green_seen || !parse_uint8(line, value, &request->green)) {
                return false;
            }
            green_seen = true;
        } else if (token_equals(line, key, "blue")) {
            if (blue_seen || !parse_uint8(line, value, &request->blue)) {
                return false;
            }
            blue_seen = true;
        } else {
            return false;
        }
        index += 2;
    }
    if (index > token_count || !red_seen || !green_seen || !blue_seen) {
        return false;
    }
    request->rgb_colour_present = true;
    *next_index = index;
    return true;
}

static bool copy_test_uuid(
    const char *line,
    const jsmntok_t *token,
    char destination[JSON_PROTOCOL_TEST_UUID_LENGTH + 1U]
)
{
    const size_t length = (size_t)(token->end - token->start);

    if (token->type != JSMN_STRING || length != JSON_PROTOCOL_TEST_UUID_LENGTH ||
        memchr(&line[token->start], '\\', length) != NULL) {
        return false;
    }
    for (size_t index = 0U; index < length; index++) {
        const char character = line[token->start + (int)index];
        const bool hyphen = index == 8U || index == 13U || index == 18U ||
            index == 23U;
        const bool hexadecimal = (character >= '0' && character <= '9') ||
            (character >= 'a' && character <= 'f');
        if ((hyphen && character != '-') || (!hyphen && !hexadecimal)) {
            return false;
        }
    }
    if (line[token->start + 14] != '4') {
        return false;
    }
    memcpy(destination, &line[token->start], length);
    destination[length] = '\0';
    return true;
}

static bool copy_test_type(
    const char *line,
    const jsmntok_t *token,
    char destination[JSON_PROTOCOL_TEST_TYPE_CAPACITY]
)
{
    const size_t length = (size_t)(token->end - token->start);

    if (token->type != JSMN_STRING || length == 0U ||
        length >= JSON_PROTOCOL_TEST_TYPE_CAPACITY ||
        memchr(&line[token->start], '\\', length) != NULL) {
        return false;
    }
    for (size_t index = 0U; index < length; index++) {
        const char character = line[token->start + (int)index];
        if (!((character >= 'a' && character <= 'z') ||
              (character >= '0' && character <= '9') || character == '_')) {
            return false;
        }
    }
    memcpy(destination, &line[token->start], length);
    destination[length] = '\0';
    return true;
}

static bool append_format(
    char *destination,
    size_t capacity,
    size_t *offset,
    const char *format,
    ...
)
{
    va_list arguments;
    int written;

    if (*offset >= capacity) {
        return false;
    }
    va_start(arguments, format);
    written = vsnprintf(
        &destination[*offset], capacity - *offset, format, arguments
    );
    va_end(arguments);
    if (written < 0 || (size_t)written >= capacity - *offset) {
        return false;
    }
    *offset += (size_t)written;
    return true;
}

bool json_protocol_parse_request(
    const char *line,
    size_t line_length,
    json_protocol_request_t *request
)
{
    jsmn_parser parser;
    jsmntok_t tokens[JSON_PROTOCOL_TOKEN_CAPACITY];
    bool version_seen = false;
    bool type_seen = false;
    bool command_id_seen = false;
    bool test_uuid_seen = false;
    bool test_type_seen = false;
    bool parameters_seen = false;
    int token_count;

    request->type = JSON_PROTOCOL_REQUEST_INVALID;
    request->command_id = 0U;
    request->test_uuid[0] = '\0';
    request->test_type[0] = '\0';
    request->rgb_colour_present = false;
    request->red = 0U;
    request->green = 0U;
    request->blue = 0U;
    jsmn_init(&parser);
    token_count = jsmn_parse(
        &parser,
        line,
        line_length,
        tokens,
        JSON_PROTOCOL_TOKEN_CAPACITY
    );
    if ((token_count != 7 && token_count != 9 && token_count != 17) ||
        tokens[0].type != JSMN_OBJECT) {
        return false;
    }

    for (int index = 1; index < token_count;) {
        const jsmntok_t *key = &tokens[index];
        const jsmntok_t *value = &tokens[index + 1];

        index += 2;

        if (token_equals(line, key, "protocol_version")) {
            uint32_t version;
            if (version_seen || !parse_positive_uint32(line, value, &version) ||
                version != JSON_PROTOCOL_VERSION) {
                return false;
            }
            version_seen = true;
        } else if (token_equals(line, key, "type")) {
            if (type_seen || value->type != JSMN_STRING) {
                return false;
            }
            if (token_equals(line, value, "START_TEST")) {
                request->type = JSON_PROTOCOL_REQUEST_START_TEST;
            } else if (token_equals(line, value, "RUN_COMPONENT_TEST")) {
                request->type = JSON_PROTOCOL_REQUEST_RUN_COMPONENT_TEST;
            } else if (token_equals(line, value, "STOP_COMPONENT_TEST")) {
                request->type = JSON_PROTOCOL_REQUEST_STOP_COMPONENT_TEST;
            } else {
                request->type = JSON_PROTOCOL_REQUEST_UNSUPPORTED;
            }
            type_seen = true;
        } else if (token_equals(line, key, "command_id")) {
            if (command_id_seen || !parse_positive_uint32(
                    line, value, &request->command_id
                )) {
                return false;
            }
            command_id_seen = true;
        } else if (token_equals(line, key, "test_uuid")) {
            if (test_uuid_seen || !copy_test_uuid(line, value, request->test_uuid)) {
                return false;
            }
            test_uuid_seen = true;
        } else if (token_equals(line, key, "test_type")) {
            if (test_type_seen || !copy_test_type(line, value, request->test_type)) {
                return false;
            }
            test_type_seen = true;
        } else if (token_equals(line, key, "parameters")) {
            if (parameters_seen || !parse_rgb_parameters(
                    line, tokens, token_count, &index, request
                )) {
                return false;
            }
            parameters_seen = true;
        } else {
            return false;
        }
    }

    if (!version_seen || !type_seen || !command_id_seen) {
        return false;
    }
    if (request->type == JSON_PROTOCOL_REQUEST_START_TEST) {
        return token_count == 9 && test_uuid_seen && !test_type_seen &&
            !parameters_seen;
    }
    if (request->type == JSON_PROTOCOL_REQUEST_RUN_COMPONENT_TEST) {
        const bool is_rgb_led = strcmp(request->test_type, "rgb_led") == 0;
        return test_type_seen && !test_uuid_seen &&
            ((is_rgb_led && token_count == 17 && parameters_seen) ||
             (!is_rgb_led && token_count == 9 && !parameters_seen));
    }
    return request->type == JSON_PROTOCOL_REQUEST_STOP_COMPONENT_TEST &&
        token_count == 7 && !test_uuid_seen && !test_type_seen &&
        !parameters_seen;
}

bool json_protocol_build_start_test_response(
    uint32_t command_id,
    const session_metadata_t *metadata,
    char *destination,
    size_t capacity,
    size_t *length
)
{
    size_t offset = 0U;

    if (!append_format(
        destination,
        capacity,
        &offset,
        "{\"protocol_version\":1,\"type\":\"START_TEST_RESPONSE\","
        "\"command_id\":%lu,\"status\":\"ok\",\"device\":{"
        "\"uid\":\"%s\",\"mcu\":\"%s\",\"board_id\":\"%s\","
        "\"board_name\":\"%s\",\"board_revision\":\"%s\"},"
        "\"firmware\":{\"version\":\"%s\",\"git_revision\":\"%s\"},"
        "\"capabilities\":[",
        (unsigned long)command_id,
        metadata->uid,
        metadata->mcu_model,
        metadata->board_id,
        metadata->board_name,
        metadata->board_revision,
        metadata->firmware_version,
        metadata->firmware_git_revision
    )) {
        return false;
    }

    for (size_t index = 0U; index < metadata->capability_count; index++) {
        if (!append_format(
            destination,
            capacity,
            &offset,
            "%s\"%s\"",
            index == 0U ? "" : ",",
            metadata->capability_at(index)
        )) {
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
    uint32_t command_id,
    const char *error_code,
    char *destination,
    size_t capacity,
    size_t *length
)
{
    const int written = snprintf(
        destination,
        capacity,
        "{\"protocol_version\":1,\"type\":\"ERROR\",\"command_id\":%lu,"
        "\"error\":\"%s\"}",
        (unsigned long)command_id,
        error_code
    );

    if (written < 0 || (size_t)written >= capacity) {
        return false;
    }
    *length = (size_t)written;
    return true;
}

bool json_protocol_build_test_response(
    const char *response_type,
    uint32_t command_id,
    const char *test_type,
    const char *status,
    char *destination,
    size_t capacity,
    size_t *length
)
{
    const int written = snprintf(
        destination,
        capacity,
        "{\"protocol_version\":1,\"type\":\"%s\",\"command_id\":%lu,"
        "\"test_type\":\"%s\",\"status\":\"%s\"}",
        response_type,
        (unsigned long)command_id,
        test_type,
        status
    );

    if (written < 0 || (size_t)written >= capacity) {
        return false;
    }
    *length = (size_t)written;
    return true;
}

bool json_protocol_build_test_event(
    uint32_t command_id,
    const char *test_type,
    const component_test_event_t *event,
    char *destination,
    size_t capacity,
    size_t *length
)
{
    if (test_type == NULL || event == NULL || event->name == NULL) {
        return false;
    }
    const int written = event->kind == COMPONENT_TEST_EVENT_IMU_SAMPLE ? snprintf(
        destination, capacity,
        "{\"protocol_version\":1,\"type\":\"TEST_EVENT\",\"command_id\":%lu,"
        "\"test_type\":\"%s\",\"event\":\"%s\",\"data\":{"
        "\"acceleration_raw\":{\"x\":%d,\"y\":%d,\"z\":%d},"
        "\"gyroscope_raw\":{\"x\":%d,\"y\":%d,\"z\":%d}}}",
        (unsigned long)command_id, test_type, event->name,
        event->acceleration_x, event->acceleration_y, event->acceleration_z,
        event->gyroscope_x, event->gyroscope_y, event->gyroscope_z
    ) : snprintf(
        destination, capacity,
        "{\"protocol_version\":1,\"type\":\"TEST_EVENT\","
        "\"command_id\":%lu,\"test_type\":\"%s\",\"event\":\"%s\"}",
        (unsigned long)command_id, test_type, event->name
    );

    if (written < 0 || (size_t)written >= capacity) {
        return false;
    }
    *length = (size_t)written;
    return true;
}
