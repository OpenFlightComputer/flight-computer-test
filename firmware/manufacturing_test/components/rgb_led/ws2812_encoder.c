#include "ws2812_encoder.h"

void ws2812_encode(
    uint8_t red,
    uint8_t green,
    uint8_t blue,
    uint8_t destination[WS2812_FRAME_BYTES]
)
{
    /* WS2812 wire order is green, red, blue even though callers use RGB. */
    destination[0] = green;
    destination[1] = red;
    destination[2] = blue;
}
