cmake_minimum_required(VERSION 3.25)

# Milestone 1 intentionally enables no compiler and creates no firmware target.
# The STM32F405 toolchain, HAL sources, linker script, and build artifact arrive
# in Milestone 4 after the repository architecture has been accepted.
project(openflightcomputer_manufacturing_test_skeleton LANGUAGES NONE)

message(STATUS "Manufacturing-test firmware skeleton: no build target in Milestone 1")

