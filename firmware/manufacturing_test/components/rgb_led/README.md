# RGB LED component

Flight Computer V1 drives the WS2812B-family LED on PA1 through TIM2 channel 2
and DMA1 stream 6/channel 3. The timer produces the 800 kHz wire timing while
DMA supplies one compare value per bit without blocking the application loop.

The component test currently lights a fixed turquoise value. The tester-side
follow-up will send raw RGB values chosen by the Python handler; the encoder
will continue to translate that RGB API into the LED's GRB wire order.
