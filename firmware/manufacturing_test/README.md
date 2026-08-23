# Manufacturing-test firmware

This bare-metal firmware is installed temporarily through ST-Link/SWD to exercise Flight Computer V1 hardware under computer-side control. It is not operational flight-control firmware.

The firmware currently provides the STM32F405 foundation plus the firmware half of Milestone 6: USB OTG FS device support, CDC ACM enumeration, interrupt-driven packet transfer, bounded queues, and newline framing. It does not yet interpret protocol messages or execute component tests.

## Architecture

The dependency direction remains:

```text
protocol
   ↓
application
   ↓
components
   ↓
hardware_abstraction and drivers
   ↓
board_support and STM32 HAL
```

`application_state` becomes `APPLICATION_STATE_READY` after successful clock setup, and `application_loop_iterations` increments continuously. These variables provide a non-invasive debugger check once hardware is available; the foundation deliberately does not use LEDs as a heartbeat.

## Versioned inputs

| Input | Selected version |
| --- | --- |
| Manufacturing firmware | `0.1.0` from the CMake project version |
| STM32CubeF4 | `v1.28.3`, submodule commit `94cae6e83f00e276a11957e7833c01ac3d0bd7af` |
| Bosch BMI270 SensorAPI | `v2.113.0`, submodule commit `41129fcfe39c583ee5462d79195741945d51c1fe` |
| Bosch BMP3 SensorAPI | `v2.0.6`, submodule commit `db4cf8e4140c593b8c3d85f8c6c07335c7ffa9dc` |
| CMSIS STM32F4 device package | commit `3c77349ce04c8af401454cc51f85ea9a50e34fc1` |
| STM32F4 HAL driver | commit `b6f0ed3829f3829eb358a2e7417d80bba1a42db7` |
| Arm GNU Toolchain | `15.3.rel1` (`arm-none-eabi-gcc` 15.3.1) |
| CMake | minimum 3.25; tested with 4.4.2 |
| Ninja | tested with 1.13.2 |

The firmware image embeds the firmware version, Git revision, STM32CubeF4 version, and compiler version in `.firmware_metadata`. Builds from modified source append `-dirty` to the Git revision; no build timestamp is embedded.

## Set up dependencies

On macOS, install the build coordinator and executor:

```bash
brew install cmake ninja
```

Install Arm's complete `gcc-arm-embedded` distribution, not Homebrew's compiler-only `arm-none-eabi-gcc` formula. The complete distribution includes newlib and the bare-metal runtime. The toolchain file searches `PATH`, Arm's standard application location, and this machine's user-local fallback at:

```text
~/.local/share/OpenFlightComputer/arm-gnu-toolchain-15.3.rel1
```

After cloning the repository, initialize the pinned STM32CubeF4 package and only its two required nested dependencies:

```bash
git submodule update --init firmware/manufacturing_test/third_party/STM32CubeF4
git submodule update --init firmware/manufacturing_test/third_party/BMI270_SensorAPI
git submodule update --init firmware/manufacturing_test/third_party/BMP3_SensorAPI
git -C firmware/manufacturing_test/third_party/STM32CubeF4 submodule update --init Drivers/CMSIS/Device/ST/STM32F4xx Drivers/STM32F4xx_HAL_Driver
```

CMake stops with a direct missing-dependency error if these files are absent.

## Build

From the repository root, the board-tester wrapper configures and builds the same CMake presets:

```bash
./fc-test firmware build
./fc-test firmware build --profile debug
```

The wrapper does not duplicate compiler, source, or linker configuration. It invokes CMake and confirms that the expected ELF was produced.

From this directory, configure and build Debug firmware:

```bash
cmake --preset firmware-debug
cmake --build --preset firmware-debug
```

For Release firmware:

```bash
cmake --preset firmware-release
cmake --build --preset firmware-release
```

Each build directory contains:

```text
openflightcomputer-manufacturing-test.elf
openflightcomputer-manufacturing-test.hex
openflightcomputer-manufacturing-test.bin
openflightcomputer-manufacturing-test.map
compile_commands.json
```

The ELF contains debug/symbol information, HEX and BIN are flashable representations, the map explains linked memory placement, and `compile_commands.json` supplies IDE indexing.

## USB development identity

The default `0xCAFE:0x4001` VID/PID pair is an unassigned development placeholder. It is deliberately centralized in CMake, clearly reported during configuration, and must not be used for distributed hardware. Override the values when an assigned identity is available:

```bash
cmake --preset firmware-debug \
  -DOPENFLIGHTCOMPUTER_USB_VID=0x1234 \
  -DOPENFLIGHTCOMPUTER_USB_PID=0x0001 \
  -DOPENFLIGHTCOMPUTER_USB_IDS_ARE_DEVELOPMENT=OFF
```

The device advertises `OpenFlightComputer Manufacturing Test` as a Full-Speed CDC ACM device. Its serial-number descriptor is intentionally absent until Milestone 7 introduces the STM32 factory UID as session identity. The configuration declares a bus-powered maximum of 500 mA.

## USB transport

PA11 and PA12 are configured as OTG FS D− and D+ on alternate function 10. PA9 provides VBUS sensing. USB interrupts run at NVIC priority 6 and enter the ST PCD and USB Device stacks; interrupt callbacks only move bytes and update completion state.

The application loop performs the slower work:

- received USB packets enter a 512-byte single-producer/single-consumer ring;
- complete LF-terminated lines are assembled outside interrupt context;
- CRLF is accepted by removing a trailing CR;
- lines may contain at most 4,096 bytes;
- oversized or receive-overflowed lines are discarded through the next newline;
- two complete received lines and two outgoing lines can be queued;
- outgoing lines gain exactly one LF terminator and remain stored until the asynchronous USB transfer completes.

The protocol layer exposes complete lines but does not parse JSON or respond to commands yet.

Run the hardware-independent framing tests with the computer's native C compiler:

```bash
cmake -S tests -B build/host-tests -G Ninja
cmake --build build/host-tests
ctest --test-dir build/host-tests --output-on-failure
```

## Clock tree

The board's 16 MHz crystal is used as the HSE source:

```text
16 MHz ÷ PLLM 16 × PLLN 336 ÷ PLLP 2 = 168 MHz SYSCLK
336 MHz ÷ PLLQ 7 = 48 MHz USB clock
```

AHB runs at 168 MHz, APB1 at 42 MHz, and APB2 at 84 MHz. Flash latency is five wait states for the 3.3 V board supply. Failure to start HSE or reach 168 MHz enters `APPLICATION_STATE_CLOCK_ERROR`; the manufacturing firmware does not silently fall back to HSI because that would conceal an oscillator fault.

## Hardware validation status

Debug and Release images compile, link, and produce all artifacts without hardware. The vector table, reset entry, memory regions, metadata, and unresolved-symbol set have been inspected. Actual HSE startup, USB enumeration and transfer, stable loop execution, and SWD programming remain unverified until a board is available.
