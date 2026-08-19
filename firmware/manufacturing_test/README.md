# Manufacturing-test firmware

This firmware is installed temporarily through ST-Link/SWD to exercise board hardware under computer-side control. It is not operational flight-control firmware.

The dependency direction is:

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

Milestone 1 contains architecture documentation only. The CMake project deliberately enables no compiler and produces no binary.

