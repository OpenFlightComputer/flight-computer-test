#include "json_protocol.h"

#include <assert.h>
#include <stddef.h>
#include <stdint.h>
#include <string.h>

static void test_start_request_is_decoded_independent_of_field_order(void)
{
    static const char request[] =
        "{\"test_uuid\":\"ccc7d571-141e-4054-8e77-6ac3a97ababa\","
        "\"command_id\":7,\"type\":\"START_TEST\","
        "\"protocol_version\":1}";
    json_protocol_request_t parsed;

    assert(json_protocol_parse_request(
        request,
        sizeof(request) - 1U,
        &parsed
    ));
    assert(parsed.type == JSON_PROTOCOL_REQUEST_START_TEST);
    assert(parsed.command_id == 7U);
    assert(strcmp(parsed.test_uuid, "ccc7d571-141e-4054-8e77-6ac3a97ababa") == 0);
}

static void test_malformed_or_unknown_fields_are_rejected(void)
{
    static const char malformed[] =
        "{\"protocol_version\":1,\"type\":\"START_TEST\","
        "\"command_id\":1}";
    static const char unknown[] =
        "{\"protocol_version\":1,\"type\":\"START_TEST\","
        "\"command_id\":1,\"test_uuid\":\"ccc7d571-141e-4054-8e77-6ac3a97ababa\","
        "\"extra\":true}";
    static const char invalid_uuid[] =
        "{\"protocol_version\":1,\"type\":\"START_TEST\","
        "\"command_id\":1,\"test_uuid\":\"ccc7d571-141e-5054-8e77-6ac3a97ababa\"}";
    json_protocol_request_t parsed;

    assert(!json_protocol_parse_request(
        malformed,
        sizeof(malformed) - 1U,
        &parsed
    ));
    assert(!json_protocol_parse_request(
        unknown,
        sizeof(unknown) - 1U,
        &parsed
    ));
    assert(!json_protocol_parse_request(
        invalid_uuid,
        sizeof(invalid_uuid) - 1U,
        &parsed
    ));
}

static void test_start_response_contains_session_metadata(void)
{
    static const char *const capabilities[] = {"mcu_runtime"};
    const session_metadata_t metadata = {
        .uid = "00112233445566778899AABB",
        .mcu_model = "STM32F405RGT6",
        .board_id = "flightcomputer-v1",
        .board_name = "Flight Computer V1",
        .board_revision = "1.7",
        .firmware_version = "0.1.0",
        .firmware_git_revision = "abc123",
        .capabilities = capabilities,
        .capability_count = 1U,
    };
    char response[512];
    size_t length;

    assert(json_protocol_build_start_test_response(
        7U,
        &metadata,
        response,
        sizeof(response),
        &length
    ));
    assert(length == strlen(response));
    assert(strstr(response, "\"command_id\":7") != NULL);
    assert(strstr(response, "\"uid\":\"00112233445566778899AABB\"") != NULL);
    assert(strstr(response, "\"capabilities\":[\"mcu_runtime\"]") != NULL);
}

int main(void)
{
    test_start_request_is_decoded_independent_of_field_order();
    test_malformed_or_unknown_fields_are_rejected();
    test_start_response_contains_session_metadata();
    return 0;
}
