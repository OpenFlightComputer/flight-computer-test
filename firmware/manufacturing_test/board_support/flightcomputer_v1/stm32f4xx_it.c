#include "stm32f4xx_it.h"

#include "stm32f4xx_hal.h"

extern PCD_HandleTypeDef openflightcomputer_usb_pcd;
extern void rgb_led_dma_irq_handler(void);

void NMI_Handler(void)
{
    for (;;) {
    }
}

void HardFault_Handler(void)
{
    for (;;) {
    }
}

void MemManage_Handler(void)
{
    for (;;) {
    }
}

void BusFault_Handler(void)
{
    for (;;) {
    }
}

void UsageFault_Handler(void)
{
    for (;;) {
    }
}

void SVC_Handler(void)
{
}

void DebugMon_Handler(void)
{
}

void PendSV_Handler(void)
{
}

void SysTick_Handler(void)
{
    HAL_IncTick();
}

void OTG_FS_IRQHandler(void)
{
    HAL_PCD_IRQHandler(&openflightcomputer_usb_pcd);
}

void DMA1_Stream6_IRQHandler(void)
{
    rgb_led_dma_irq_handler();
}
