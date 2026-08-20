#include "json_protocol.h"

#define JSMN_STATIC
#include "third_party/jsmn.h"

#include <stdio.h>
#include <stdarg.h>
#include <string.h>

#define JSON_PROTOCOL_TOKEN_CAPACITY 16U

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
    int token_count;

    request->type = JSON_PROTOCOL_REQUEST_INVALID;
    request->command_id = 0U;
    request->test_uuid[0] = '\0';
    jsmn_init(&parser);
    token_count = jsmn_parse(
        &parser,
        line,
        line_length,
        tokens,
        JSON_PROTOCOL_TOKEN_CAPACITY
    );
    if (token_count != 9 || tokens[0].type != JSMN_OBJECT) {
        return false;
    }

    for (int index = 1; index < token_count; index += 2) {
        const jsmntok_t *key = &tokens[index];
        const jsmntok_t *value = &tokens[index + 1];

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
            request->type = token_equals(line, value, "START_TEST") ?
                JSON_PROTOCOL_REQUEST_START_TEST : JSON_PROTOCOL_REQUEST_UNSUPPORTED;
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
        } else {
            return false;
        }
    }

    return version_seen && type_seen && command_id_seen && test_uuid_seen;
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
            metadata->capabilities[index]
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
