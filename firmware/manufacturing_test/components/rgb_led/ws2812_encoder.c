#include "ws2812_encoder.h"

static void encode_byte(uint8_t value, uint16_t *destination)
{
    for (size_t bit = 0U; bit < 8U; bit++) {
        const uint8_t mask = (uint8_t)(0x80U >> bit);
        destination[bit] = (value & mask) == 0U ?
            WS2812_ZERO_HIGH_TICKS : WS2812_ONE_HIGH_TICKS;
    }
}

void ws2812_encode(
    uint8_t red,
    uint8_t green,
    uint8_t blue,
    uint16_t destination[WS2812_FRAME_VALUES]
)
{
    /* WS2812 wire order is green, red, blue even though callers use RGB. */
    encode_byte(green, &destination[0]);
    encode_byte(red, &destination[8]);
    encode_byte(blue, &destination[16]);

    /* A zero compare value holds DIN low for the complete PWM period. */
    for (size_t index = WS2812_DATA_BITS; index < WS2812_FRAME_VALUES; index++) {
        destination[index] = 0U;
    }
}
