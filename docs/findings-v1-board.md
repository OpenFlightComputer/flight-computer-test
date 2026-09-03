# Flight Computer V1 board findings

This document records what was learned from the first assembled Flight Computer
V1. Manufacturing revision 1.7 was generated from schematic revision 0.1. The
findings are hardware facts and V2 inputs, not unresolved tester assumptions.

## Accepted hardware

The following paths worked in a complete physical acceptance run:

- STM32F405 programming, verification, and reset over SWD;
- 16 MHz HSE and the configured 168 MHz system/48 MHz USB clocks;
- USB Full Speed CDC communication after applying the V1 VBUS workaround;
- PA1 through R24 to the WS2812 DIN, including turquoise RGB output;
- BMI270 communication over SPI3 and changing accelerometer/gyroscope samples;
- BMP388 communication over I2C2 and changing compensated pressure/temperature;
- active-low microSD card detection, SPI1 initialization, raw write, read-back,
  checksum verification, and cleanup.

## Confirmed V1 limitations

### D4 and D5 polarity

D4 and D5 are reversed in the schematic/PCB connection for the selected LED
symbol: their anodes are connected toward ground and their cathodes toward the
MCU through R22/R23. They cannot illuminate as assembled and cannot be repaired
by changing GPIO polarity. Configuration v005 therefore disabled both status
LED tests, and the current v006 procedure omits them entirely. V2 must correct
the schematic, footprint orientation, and assembly marking before those tests
are re-enabled.

### USB VBUS sensing

Revision 0.1 connects USB VBUS to PA9 through two 100 kOhm resistors. Although
an unloaded equal divider suggests 2.5 V, the assembled sensing node measured
about 1 V and did not satisfy the STM32 USB VBUS input. V1 manufacturing
firmware therefore disables hardware VBUS sensing and assumes VBUS is present.
V2 must use the STM32F405-supported VBUS topology and then re-enable sensing in
firmware.

### WS2812 interface

The LED has a valid 5 V supply, PA1 reaches DIN through the approximately 330
ohm R24 path, and a cycle-counted 3.3 V GPIO waveform illuminates it. The V1
board therefore works without a level shifter on the tested unit, but V2 should
add an appropriate 3.3 V-to-5 V logic buffer to provide repeatable input-high
margin rather than relying on unit-specific tolerance.

## V2 board actions

1. Correct D4/D5 polarity and add unambiguous diode orientation markings.
2. Correct PA9 VBUS sensing and remove the V1-only software workaround.
3. Add a logic-level buffer for WS2812 DIN while retaining a series resistor.
4. Add labelled test pads for 5 V, 3.3 V, ground, reset, SWD, VBUS sense, RGB
   DIN, SPI clocks/data/chip selects, I2C clock/data, and SD card detect.
5. Give the revised hardware its own board revision identity and configuration.
6. Resolve the remaining receiver UART and ESC timer assignments before release.
7. Require clean ERC/DRC results and an assembly-polarity review before ordering.

## Flight-firmware implications

V1 flight firmware must retain the VBUS-sensing workaround if USB is enabled
and must not rely on D4/D5 for health indication. The validated SPI3/BMI270,
I2C2/BMP388, SPI1/microSD, clock, and PA1 routes are suitable starting points
for production drivers, subject to flight-specific scheduling and fault policy.
