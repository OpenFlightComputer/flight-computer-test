#include "ws2812_encoder.h"

#include <assert.h>
#include <stdint.h>

static void test_encoder_uses_grb_wire_order(void)
{
    uint8_t frame[WS2812_FRAME_BYTES];

    ws2812_encode(0x81U, 0x42U, 0x24U, frame);

    assert(frame[0] == 0x42U);
    assert(frame[1] == 0x81U);
    assert(frame[2] == 0x24U);
}

int main(void)
{
    test_encoder_uses_grb_wire_order();
    return 0;
}
