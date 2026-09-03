# RGB LED component

Flight Computer V1 drives its single WS2812B-family LED on PA1 with direct GPIO
writes timed by the Cortex-M4 cycle counter. Interrupts are masked for the
approximately 30 microseconds needed to send one 24-bit frame, then restored to
their previous state. This implementation was verified on the assembled V1
board after the original TIM2/PWM/DMA implementation produced no LED output.

The board tester sends raw RGB values selected by its human-friendly colour
policy. The encoder translates that RGB API into the LED's GRB wire order.
