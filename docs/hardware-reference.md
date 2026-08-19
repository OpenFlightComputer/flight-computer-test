# Flight Computer V1 hardware reference

This document records the Milestone 0 inspection of the authoritative KiCad design. It is evidence for later board configuration and firmware board support, not a substitute for KiCad.

## Source snapshot

- Hardware repository: `/Users/jul/Private/projects/flightComputer/flight_computer_pcb/FlightComputer_V1`
- Branch: `main`
- Git commit: `e1f4bdebb0fe18a274fba08a50c99ed978c7ec72`
- Working tree: modified and untracked owner work was present during inspection; no hardware files were changed by this milestone
- `FlightComputer_V1.kicad_pro` SHA-256: `ed197e094f1406852b88b31015f0e1152ceef05802e561fce1d1354021c72d44`
- `FlightComputer_V1.kicad_sch` SHA-256: `90c675907b837f97d827d3e5cbc24ff5cf763a53324cc96fd155d12ba1f80347`
- `FlightComputer_V1.kicad_pcb` SHA-256: `3f0a6b184265de4666bb49451353d1cc9ca22d569f1a510fe64b1ad4d7d17f23`
- KiCad export tool observed: Eeschema 10.0.4
- Schematic title/revision: `First PCB`, revision `0.1`

The hashes above identify the exact files inspected despite the dirty hardware working tree. Recalculate them before deriving the Milestone 3 board configuration if the KiCad design changes.

## Test-relevant inventory

| Reference | Part/value | Interface or role |
| --- | --- | --- |
| U5 | STM32F405RGTx, corresponding project target STM32F405RGT6 | Main MCU, LQFP-64 |
| U1 | BMI270 | SPI-capable IMU with two interrupt lines |
| U3 | BMP388 | I2C-connected barometer; SDO and CSB are strapped for this mode/address selection |
| Card1 | XKTF-015-N | microSD socket using SPI signals plus card detect |
| USBC1 | TYPE-C-31-M-12 | USB-C receptacle, USB 2.0 data and VBUS |
| J5 | 1x5 connector | +3.3 V, SWDIO, SWCLK, NRST, GND |
| D4, D5 | Red and green LEDs | MCU-driven discrete status indicators through series resistors |
| LED1 | WS2812B-B/W | 5 V addressable RGB LED through a series data resistor |
| U2 | AP2112K-3.3 | 3.3 V regulator |
| U4 | AP64352SP-13 | 5 V buck regulator from ESC_VBAT |

## MCU signal mapping

Directions are from the MCU perspective. Alternate functions follow the STM32F405RG datasheet where the intended peripheral is unambiguous. `GPIO/analog` means no alternate-function selection is required. `TBD` is deliberate: the schematic fixes the pin but does not uniquely choose a firmware peripheral.

| MCU pin | Net | Direction | Intended interface | Alternate function / mode | Connected hardware | Test relevance |
| --- | --- | --- | --- | --- | --- | --- |
| PA1 | WS2812_DI | Output | WS2812 data | GPIO or timer mode TBD | R24 to LED1 DIN | RGB LED acceptance test |
| PA2 | GPS_RX | Output | GPS serial receive input | USART2_TX, AF7 | GPS connector/test point path | Future interface test |
| PA3 | GPS_TX | Input | GPS serial transmit output | USART2_RX, AF7 | GPS connector/test point path | Future interface test |
| PA4 | VBAT_ADC | Analog input | Battery-voltage sense | ADC1_IN4 | Divider/filter from ESC_VBAT | Outside V1 software power bring-up |
| PA5 | SD_SCK | Output | microSD SPI clock | SPI1_SCK, AF5 | Card1 CLK | microSD test |
| PA6 | SD_MISO | Input | microSD SPI data out | SPI1_MISO, AF5 | Card1 DAT0 | microSD test |
| PA7 | SD_MOSI | Output | microSD SPI command/data in | SPI1_MOSI, AF5 | Card1 CMD | microSD test |
| PA9 | USB VBUS divider net | Input | USB OTG FS VBUS sensing | OTG_FS_VBUS, AF10 | R31/R30 divider from USB_VBUS | USB CDC enumeration |
| PA11 | USB_DN | Bidirectional | USB D− | OTG_FS_DM, AF10 | R14 to USB-C DN pins | USB CDC protocol |
| PA12 | USB_DP | Bidirectional | USB D+ | OTG_FS_DP, AF10 | R15 to USB-C DP pins | USB CDC protocol |
| PA13 | SWDIO | Bidirectional | SWD data | JTMS/SWDIO, AF0 | J5 pin 2 | Programming and debug |
| PA14 | SWCLK | Input | SWD clock | JTCK/SWCLK, AF0 | J5 pin 3 | Programming and debug |
| PB0 | CURR_ADC | Analog input | ESC current sense | ADC1_IN8 | Divider/filter from ESC_CURR | Outside V1 |
| PB3 | IMU_SPI_SCK | Output | BMI270 SPI clock | SPI instance/AF TBD | U1 SCX | BMI270 test |
| PB4 | IMU_SPI_MISO | Input | BMI270 SPI data out | SPI instance/AF TBD | U1 SDO | BMI270 test |
| PB5 | IMU_SPI_MOSI | Output | BMI270 SPI data in | SPI instance/AF TBD | U1 SDX | BMI270 test |
| PB6 | IMU_INT2 | Input | BMI270 interrupt 2 | GPIO/EXTI | U1 INT2 | BMI270 test |
| PB9 | GPS_PPS | Input | GPS pulse per second | GPIO/EXTI or timer capture TBD | GPS connector/test point path | Future timing test |
| PB10 | I2C_SCL | Bidirectional/open-drain | BMP388 clock | I2C2_SCL, AF4 | U3 SCK with pull-up | BMP388 test |
| PB11 | I2C_SDA | Bidirectional/open-drain | BMP388 data | I2C2_SDA, AF4 | U3 SDI with pull-up | BMP388 test |
| PB13 | LED_RED | Output | Discrete red LED | GPIO | R22 to D4 | Status LED test |
| PB14 | LED_GREEN | Output | Discrete green LED | GPIO | R23 to D5 | Status LED test |
| PC4 | SD_CS | Output | microSD chip select | GPIO | Card1 CD/DAT3 plus pull-up | microSD test |
| PC5 | SD_DET | Input | microSD card detect | GPIO/EXTI | Card1 CD plus pull-up | microSD test |
| PC6 | ESC_M4 | Output | Motor/ESC channel 4 | TIM8_CH1, AF3 candidate | Series resistor to P1 | Outside V1 |
| PC7 | ESC_M3 | Output | Motor/ESC channel 3 | TIM8_CH2, AF3 candidate | Series resistor to P1 | Outside V1 |
| PC8 | ESC_M2 | Output | Motor/ESC channel 2 | TIM8_CH3, AF3 candidate | Series resistor to P1 | Outside V1 |
| PC9 | ESC_M1 | Output | Motor/ESC channel 1 | TIM8_CH4, AF3 candidate | Series resistor to P1 | Outside V1 |
| PC10 | RP1_RX | Output | Receiver/telemetry serial | UART4_TX AF8 or USART3_TX AF7, TBD | Test point/external path | Future interface test |
| PC11 | RP1_TX | Input | Receiver/telemetry serial | UART4_RX AF8 or USART3_RX AF7, TBD | Test point/external path | Future interface test |
| PC12 | IMU_INT1 | Input | BMI270 interrupt 1 | GPIO/EXTI | U1 INT1 | BMI270 test |
| PD2 | IMU_CS | Output | BMI270 chip select | GPIO | U1 CSB | BMI270 test |
| PH0 | HSE_IN | Input | External clock | OSC_IN | Y1 | Runtime/clock sanity |
| PH1 | HSE_OUT | Output | External clock | OSC_OUT | Y1 | Runtime/clock sanity |
| NRST | NRST | Input/open-drain | Reset | Reset function | J5 and reset switch | Flash/reset workflow |
| BOOT0 | BOOT0 | Input | Boot selection | Boot strap | Pull-down and switch | Bring-up/recovery |

Signal names such as `GPS_RX` and `RP1_RX` appear to be named from the external peripheral perspective; the direction and UART function columns make the MCU-side meaning explicit.

## Interface observations

- The BMP388 is wired for I2C: CSB is tied to +3.3 V and SDO is tied to GND. Its interrupt pin is unconnected.
- The BMI270 is routed as a four-wire SPI device. PB3/PB4/PB5 can support multiple STM32 SPI alternate mappings, so firmware must select and document one consistently rather than infer it from the net names.
- The microSD socket is routed in SPI mode through SPI1 pins and includes a dedicated card-detect signal.
- USB-C D+/D− route to the STM32 OTG FS pins. CC1 and CC2 each have pull-down resistors. VBUS reaches PA9 through a divider/sense path rather than a direct net label.
- The SWD header exposes the complete V1 programming set required by the board-tester workflow.
- The red and green discrete LEDs require hardware review before Milestone 11. Both the schematic netlist and PCB connect D4/D5 pad 2 (`A`) to GND and pad 1 (`K`) toward the MCU through a resistor. That appears reversed for the standard KiCad LED symbol and cannot be solved merely by choosing active-high versus active-low firmware.
- The WS2812 is powered from +5 V and takes 3.3 V MCU data through R24 with no level shifter shown. Validate the actual part's input-high threshold/noise margin during bring-up rather than assuming guaranteed logic compatibility.

## Revision and authority warning

The schematic title block revision (`0.1`) does not match the highest generated production filename observed (`flightcomputer_v1.7_*`). Those filenames are not sufficient authority to relabel the PCB. Resolve the intended public board revision with the owner before creating an immutable test configuration or publishing acceptance results.

## External MCU references

- STMicroelectronics STM32F405/407 datasheet (DS8626): <https://www.st.com/resource/en/datasheet/stm32f405rg.pdf>
- STMicroelectronics STM32F4 reference manual (RM0090): <https://www.st.com/resource/en/reference_manual/rm0090-stm32f4xx-reference-manual-stmicroelectronics.pdf>
