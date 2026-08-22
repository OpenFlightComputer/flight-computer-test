#include "json_protocol.h"

#include <assert.h>
#include <stddef.h>
#include <stdint.h>
#include <string.h>

static const char *test_capability_at(size_t index)
{
    static const char *const capabilities[] = {"mcu_runtime"};

    return capabilities[index];
}

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
    const session_metadata_t metadata = {
        .uid = "00112233445566778899AABB",
        .mcu_model = "STM32F405RGT6",
        .board_id = "flightcomputer-v1",
        .board_name = "Flight Computer V1",
        .board_revision = "1.7",
        .firmware_version = "0.1.0",
        .firmware_git_revision = "abc123",
        .capability_at = test_capability_at,
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

static void test_component_requests_are_decoded(void)
{
    static const char run_request[] =
        "{\"protocol_version\":1,\"type\":\"RUN_COMPONENT_TEST\","
        "\"command_id\":8,\"test_type\":\"status_led_red\"}";
    static const char stop_request[] =
        "{\"protocol_version\":1,\"type\":\"STOP_COMPONENT_TEST\","
        "\"command_id\":9}";
    json_protocol_request_t parsed;

    assert(json_protocol_parse_request(
        run_request, sizeof(run_request) - 1U, &parsed
    ));
    assert(parsed.type == JSON_PROTOCOL_REQUEST_RUN_COMPONENT_TEST);
    assert(strcmp(parsed.test_type, "status_led_red") == 0);
    assert(json_protocol_parse_request(
        stop_request, sizeof(stop_request) - 1U, &parsed
    ));
    assert(parsed.type == JSON_PROTOCOL_REQUEST_STOP_COMPONENT_TEST);
}

static void test_rgb_parameters_are_decoded_in_any_field_order(void)
{
    static const char request[] =
        "{\"parameters\":{\"blue\":200,\"red\":40,\"green\":220},"
        "\"test_type\":\"rgb_led\",\"command_id\":8,"
        "\"type\":\"RUN_COMPONENT_TEST\",\"protocol_version\":1}";
    json_protocol_request_t parsed;

    assert(json_protocol_parse_request(request, sizeof(request) - 1U, &parsed));
    assert(parsed.rgb_colour_present);
    assert(parsed.red == 40U);
    assert(parsed.green == 220U);
    assert(parsed.blue == 200U);
}

static void test_invalid_rgb_parameters_are_rejected(void)
{
    static const char absent[] =
        "{\"protocol_version\":1,\"type\":\"RUN_COMPONENT_TEST\","
        "\"command_id\":8,\"test_type\":\"rgb_led\"}";
    static const char missing[] =
        "{\"protocol_version\":1,\"type\":\"RUN_COMPONENT_TEST\","
        "\"command_id\":8,\"test_type\":\"rgb_led\","
        "\"parameters\":{\"red\":40,\"green\":220}}";
    static const char out_of_range[] =
        "{\"protocol_version\":1,\"type\":\"RUN_COMPONENT_TEST\","
        "\"command_id\":8,\"test_type\":\"rgb_led\","
        "\"parameters\":{\"red\":256,\"green\":220,\"blue\":200}}";
    json_protocol_request_t parsed;

    assert(!json_protocol_parse_request(absent, sizeof(absent) - 1U, &parsed));
    assert(!json_protocol_parse_request(missing, sizeof(missing) - 1U, &parsed));
    assert(!json_protocol_parse_request(
        out_of_range, sizeof(out_of_range) - 1U, &parsed
    ));
}

static void test_component_response_is_serialized(void)
{
    char response[256];
    size_t length;

    assert(json_protocol_build_test_response(
        "TEST_STARTED", 8U, "rgb_led", "running", response,
        sizeof(response), &length
    ));
    assert(length == strlen(response));
    assert(strstr(response, "\"type\":\"TEST_STARTED\"") != NULL);
    assert(strstr(response, "\"test_type\":\"rgb_led\"") != NULL);
    assert(json_protocol_build_test_event(
        8U, "rgb_led", "operator_confirmation_required", response,
        sizeof(response), &length
    ));
    assert(strstr(response, "\"type\":\"TEST_EVENT\"") != NULL);
}

int main(void)
{
    test_start_request_is_decoded_independent_of_field_order();
    test_malformed_or_unknown_fields_are_rejected();
    test_start_response_contains_session_metadata();
    test_component_requests_are_decoded();
    test_rgb_parameters_are_decoded_in_any_field_order();
    test_invalid_rgb_parameters_are_rejected();
    test_component_response_is_serialized();
    return 0;
}
