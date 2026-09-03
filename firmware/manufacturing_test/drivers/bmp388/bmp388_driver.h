#ifndef OPENFLIGHTCOMPUTER_BMP388_DRIVER_H
#define OPENFLIGHTCOMPUTER_BMP388_DRIVER_H

#include <stdbool.h>
#include <stdint.h>

typedef struct {
    /* Bosch integer compensation: both values retain two decimal places. */
    int32_t pressure_centi_pa;
    int32_t temperature_centi_c;
} bmp388_sample_t;

typedef struct {
    const char *stage;
    const char *reason;
    int32_t code;
} bmp388_failure_t;

bool bmp388_driver_initialize(void);
bool bmp388_driver_read_sample(bmp388_sample_t *sample);
void bmp388_driver_shutdown(void);
const bmp388_failure_t *bmp388_driver_last_failure(void);

#endif
