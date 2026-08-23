#ifndef OPENFLIGHTCOMPUTER_SPI_DEVICE_H
#define OPENFLIGHTCOMPUTER_SPI_DEVICE_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

typedef struct spi_device spi_device_t;

typedef struct {
    bool (*initialize)(spi_device_t *device);
    bool (*select)(spi_device_t *device);
    void (*deselect)(spi_device_t *device);
    bool (*transfer)(spi_device_t *device, const uint8_t *tx, uint8_t *rx, size_t length);
    bool (*set_prescaler)(spi_device_t *device, uint32_t prescaler);
} spi_device_operations_t;

struct spi_device {
    const spi_device_operations_t *operations;
    void *context;
};

bool spi_device_initialize(spi_device_t *device);
bool spi_device_select(spi_device_t *device);
void spi_device_deselect(spi_device_t *device);
bool spi_device_transfer(spi_device_t *device, const uint8_t *tx, uint8_t *rx, size_t length);
bool spi_device_set_prescaler(spi_device_t *device, uint32_t prescaler);

#endif
