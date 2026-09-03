#include "session_protocol.h"

#include "component_registry.h"
#include "component_test_runner.h"
#include "json_protocol.h"
#include "session_metadata.h"
#include "usb_cdc_transport.h"

#define SESSION_PROTOCOL_LINE_CAPACITY 4097U

static uint8_t line_buffer[SESSION_PROTOCOL_LINE_CAPACITY];
static component_test_runner_t component_test_runner;

static void queue_response(const uint8_t *line, size_t response_length)
{
    (void)usb_cdc_transport_queue_line(line, response_length);
}

static void process_line(uint8_t *line, size_t line_length)
{
    json_protocol_request_t request;
    session_metadata_t metadata;
    size_t response_length;
    bool response_ready;

    if (!json_protocol_parse_request(
            (const char *)line, line_length, &request
        )) {
        /* Malformed JSON or a request shape outside the protocol contract. */
        response_ready = json_protocol_build_error_response(
            0U,
            "invalid_request",
            (char *)line,
            SESSION_PROTOCOL_LINE_CAPACITY,
            &response_length
        );
    } else if (request.type == JSON_PROTOCOL_REQUEST_START_TEST) {
        /* Session initialization: return immutable device and firmware metadata. */
        session_metadata_read(&metadata);
        response_ready = json_protocol_build_start_test_response(
            request.command_id,
            &metadata,
            (char *)line,
            SESSION_PROTOCOL_LINE_CAPACITY,
            &response_length
        );
    } else if (request.type == JSON_PROTOCOL_REQUEST_RUN_COMPONENT_TEST) {
        const component_test_definition_t *definition;

        if (component_test_runner_state(&component_test_runner) !=
            COMPONENT_TEST_RUNNER_IDLE) {
            /* A test is already active; component tests are never queued. */
            response_ready = json_protocol_build_error_response(
                request.command_id, "test_already_active", (char *)line,
                SESSION_PROTOCOL_LINE_CAPACITY, &response_length
            );
        } else {
            definition = component_registry_find(
                component_registry_get(), request.test_type
            );
            if (definition == NULL) {
                /* The requested type is not implemented by this firmware build. */
                response_ready = json_protocol_build_error_response(
                    request.command_id, "unsupported_test_type", (char *)line,
                    SESSION_PROTOCOL_LINE_CAPACITY, &response_length
                );
            } else {
                const component_test_parameters_t parameters = {
                    .rgb_colour_present = request.rgb_colour_present,
                    .red = request.red,
                    .green = request.green,
                    .blue = request.blue,
                };
                /* The registry entry is runnable: make it the single active test. */
                (void)component_test_runner_start(
                    &component_test_runner, definition, request.command_id,
                    &parameters
                );
                response_ready = json_protocol_build_test_response(
                    "TEST_STARTED", request.command_id, definition->type, "running",
                    (char *)line, SESSION_PROTOCOL_LINE_CAPACITY, &response_length
                );
            }
        }
    } else if (request.type == JSON_PROTOCOL_REQUEST_STOP_COMPONENT_TEST) {
        const char *active_type = component_test_runner_active_type(
            &component_test_runner
        );

        if (active_type == NULL) {
            /* There is no running test for this stop command to cancel. */
            response_ready = json_protocol_build_error_response(
                request.command_id, "no_active_test", (char *)line,
                SESSION_PROTOCOL_LINE_CAPACITY, &response_length
            );
        } else {
            /* Clear active state and run component cleanup before acknowledging stop. */
            (void)component_test_runner_stop(&component_test_runner);
            response_ready = json_protocol_build_test_response(
                "TEST_STOPPED", request.command_id, active_type, "stopped",
                (char *)line, SESSION_PROTOCOL_LINE_CAPACITY, &response_length
            );
        }
    } else {
        /* The JSON was valid, but its message type is not implemented. */
        response_ready = json_protocol_build_error_response(
            request.command_id,
            "unsupported_message_type",
            (char *)line,
            SESSION_PROTOCOL_LINE_CAPACITY,
            &response_length
        );
    }

    if (response_ready) {
        queue_response(line, response_length);
    }
}

void session_protocol_initialize(void)
{
    component_test_runner_initialize(&component_test_runner);
}

void session_protocol_process(void)
{
    size_t line_length;

    /* Leave complete requests queued until their response has somewhere to go. */
    while (usb_cdc_transport_can_queue_line() && usb_cdc_transport_read_line(
        line_buffer,
        sizeof(line_buffer),
        &line_length
    ) == USB_CDC_LINE_AVAILABLE) {
        process_line(line_buffer, line_length);
    }

    if (usb_cdc_transport_can_queue_line() &&
        component_test_runner_state(&component_test_runner) ==
            COMPONENT_TEST_RUNNER_RUNNING) {
        const char *active_type = component_test_runner_active_type(
            &component_test_runner
        );
        const uint32_t command_id = component_test_runner_active_command_id(
            &component_test_runner
        );
        const component_test_runner_update_t update =
            component_test_runner_process(&component_test_runner);

        if (update != COMPONENT_TEST_RUNNER_UPDATE_NONE) {
            size_t response_length;
            bool response_ready;

            if (update == COMPONENT_TEST_RUNNER_UPDATE_EVENT) {
                /* An active component emitted a non-terminal event. */
                response_ready = json_protocol_build_test_event(
                    command_id, active_type,
                    component_test_runner_event(&component_test_runner),
                    (char *)line_buffer, sizeof(line_buffer), &response_length
                );
            } else {
                /* The component completed, so report its terminal pass/fail state. */
                response_ready = json_protocol_build_test_response(
                    "TEST_COMPLETED", command_id, active_type,
                    update == COMPONENT_TEST_RUNNER_UPDATE_PASSED ? "passed" : "failed",
                    (char *)line_buffer, sizeof(line_buffer), &response_length
                );
            }
            if (response_ready) {
                queue_response(line_buffer, response_length);
            }
        }
    }
}
