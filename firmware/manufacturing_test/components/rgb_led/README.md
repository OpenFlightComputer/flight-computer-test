# RGB LED component

Flight Computer V1 drives the WS2812B-family LED on PA1 through TIM2 channel 2
and DMA1 stream 6/channel 3. The timer produces the 800 kHz wire timing while
DMA supplies one compare value per bit without blocking the application loop.

The board tester sends raw RGB values selected by its human-friendly colour
policy. The encoder translates that RGB API into the LED's GRB wire order.
