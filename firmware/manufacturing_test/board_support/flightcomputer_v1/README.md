# Flight Computer V1 board support

This board definition targets the STM32F405RGT6 manufacturing revision 1.7 hardware generated from schematic revision 0.1.

Board support provides the STM32F405 memory map, HAL configuration, core interrupt handlers, and system-clock setup. The 16 MHz HSE is multiplied to 168 MHz SYSCLK while preserving the 48 MHz USB clock.

PA11/PA12 use USB OTG FS alternate function 10 and the OTG FS interrupt runs at priority 6. `usb_device_port.c` is the narrow adapter between the official ST USB Device core and the STM32 HAL PCD driver. Revision 0.1's PA9 VBUS divider was measured below the valid sensing threshold, so this V1 definition disables VBUS sensing and assumes the bus-powered USB connection is present. A corrected board revision must restore hardware VBUS sensing.

Physical acceptance confirmed SPI3 for the BMI270, I2C2 for the BMP388, SPI1 and active-low detection for microSD, and PA1 for the WS2812. Receiver UART and ESC timer selections remain outside the V1 tester and must be resolved before flight-firmware implementation.
