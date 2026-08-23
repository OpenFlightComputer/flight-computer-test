#include "spi_device.h"

bool spi_device_initialize(spi_device_t *device)
{
    return device != NULL && device->operations != NULL &&
        device->operations->initialize != NULL && device->operations->initialize(device);
}

bool spi_device_select(spi_device_t *device)
{
    return device != NULL && device->operations != NULL &&
        device->operations->select != NULL && device->operations->select(device);
}

void spi_device_deselect(spi_device_t *device)
{
    if (device != NULL && device->operations != NULL && device->operations->deselect != NULL) {
        device->operations->deselect(device);
    }
}

bool spi_device_transfer(spi_device_t *device, const uint8_t *tx, uint8_t *rx, size_t length)
{
    return device != NULL && device->operations != NULL &&
        device->operations->transfer != NULL && device->operations->transfer(device, tx, rx, length);
}

bool spi_device_set_prescaler(spi_device_t *device, uint32_t prescaler)
{
    return device != NULL && device->operations != NULL &&
        device->operations->set_prescaler != NULL &&
        device->operations->set_prescaler(device, prescaler);
}
