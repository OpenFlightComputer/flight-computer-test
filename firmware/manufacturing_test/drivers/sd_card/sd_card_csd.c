#include "sd_card_csd.h"

#include <stddef.h>

#define SD_BLOCK_SIZE 512U

bool sd_card_parse_csd(const uint8_t csd[16], uint64_t *sector_count)
{
    if (csd == NULL || sector_count == NULL) {
        return false;
    }

    const uint8_t structure = csd[0] >> 6U;
    if (structure == 1U) {
        /* CSD v2: capacity = (C_SIZE + 1) x 1024 sectors. */
        const uint32_t c_size =
            ((uint32_t)(csd[7] & 0x3FU) << 16U) |
            ((uint32_t)csd[8] << 8U) |
            csd[9];
        *sector_count = (uint64_t)(c_size + 1U) * 1024U;
        return true;
    }
    if (structure == 0U) {
        /* CSD v1: capacity uses C_SIZE, C_SIZE_MULT, and READ_BL_LEN. */
        const uint32_t c_size =
            ((uint32_t)(csd[6] & 0x03U) << 10U) |
            ((uint32_t)csd[7] << 2U) |
            (csd[8] >> 6U);
        const uint32_t c_mult =
            ((uint32_t)(csd[9] & 0x03U) << 1U) |
            (csd[10] >> 7U);
        const uint32_t read_length = csd[5] & 0x0FU;
        *sector_count = ((uint64_t)(c_size + 1U) <<
            (c_mult + 2U + read_length)) / SD_BLOCK_SIZE;
        return true;
    }

    /* Structures 2 and 3 belong to card classes unsupported by this driver. */
    return false;
}
