#ifndef OPENFLIGHTCOMPUTER_SD_CARD_DRIVER_H
#define OPENFLIGHTCOMPUTER_SD_CARD_DRIVER_H

#include <stdbool.h>
#include <stdint.h>

#define SD_CARD_TEST_BLOCK_COUNT 8U

typedef struct {
    uint64_t sector_count;
    uint32_t test_sector;
    uint32_t checksum;
    bool high_capacity;
} sd_card_information_t;

typedef struct {
    const char *stage;
    const char *reason;
    int32_t code;
} sd_card_failure_t;

bool sd_card_driver_initialize(sd_card_information_t *information);
bool sd_card_driver_write_test_block(sd_card_information_t *information, uint32_t block);
bool sd_card_driver_verify_test_block(const sd_card_information_t *information, uint32_t block);
bool sd_card_driver_clear_test_block(const sd_card_information_t *information, uint32_t block);
void sd_card_driver_shutdown(void);
const sd_card_failure_t *sd_card_driver_last_failure(void);

#endif
