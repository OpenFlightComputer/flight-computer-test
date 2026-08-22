#ifndef OPENFLIGHTCOMPUTER_COMPONENT_REGISTRY_H
#define OPENFLIGHTCOMPUTER_COMPONENT_REGISTRY_H

#include <stddef.h>
#include <stdbool.h>
#include <stdint.h>

#define COMPONENT_TEST_TYPE_CAPACITY 32U

typedef enum {
    COMPONENT_TEST_PROCESS_RUNNING = 0,
    COMPONENT_TEST_PROCESS_EVENT = 1,
    COMPONENT_TEST_PROCESS_PASSED = 2,
    COMPONENT_TEST_PROCESS_FAILED = 3,
} component_test_process_result_t;

typedef struct {
    bool rgb_colour_present;
    uint8_t red;
    uint8_t green;
    uint8_t blue;
} component_test_parameters_t;

typedef struct {
    const char *type;
    void (*start)(const component_test_parameters_t *parameters);
    component_test_process_result_t (*process)(void);
    const char *(*event)(void);
    void (*stop)(void);
} component_test_definition_t;

typedef struct {
    const component_test_definition_t *definitions;
    size_t count;
} component_test_registry_t;

const component_test_registry_t *component_registry_get(void);
const component_test_definition_t *component_registry_find(
    const component_test_registry_t *registry,
    const char *type
);
const char *component_registry_capability_at(size_t index);
size_t component_registry_capability_count(void);

#endif
