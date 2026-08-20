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
