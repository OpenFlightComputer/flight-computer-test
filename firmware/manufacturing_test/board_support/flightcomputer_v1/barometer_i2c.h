#ifndef OPENFLIGHTCOMPUTER_BAROMETER_I2C_H
#define OPENFLIGHTCOMPUTER_BAROMETER_I2C_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

bool flightcomputer_v1_barometer_i2c_read(
    uint8_t address, uint8_t register_address, uint8_t *data, size_t length
);
bool flightcomputer_v1_barometer_i2c_write(
    uint8_t address, uint8_t register_address, const uint8_t *data, size_t length
);

#endif
