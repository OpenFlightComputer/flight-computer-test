#ifndef OPENFLIGHTCOMPUTER_SPI_DEVICES_H
#define OPENFLIGHTCOMPUTER_SPI_DEVICES_H

#include "spi_device.h"

#include <stdbool.h>
#include <stdint.h>

spi_device_t *flightcomputer_v1_imu_spi_device(void);
spi_device_t *flightcomputer_v1_sd_spi_device(void);
bool flightcomputer_v1_sd_card_inserted(void);
void flightcomputer_v1_delay_us(uint32_t microseconds);

#endif
