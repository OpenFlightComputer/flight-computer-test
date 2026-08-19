#include "newline_framer.h"

#include <assert.h>
#include <stddef.h>
#include <stdint.h>
#include <string.h>

#define CAPTURED_LINE_COUNT 4U

typedef struct {
    uint8_t lines[CAPTURED_LINE_COUNT][NEWLINE_FRAMER_MAX_LINE_LENGTH];
    size_t lengths[CAPTURED_LINE_COUNT];
    size_t count;
} captured_lines_t;

static void capture_line(const uint8_t *line, size_t length, void *context)
{
    captured_lines_t *captured = context;

    assert(captured->count < CAPTURED_LINE_COUNT);
    if (length > 0U) {
        memcpy(captured->lines[captured->count], line, length);
    }
    captured->lengths[captured->count] = length;
    captured->count++;
}

static void test_split_and_combined_lines(void)
{
    newline_framer_t framer;
    captured_lines_t captured = {0};
    static const uint8_t first[] = "first";
    static const uint8_t second[] = " line\nsecond\r\nthird\n";

    newline_framer_initialize(&framer);
    newline_framer_consume(
        &framer,
        first,
        sizeof(first) - 1U,
        capture_line,
        &captured
    );
    assert(captured.count == 0U);

    newline_framer_consume(
        &framer,
        second,
        sizeof(second) - 1U,
        capture_line,
        &captured
    );

    assert(captured.count == 3U);
    assert(captured.lengths[0] == 10U);
    assert(memcmp(captured.lines[0], "first line", 10U) == 0);
    assert(captured.lengths[1] == 6U);
    assert(memcmp(captured.lines[1], "second", 6U) == 0);
    assert(captured.lengths[2] == 5U);
    assert(memcmp(captured.lines[2], "third", 5U) == 0);
}

static void test_maximum_length_is_accepted(void)
{
    newline_framer_t framer;
    captured_lines_t captured = {0};
    uint8_t input[NEWLINE_FRAMER_MAX_LINE_LENGTH + 1U];

    memset(input, 'x', NEWLINE_FRAMER_MAX_LINE_LENGTH);
    input[NEWLINE_FRAMER_MAX_LINE_LENGTH] = (uint8_t)'\n';

    newline_framer_initialize(&framer);
    newline_framer_consume(
        &framer,
        input,
        sizeof(input),
        capture_line,
        &captured
    );

    assert(captured.count == 1U);
    assert(captured.lengths[0] == NEWLINE_FRAMER_MAX_LINE_LENGTH);
    assert(framer.overflow_count == 0U);
}

static void test_oversized_line_is_discarded_and_recovery_is_bounded(void)
{
    newline_framer_t framer;
    captured_lines_t captured = {0};
    uint8_t oversized[NEWLINE_FRAMER_MAX_LINE_LENGTH + 2U];
    static const uint8_t recovery[] = "valid\n";

    memset(oversized, 'x', sizeof(oversized));
    oversized[sizeof(oversized) - 1U] = (uint8_t)'\n';

    newline_framer_initialize(&framer);
    newline_framer_consume(
        &framer,
        oversized,
        sizeof(oversized),
        capture_line,
        &captured
    );
    newline_framer_consume(
        &framer,
        recovery,
        sizeof(recovery) - 1U,
        capture_line,
        &captured
    );

    assert(framer.overflow_count == 1U);
    assert(captured.count == 1U);
    assert(captured.lengths[0] == 5U);
    assert(memcmp(captured.lines[0], "valid", 5U) == 0);
}

int main(void)
{
    test_split_and_combined_lines();
    test_maximum_length_is_accepted();
    test_oversized_line_is_discarded_and_recovery_is_bounded();
    return 0;
}
