# Flight Computer V1 tester findings

The V1 tester reached a complete physical pass by treating each failure as a
layered system problem. The recurring method was:

1. reduce the failing path to the smallest observable operation;
2. separate power, PCB routing, MCU pin configuration, peripheral hardware,
   protocol serialization, and operator presentation;
3. add measurements or structured diagnostics at the uncertain boundary;
4. change one layer at a time and retain the evidence;
5. rerun the complete workflow after the isolated path works.

This prevented unrelated changes from being used to explain a failure and made
it possible to recombine the independently verified pieces into one passing run.

## Bring-up investigations

### USB enumeration

SWD first established that the MCU could be programmed, verified, reset, and
run from its configured clock. USB VBUS was then measured at both the connector
and PA9 divider rather than treating enumeration as one opaque software issue.
The approximately 1 V PA9 measurement isolated the fault to VBUS sensing. With
hardware sensing disabled for V1, the existing USB CDC stack enumerated and the
JSON session worked, confirming that D+/D-, the clock, descriptors, interrupts,
and host connection were otherwise functional.

### Discrete LEDs

GPIO polarity changes did not make D4/D5 illuminate. Continuity and schematic/
PCB inspection showed that their physical polarity was reversed. The tests were
disabled in a new immutable test configuration rather than claiming that a
software change could accept broken hardware.

### BMI270 presentation

The sensor communicated and changed with motion, but raw counts on a common bar
scale made the accelerometer and gyroscope appear swapped. The tester now uses
the configured sensor ranges to show acceleration in g and angular rate in
degrees per second with independent scales. This also clarified the physical
model: an accelerometer sees gravity while stationary; a gyroscope responds to
rotation and returns near zero afterward.

### BMP388 initialization and display

An immediate failure initially contained too little information. Adding an I2C
address probe and stage/reason/code events localized the problem to the Bosch
driver boundary: its required `intf_ptr` callback context was null. After that
was fixed, a two-second settling period removed startup transients and pressure
change was displayed in pascals, where a small bench-height change is visible.

### microSD protocol

The card-detect and initialization sequence advanced farther than the console
showed. Raw received-line diagnostics exposed malformed JSON. The card capacity
is a 64-bit value, but the firmware's size-optimized newlib-nano configuration
did not reliably support the `%llu` conversion. A bounded manual decimal
formatter fixed the protocol without enabling a larger C library. The full
write, read-back, checksum, and cleanup sequence then passed.

The firmware also stopped consuming a request or component transition unless
the bounded USB transmit queue had room. This backpressure rule prevents a
diagnostic event or terminal result from being silently lost.

### WS2812 RGB LED

This was the clearest example of layered debugging:

1. The LED supply measured approximately 4.87 V and its ground measured 0 V.
2. The PA1-to-DIN path had continuity through the approximately 330 ohm R24.
3. A long GPIO-high diagnostic produced 3.3 V at the data path, then returned
   to 0 V, proving the MCU pin and PCB route could be controlled.
4. The original TIM2/PWM/DMA waveform still produced no illumination. Build
   success and timing calculations alone therefore did not prove the waveform.
5. A cycle-counted GPIO implementation bypassed TIM2, PWM, DMA, and its IRQ
   while keeping the same power, route, colour bytes, and LED.
6. The LED illuminated, isolating the defect to the timer/DMA implementation
   rather than the LED, soldering, PA1 route, power, or GRB colour selection.
7. The working implementation was reduced to a permanent three-byte GRB encoder
   and a roughly 30-microsecond interrupt-masked transmission.

The exact timer/DMA defect was not measured with an oscilloscope, so no narrower
root cause is claimed. The important lesson is to measure or substitute the
waveform-generating layer before changing already verified hardware layers.

## Dirty firmware revisions

Firmware metadata appends `-dirty` when the build is configured from a working
tree containing uncommitted changes. It is not an error state and does not alter
execution. It warns that the binary cannot be reconstructed from the named Git
commit alone. The flag must remain: removing it would hide useful acceptance
evidence. A formal archived run should be produced from a clean commit and will
then report only the commit hash.

## Accepted result

The final clean v006 hardware pass is preserved as a sanitized example in
[`example-results/flightcomputer-v1-successful-run.json`](example-results/flightcomputer-v1-successful-run.json).
It passed turquoise RGB output, 178 IMU samples, 101 barometer samples, and the
automatic SD-card write/read/checksum/cleanup sequence. The device UID and local
absolute paths are redacted because the repository is public. The firmware was
built from clean commit `1642cde5f7bb`, so the report contains no `-dirty`
marker and can be reconstructed from the named source revision.

## Practices to carry forward

- Distinguish implemented, host-tested, cross-built, electrically verified,
  and physically accepted states.
- Design diagnostic events before hardware testing rather than after a silent
  failure occurs.
- Keep interrupt callbacks bounded and apply backpressure before state changes.
- Start from vendor driver examples and verify every callback context field.
- Present sensor values in physical units with realistic independent scales.
- Record both failed investigations and the final pass; they explain why the
  accepted implementation exists.
- Preserve dirty-build detection and require clean builds for formal evidence.
