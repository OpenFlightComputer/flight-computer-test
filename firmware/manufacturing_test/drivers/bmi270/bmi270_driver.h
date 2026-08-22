#ifndef OPENFLIGHTCOMPUTER_BMI270_DRIVER_H
#define OPENFLIGHTCOMPUTER_BMI270_DRIVER_H

#include <stdbool.h>
#include <stdint.h>

typedef struct {
    int16_t acceleration_x;
    int16_t acceleration_y;
    int16_t acceleration_z;
    int16_t gyroscope_x;
    int16_t gyroscope_y;
    int16_t gyroscope_z;
} bmi270_sample_t;

bool bmi270_driver_initialize(void);
bool bmi270_driver_read_sample(bmi270_sample_t *sample);
void bmi270_driver_shutdown(void);

#endif
