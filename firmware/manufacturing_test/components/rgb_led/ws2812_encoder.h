#ifndef OPENFLIGHTCOMPUTER_WS2812_ENCODER_H
#define OPENFLIGHTCOMPUTER_WS2812_ENCODER_H

#include <stddef.h>
#include <stdint.h>

#define WS2812_DATA_BITS 24U
#define WS2812_RESET_PERIODS 256U
#define WS2812_FRAME_VALUES (WS2812_DATA_BITS + WS2812_RESET_PERIODS)
#define WS2812_ZERO_HIGH_TICKS 29U
#define WS2812_ONE_HIGH_TICKS 59U

void ws2812_encode(
    uint8_t red,
    uint8_t green,
    uint8_t blue,
    uint16_t destination[WS2812_FRAME_VALUES]
);

#endif
