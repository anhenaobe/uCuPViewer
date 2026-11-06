#include "stm32l4xx_hal.h"

/* The framework startup only supplies a weak default SysTick vector. */
void SysTick_Handler(void)
{
    HAL_IncTick();
}
