#ifndef OPENFLIGHTCOMPUTER_USB_CDC_TRANSPORT_H
#define OPENFLIGHTCOMPUTER_USB_CDC_TRANSPORT_H

#include "newline_framer.h"

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

typedef enum {
    USB_CDC_LINE_UNAVAILABLE = 0,
    USB_CDC_LINE_AVAILABLE = 1,
    USB_CDC_LINE_BUFFER_TOO_SMALL = 2,
} usb_cdc_line_result_t;

typedef struct {
    uint32_t received_bytes_dropped;
    uint32_t completed_lines_dropped;
    uint32_t oversized_lines_dropped;
    uint32_t transmitted_lines_dropped;
} usb_cdc_transport_statistics_t;

bool usb_cdc_transport_initialize(void);
void usb_cdc_transport_process(void);

usb_cdc_line_result_t usb_cdc_transport_read_line(
    uint8_t *destination,
    size_t capacity,
    size_t *length
);

bool usb_cdc_transport_queue_line(const uint8_t *line, size_t length);
bool usb_cdc_transport_can_queue_line(void);
usb_cdc_transport_statistics_t usb_cdc_transport_statistics(void);

#endif
