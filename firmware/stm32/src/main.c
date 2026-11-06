#include "stm32l4xx_hal.h"
#include "acquisition.h"
#ifdef ACQUISITION_TARGET_TEST
#include "../test/target_test.c"
volatile int acquisition_test_result = -1;
#endif
/* Framework supplies startup and SystemInit, but only a weak SysTick vector. */
void SysTick_Handler(void) { HAL_IncTick(); }
static void fail(void) { __disable_irq(); for (;;) {} }
static void clock_init(void) {
    RCC_OscInitTypeDef osc = {0};
    RCC_ClkInitTypeDef clocks = {0};
    __HAL_RCC_PWR_CLK_ENABLE();
    if (HAL_PWREx_ControlVoltageScaling(PWR_REGULATOR_VOLTAGE_SCALE1) != HAL_OK) fail();
    osc.OscillatorType = RCC_OSCILLATORTYPE_HSI;
    osc.HSIState = RCC_HSI_ON;
    osc.HSICalibrationValue = RCC_HSICALIBRATION_DEFAULT;
    osc.PLL.PLLState = RCC_PLL_NONE;
    if (HAL_RCC_OscConfig(&osc) != HAL_OK) fail();
    clocks.ClockType = RCC_CLOCKTYPE_SYSCLK | RCC_CLOCKTYPE_HCLK | RCC_CLOCKTYPE_PCLK1 | RCC_CLOCKTYPE_PCLK2;
    clocks.SYSCLKSource = RCC_SYSCLKSOURCE_HSI;
    clocks.AHBCLKDivider = RCC_SYSCLK_DIV1;
    clocks.APB1CLKDivider = RCC_HCLK_DIV1;
    clocks.APB2CLKDivider = RCC_HCLK_DIV1;
    if (HAL_RCC_ClockConfig(&clocks, FLASH_LATENCY_0) != HAL_OK) fail();
}
int main(void) {
    HAL_Init();
    clock_init();
    __HAL_RCC_GPIOB_CLK_ENABLE();
    GPIO_InitTypeDef led = {0};
    led.Pin = GPIO_PIN_3;
    led.Mode = GPIO_MODE_OUTPUT_PP;
    HAL_GPIO_Init(GPIOB, &led);
    if (!acquisition_init()) fail();
#ifdef ACQUISITION_TARGET_TEST
    acquisition_test_result = acquisition_target_test();
    if (acquisition_test_result != 0) fail();
#endif
    if (!acquisition_start()) fail();
    for (;;) {
        acquisition_poll();
        HAL_GPIO_WritePin(GPIOB, GPIO_PIN_3,
            acquisition_get_status() == ACQ_READY ? GPIO_PIN_SET : GPIO_PIN_RESET);
        /* Hold the first window for debugger inspection; no automatic release. */
    }
}
