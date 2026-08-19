# Flight Computer V1 board support

This board definition targets the STM32F405RGT6 manufacturing revision 1.7 hardware generated from schematic revision 0.1.

Milestone 4 provides the STM32F405 memory map, HAL configuration, core interrupt handlers, and system-clock setup. The 16 MHz HSE is multiplied to 168 MHz SYSCLK while preserving the 48 MHz clock required by later USB work.

Peripheral pin initialization remains deferred to the relevant component milestones. Ambiguous BMI270 SPI, receiver UART, and ESC timer selections are not guessed here.
