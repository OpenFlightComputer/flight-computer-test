#include "application.h"
#include "system_clock.h"
#include "usb_cdc_transport.h"

#include "stm32f4xx_hal.h"

int main(void)
{
    HAL_Init();

    if (system_clock_configure() != HAL_OK) {
        application_stop(APPLICATION_STATE_CLOCK_ERROR);
    }

    if (SystemCoreClock != SYSTEM_CLOCK_FREQUENCY_HZ) {
        application_stop(APPLICATION_STATE_CLOCK_ERROR);
    }

    if (!usb_cdc_transport_initialize()) {
        application_stop(APPLICATION_STATE_USB_ERROR);
    }

    application_run();
}
