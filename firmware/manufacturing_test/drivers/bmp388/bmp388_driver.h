#ifndef OPENFLIGHTCOMPUTER_BMP388_DRIVER_H
#define OPENFLIGHTCOMPUTER_BMP388_DRIVER_H

#include <stdbool.h>
#include <stdint.h>

typedef struct {
    /* Bosch integer compensation: both values retain two decimal places. */
    int32_t pressure_centi_pa;
    int32_t temperature_centi_c;
} bmp388_sample_t;

bool bmp388_driver_initialize(void);
bool bmp388_driver_read_sample(bmp388_sample_t *sample);
void bmp388_driver_shutdown(void);

#endif
