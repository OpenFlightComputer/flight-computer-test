#include "ws2812_encoder.h"

#include <assert.h>
#include <stddef.h>

static void assert_encoded_byte(
    const uint16_t *encoded,
    uint8_t expected
)
{
    for (size_t bit = 0U; bit < 8U; bit++) {
        const uint8_t mask = (uint8_t)(0x80U >> bit);
        const uint16_t expected_ticks = (expected & mask) == 0U ?
            WS2812_ZERO_HIGH_TICKS : WS2812_ONE_HIGH_TICKS;
        assert(encoded[bit] == expected_ticks);
    }
}

static void test_encoder_uses_grb_wire_order(void)
{
    uint16_t frame[WS2812_FRAME_VALUES];

    ws2812_encode(0x81U, 0x42U, 0x24U, frame);

    assert_encoded_byte(&frame[0], 0x42U);
    assert_encoded_byte(&frame[8], 0x81U);
    assert_encoded_byte(&frame[16], 0x24U);
}

static void test_encoder_appends_low_reset_period(void)
{
    uint16_t frame[WS2812_FRAME_VALUES];

    ws2812_encode(0xFFU, 0xFFU, 0xFFU, frame);

    for (size_t index = WS2812_DATA_BITS;
         index < WS2812_FRAME_VALUES;
         index++) {
        assert(frame[index] == 0U);
    }
}

int main(void)
{
    test_encoder_uses_grb_wire_order();
    test_encoder_appends_low_reset_period();
    return 0;
}
