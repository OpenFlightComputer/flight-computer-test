# Flight Computer V1 board support

This board definition targets the STM32F405RGT6 manufacturing revision 1.7 hardware generated from schematic revision 0.1.

Board support provides the STM32F405 memory map, HAL configuration, core interrupt handlers, and system-clock setup. The 16 MHz HSE is multiplied to 168 MHz SYSCLK while preserving the 48 MHz USB clock.

The firmware side of Milestone 6 configures PA11/PA12 for USB OTG FS alternate function 10, PA9 for VBUS sensing, and the OTG FS interrupt at priority 6. `usb_device_port.c` is the narrow adapter between the official ST USB Device core and the STM32 HAL PCD driver. The board is described as bus-powered because USB VBUS supplies its 5 V input path.

Other peripheral pin initialization remains deferred to the relevant component milestones. Ambiguous BMI270 SPI, receiver UART, and ESC timer selections are not guessed here.
