#include "component_registry.h"

#include <string.h>

/*
 * Production entries are deliberately added only with their real component
 * implementation.
 */
extern void status_led_red_start(void);
extern void status_led_green_start(void);
extern component_test_process_result_t status_led_process(void);
extern void status_led_stop(void);
static const component_test_definition_t production_tests[] = {
    { .type = "status_led_red", .start = status_led_red_start,
      .process = status_led_process, .event = NULL, .stop = status_led_stop },
    { .type = "status_led_green", .start = status_led_green_start,
      .process = status_led_process, .event = NULL, .stop = status_led_stop },
};
static const component_test_registry_t production_registry = {
    .definitions = production_tests,
    .count = sizeof(production_tests) / sizeof(production_tests[0]),
};

const component_test_registry_t *component_registry_get(void)
{
    return &production_registry;
}

const component_test_definition_t *component_registry_find(
    const component_test_registry_t *registry,
    const char *type
)
{
    if (registry == NULL || type == NULL) {
        return NULL;
    }
    for (size_t index = 0U; index < registry->count; index++) {
        if (strcmp(registry->definitions[index].type, type) == 0) {
            return &registry->definitions[index];
        }
    }
    return NULL;
}

const char *component_registry_capability_at(size_t index)
{
    if (index >= production_registry.count) {
        return NULL;
    }
    return production_registry.definitions[index].type;
}

size_t component_registry_capability_count(void)
{
    return production_registry.count;
}
