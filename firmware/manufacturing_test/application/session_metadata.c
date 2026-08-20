#include "session_metadata.h"

#include "board_metadata.h"
#include "firmware_metadata.h"

#include "stm32f4xx.h"

static const char hexadecimal[] = "0123456789ABCDEF";

static void append_word_as_hex(char *destination, uint32_t word)
{
    for (size_t index = 0U; index < 8U; index++) {
        const uint32_t shift = 28U - (uint32_t)(index * 4U);
        destination[index] = hexadecimal[(word >> shift) & 0xFU];
    }
}

void session_metadata_read(session_metadata_t *metadata)
{
    const uint32_t uid_words[] = {
        *(const uint32_t *)(UID_BASE),
        *(const uint32_t *)(UID_BASE + 4U),
        *(const uint32_t *)(UID_BASE + 8U),
    };

    for (size_t index = 0U; index < 3U; index++) {
        append_word_as_hex(&metadata->uid[index * 8U], uid_words[index]);
    }
    metadata->uid[SESSION_METADATA_UID_HEX_LENGTH] = '\0';
    metadata->mcu_model = OPENFLIGHTCOMPUTER_MCU_MODEL;
    metadata->board_id = OPENFLIGHTCOMPUTER_BOARD_ID;
    metadata->board_name = OPENFLIGHTCOMPUTER_BOARD_NAME;
    metadata->board_revision = OPENFLIGHTCOMPUTER_BOARD_REVISION;
    metadata->firmware_version = firmware_version;
    metadata->firmware_git_revision = firmware_git_revision;
    metadata->capabilities = NULL;
    metadata->capability_count = 0U;
}
