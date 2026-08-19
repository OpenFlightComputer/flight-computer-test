#include "firmware_version.h"

__attribute__((section(".firmware_metadata"), used))
const char firmware_version[] = OPENFLIGHTCOMPUTER_FIRMWARE_VERSION;

__attribute__((section(".firmware_metadata"), used))
const char firmware_git_revision[] = OPENFLIGHTCOMPUTER_FIRMWARE_GIT_REVISION;

__attribute__((section(".firmware_metadata"), used))
const char firmware_stm32cube_f4_version[] =
    OPENFLIGHTCOMPUTER_STM32CUBE_F4_VERSION;

__attribute__((section(".firmware_metadata"), used))
const char firmware_arm_gcc_version[] = OPENFLIGHTCOMPUTER_ARM_GCC_VERSION;
