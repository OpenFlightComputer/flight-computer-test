#ifndef OPENFLIGHTCOMPUTER_JSON_PROTOCOL_H
#define OPENFLIGHTCOMPUTER_JSON_PROTOCOL_H

#include "session_metadata.h"

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#define JSON_PROTOCOL_VERSION 1U
#define JSON_PROTOCOL_TEST_UUID_LENGTH 36U

typedef enum {
    JSON_PROTOCOL_REQUEST_START_TEST = 0,
    JSON_PROTOCOL_REQUEST_INVALID = 1,
    JSON_PROTOCOL_REQUEST_UNSUPPORTED = 2,
} json_protocol_request_type_t;

typedef struct {
    json_protocol_request_type_t type;
    uint32_t command_id;
    char test_uuid[JSON_PROTOCOL_TEST_UUID_LENGTH + 1U];
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

#endif
