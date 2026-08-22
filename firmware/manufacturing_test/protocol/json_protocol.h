#ifndef OPENFLIGHTCOMPUTER_JSON_PROTOCOL_H
#define OPENFLIGHTCOMPUTER_JSON_PROTOCOL_H

#include "session_metadata.h"

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#define JSON_PROTOCOL_VERSION 1U
#define JSON_PROTOCOL_TEST_UUID_LENGTH 36U
#define JSON_PROTOCOL_TEST_TYPE_CAPACITY 32U

typedef enum {
    JSON_PROTOCOL_REQUEST_START_TEST = 0,
    JSON_PROTOCOL_REQUEST_RUN_COMPONENT_TEST = 1,
    JSON_PROTOCOL_REQUEST_STOP_COMPONENT_TEST = 2,
    JSON_PROTOCOL_REQUEST_INVALID = 3,
    JSON_PROTOCOL_REQUEST_UNSUPPORTED = 4,
} json_protocol_request_type_t;

typedef struct {
    json_protocol_request_type_t type;
    uint32_t command_id;
    char test_uuid[JSON_PROTOCOL_TEST_UUID_LENGTH + 1U];
    char test_type[JSON_PROTOCOL_TEST_TYPE_CAPACITY];
    bool rgb_colour_present;
    uint8_t red;
    uint8_t green;
    uint8_t blue;
} json_protocol_request_t;

bool json_protocol_parse_request(
    const char *line,
    size_t line_length,
    json_protocol_request_t *request
);
bool json_protocol_build_start_test_response(
    uint32_t command_id,
    const session_metadata_t *metadata,
    char *destination,
    size_t capacity,
    size_t *length
);
bool json_protocol_build_error_response(
    uint32_t command_id,
    const char *error_code,
    char *destination,
    size_t capacity,
    size_t *length
);
bool json_protocol_build_test_response(
    const char *response_type,
    uint32_t command_id,
    const char *test_type,
    const char *status,
    char *destination,
    size_t capacity,
    size_t *length
);
bool json_protocol_build_test_event(
    uint32_t command_id,
    const char *test_type,
    const char *event,
    char *destination,
    size_t capacity,
    size_t *length
);

#endif
