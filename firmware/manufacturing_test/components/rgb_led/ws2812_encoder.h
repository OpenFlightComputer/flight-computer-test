#ifndef OPENFLIGHTCOMPUTER_WS2812_ENCODER_H
#define OPENFLIGHTCOMPUTER_WS2812_ENCODER_H

#include <stdint.h>

#define WS2812_FRAME_BYTES 3U
#define WS2812_DATA_BITS (WS2812_FRAME_BYTES * 8U)

void ws2812_encode(
    uint8_t red,
    uint8_t green,
    uint8_t blue,
    uint8_t destination[WS2812_FRAME_BYTES]
);

#endif
