#include "session_protocol.h"

#include "json_protocol.h"
#include "session_metadata.h"
#include "usb_cdc_transport.h"

#define SESSION_PROTOCOL_LINE_CAPACITY 4097U

static uint8_t line_buffer[SESSION_PROTOCOL_LINE_CAPACITY];

static void process_line(uint8_t *line, size_t line_length)
{
    json_protocol_request_t request;
    session_metadata_t metadata;
    size_t response_length;
    bool response_ready;

    if (!json_protocol_parse_request(
            (const char *)line, line_length, &request
        )) {
        response_ready = json_protocol_build_error_response(
            0U,
            "invalid_request",
            (char *)line,
            SESSION_PROTOCOL_LINE_CAPACITY,
            &response_length
        );
    } else if (request.type == JSON_PROTOCOL_REQUEST_START_TEST) {
        session_metadata_read(&metadata);
        response_ready = json_protocol_build_start_test_response(
            request.command_id,
            &metadata,
            (char *)line,
            SESSION_PROTOCOL_LINE_CAPACITY,
            &response_length
        );
    } else {
        response_ready = json_protocol_build_error_response(
            request.command_id,
            "unsupported_message_type",
            (char *)line,
            SESSION_PROTOCOL_LINE_CAPACITY,
            &response_length
        );
    }

    if (response_ready) {
        (void)usb_cdc_transport_queue_line(
            line,
            response_length
        );
    }
}

void session_protocol_process(void)
{
    size_t line_length;

    while (usb_cdc_transport_read_line(
        line_buffer,
        sizeof(line_buffer),
        &line_length
    ) == USB_CDC_LINE_AVAILABLE) {
        process_line(line_buffer, line_length);
    }
}
