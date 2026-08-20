#include "component_registry.h"

#include <string.h>

/*
 * Production entries are deliberately added only with their real component
 * implementation. An empty registry therefore truthfully advertises no
 * component capabilities until Milestone 10 introduces the first test.
 */
static const component_test_registry_t production_registry = {
    .definitions = NULL,
    .count = 0U,
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
