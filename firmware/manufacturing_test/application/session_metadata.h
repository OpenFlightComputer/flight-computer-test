#ifndef OPENFLIGHTCOMPUTER_SESSION_METADATA_H
#define OPENFLIGHTCOMPUTER_SESSION_METADATA_H

#include <stddef.h>

#define SESSION_METADATA_UID_HEX_LENGTH 24U

typedef struct {
    char uid[SESSION_METADATA_UID_HEX_LENGTH + 1U];
    const char *mcu_model;
    const char *board_id;
    const char *board_name;
    const char *board_revision;
    const char *firmware_version;
    const char *firmware_git_revision;
    const char *(*capability_at)(size_t index);
    size_t capability_count;
} session_metadata_t;

void session_metadata_read(session_metadata_t *metadata);

#endif
