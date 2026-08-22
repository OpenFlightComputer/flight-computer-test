cmake_minimum_required(VERSION 3.25)

project(openflightcomputer_firmware_host_tests LANGUAGES C)

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)
set(CMAKE_C_EXTENSIONS OFF)

enable_testing()

add_executable(test_newline_framer
    test_newline_framer.c
    ../protocol/newline_framer.c
)

target_include_directories(test_newline_framer PRIVATE ../protocol)
target_compile_options(test_newline_framer PRIVATE
    -Wall
    -Wextra
    -Wpedantic
    -Werror
)

add_test(NAME newline_framer COMMAND test_newline_framer)

add_executable(test_json_protocol
    test_json_protocol.c
    ../protocol/json_protocol.c
)

target_include_directories(test_json_protocol PRIVATE
    ../application
    ../protocol
)
target_compile_options(test_json_protocol PRIVATE
    -Wall
    -Wextra
    -Wpedantic
    -Werror
)

add_test(NAME json_protocol COMMAND test_json_protocol)

add_executable(test_component_test_runner
    test_component_test_runner.c
    ../application/component_test_runner.c
)

target_include_directories(test_component_test_runner PRIVATE
    ../application
    ../components
)
target_compile_options(test_component_test_runner PRIVATE
    -Wall
    -Wextra
    -Wpedantic
    -Werror
)

add_test(NAME component_test_runner COMMAND test_component_test_runner)

add_executable(test_ws2812_encoder
    test_ws2812_encoder.c
    ../components/rgb_led/ws2812_encoder.c
)

target_include_directories(test_ws2812_encoder PRIVATE
    ../components/rgb_led
)
target_compile_options(test_ws2812_encoder PRIVATE
    -Wall
    -Wextra
    -Wpedantic
    -Werror
)

add_test(NAME ws2812_encoder COMMAND test_ws2812_encoder)
