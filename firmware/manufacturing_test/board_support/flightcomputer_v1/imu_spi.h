#ifndef OPENFLIGHTCOMPUTER_IMU_SPI_H
#define OPENFLIGHTCOMPUTER_IMU_SPI_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

bool flightcomputer_v1_imu_spi_transfer(
    const uint8_t *transmit,
    uint8_t *receive,
    size_t length
);
void flightcomputer_v1_delay_us(uint32_t microseconds);

#endif
