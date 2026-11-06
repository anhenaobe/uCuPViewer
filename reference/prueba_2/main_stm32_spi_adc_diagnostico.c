#include "stm32l4xx_hal.h"
#include <stdint.h>
#include <string.h>

/* Protocolo actual de osc_spi.py: 4 + 64*(2 canales)*(2 bytes) = 260 B */
#define SAMPLES 64u
#define FRAME_BYTES (4u + SAMPLES * 4u)
#define ADC_INVALID 0xEEEEu

SPI_HandleTypeDef hspi1;
ADC_HandleTypeDef hadc1;
TIM_HandleTypeDef htim2;

static uint8_t tx[FRAME_BYTES];
static uint8_t rx[FRAME_BYTES];
static uint32_t sample_rate = 1000;
static uint8_t sequence_number = 0;
static uint8_t adc_status = 0;

/* Diagnostico en tx[3]: F0=trama inicial; 00=ADC OK; 10=ADC init;
   11=calibracion; 12=timer; 13=config canal; 14=start ADC;
   15=timeout ADC; 16=timeout timer. */

void Error_Handler(void) { __disable_irq(); while (1) {} }

void HAL_SPI_MspInit(SPI_HandleTypeDef *h)
{
    if (h->Instance != SPI1) return;
    __HAL_RCC_GPIOA_CLK_ENABLE();
    __HAL_RCC_GPIOB_CLK_ENABLE();
    __HAL_RCC_SPI1_CLK_ENABLE();
    GPIO_InitTypeDef g = {0};
    g.Pin = GPIO_PIN_3 | GPIO_PIN_4 | GPIO_PIN_5;
    g.Mode = GPIO_MODE_AF_PP;
    g.Pull = GPIO_NOPULL;
    g.Speed = GPIO_SPEED_FREQ_HIGH;
    g.Alternate = GPIO_AF5_SPI1;
    HAL_GPIO_Init(GPIOB, &g);
    g.Pin = GPIO_PIN_4;
    g.Pull = GPIO_PULLUP;
    HAL_GPIO_Init(GPIOA, &g);
}

void HAL_ADC_MspInit(ADC_HandleTypeDef *h)
{
    if (h->Instance != ADC1) return;
    __HAL_RCC_ADC_CLK_ENABLE();
    __HAL_RCC_GPIOA_CLK_ENABLE();
    GPIO_InitTypeDef g = {0};
    g.Pin = GPIO_PIN_0 | GPIO_PIN_1;
    g.Mode = GPIO_MODE_ANALOG_ADC_CONTROL;
    g.Pull = GPIO_NOPULL;
    HAL_GPIO_Init(GPIOA, &g);
}

void HAL_TIM_Base_MspInit(TIM_HandleTypeDef *h)
{
    if (h->Instance == TIM2) __HAL_RCC_TIM2_CLK_ENABLE();
}

static void clock_16mhz(void)
{
    RCC_OscInitTypeDef o = {0};
    RCC_ClkInitTypeDef c = {0};
    o.OscillatorType = RCC_OSCILLATORTYPE_HSI;
    o.HSIState = RCC_HSI_ON;
    o.HSICalibrationValue = RCC_HSICALIBRATION_DEFAULT;
    o.PLL.PLLState = RCC_PLL_NONE;
    if (HAL_RCC_OscConfig(&o) != HAL_OK) Error_Handler();
    c.ClockType = RCC_CLOCKTYPE_SYSCLK | RCC_CLOCKTYPE_HCLK |
                  RCC_CLOCKTYPE_PCLK1 | RCC_CLOCKTYPE_PCLK2;
    c.SYSCLKSource = RCC_SYSCLKSOURCE_HSI;
    c.AHBCLKDivider = RCC_SYSCLK_DIV1;
    c.APB1CLKDivider = RCC_HCLK_DIV1;
    c.APB2CLKDivider = RCC_HCLK_DIV1;
    if (HAL_RCC_ClockConfig(&c, FLASH_LATENCY_0) != HAL_OK) Error_Handler();
}

static void spi_init(void)
{
    hspi1.Instance = SPI1;
    hspi1.Init.Mode = SPI_MODE_SLAVE;
    hspi1.Init.Direction = SPI_DIRECTION_2LINES;
    hspi1.Init.DataSize = SPI_DATASIZE_8BIT;
    hspi1.Init.CLKPolarity = SPI_POLARITY_LOW;
    hspi1.Init.CLKPhase = SPI_PHASE_1EDGE;
    hspi1.Init.NSS = SPI_NSS_HARD_INPUT;
    hspi1.Init.FirstBit = SPI_FIRSTBIT_MSB;
    hspi1.Init.TIMode = SPI_TIMODE_DISABLE;
    hspi1.Init.CRCCalculation = SPI_CRCCALCULATION_DISABLE;
    hspi1.Init.CRCPolynomial = 7;
    if (HAL_SPI_Init(&hspi1) != HAL_OK) Error_Handler();
}

static uint8_t adc_init_safe(void)
{
    hadc1.Instance = ADC1;
    hadc1.Init.ClockPrescaler = ADC_CLOCK_SYNC_PCLK_DIV2;
    hadc1.Init.Resolution = ADC_RESOLUTION_12B;
    hadc1.Init.DataAlign = ADC_DATAALIGN_RIGHT;
    hadc1.Init.ScanConvMode = ADC_SCAN_DISABLE;
    hadc1.Init.EOCSelection = ADC_EOC_SINGLE_CONV;
    hadc1.Init.LowPowerAutoWait = DISABLE;
    hadc1.Init.ContinuousConvMode = DISABLE;
    hadc1.Init.NbrOfConversion = 1;
    hadc1.Init.DiscontinuousConvMode = DISABLE;
    hadc1.Init.ExternalTrigConv = ADC_SOFTWARE_START;
    hadc1.Init.ExternalTrigConvEdge = ADC_EXTERNALTRIGCONVEDGE_NONE;
    hadc1.Init.DMAContinuousRequests = DISABLE;
    hadc1.Init.Overrun = ADC_OVR_DATA_OVERWRITTEN;
    hadc1.Init.OversamplingMode = DISABLE;
    if (HAL_ADC_Init(&hadc1) != HAL_OK) return 0x10;
    if (HAL_ADCEx_Calibration_Start(&hadc1, ADC_SINGLE_ENDED) != HAL_OK) return 0x11;
    return 0;
}

static uint8_t read_adc(uint32_t channel, uint16_t *result)
{
    ADC_ChannelConfTypeDef c = {0};
    c.Channel = channel;
    c.Rank = ADC_REGULAR_RANK_1;
    c.SamplingTime = ADC_SAMPLETIME_47CYCLES_5;
    c.SingleDiff = ADC_SINGLE_ENDED;
    c.OffsetNumber = ADC_OFFSET_NONE;
    c.Offset = 0;
    if (HAL_ADC_ConfigChannel(&hadc1, &c) != HAL_OK) return 0x13;
    if (HAL_ADC_Start(&hadc1) != HAL_OK) return 0x14;
    if (HAL_ADC_PollForConversion(&hadc1, 10) != HAL_OK) {
        HAL_ADC_Stop(&hadc1);
        return 0x15;
    }
    *result = (uint16_t)HAL_ADC_GetValue(&hadc1);
    HAL_ADC_Stop(&hadc1);
    return 0;
}

static void put_u16(uint8_t *p, uint16_t x)
{
    p[0] = (uint8_t)(x & 0xffu);
    p[1] = (uint8_t)(x >> 8);
}

static void prepare_frame(uint8_t code)
{
    memset(tx, 0, sizeof(tx));
    tx[0] = 0x53;
    tx[1] = 0x43;
    tx[2] = (sample_rate == 100) ? 1 : (sample_rate == 1000) ? 2 : 3;
    tx[3] = code;
    for (uint32_t i = 0; i < SAMPLES; ++i) {
        put_u16(tx + 4 + 4*i, ADC_INVALID);
        put_u16(tx + 6 + 4*i, ADC_INVALID);
    }
}

static uint8_t capture(void)
{
    prepare_frame(0);
    if (adc_status) return adc_status;

    const uint32_t period_us = 1000000u / sample_rate;
    htim2.Instance = TIM2;
    htim2.Init.Prescaler = 15;
    htim2.Init.CounterMode = TIM_COUNTERMODE_UP;
    htim2.Init.Period = period_us - 1;
    htim2.Init.ClockDivision = TIM_CLOCKDIVISION_DIV1;
    htim2.Init.AutoReloadPreload = TIM_AUTORELOAD_PRELOAD_DISABLE;
    if (HAL_TIM_Base_Init(&htim2) != HAL_OK) return 0x12;
    __HAL_TIM_SET_COUNTER(&htim2, 0);
    __HAL_TIM_CLEAR_FLAG(&htim2, TIM_FLAG_UPDATE);
    if (HAL_TIM_Base_Start(&htim2) != HAL_OK) return 0x12;

    uint8_t error = 0;
    for (uint32_t i = 0; i < SAMPLES; ++i) {
        uint32_t start_ms = HAL_GetTick();
        while (__HAL_TIM_GET_FLAG(&htim2, TIM_FLAG_UPDATE) == RESET) {
            if ((HAL_GetTick() - start_ms) > 100u) { error = 0x16; goto finish; }
        }
        __HAL_TIM_CLEAR_FLAG(&htim2, TIM_FLAG_UPDATE);
        uint16_t a = ADC_INVALID, b = ADC_INVALID;
        error = read_adc(ADC_CHANNEL_5, &a);  /* PA0 */
        if (error) goto finish;
        error = read_adc(ADC_CHANNEL_6, &b);  /* PA1 */
        if (error) goto finish;
        put_u16(tx + 4 + 4*i, a);
        put_u16(tx + 6 + 4*i, b);
    }
finish:
    HAL_TIM_Base_Stop(&htim2);
    return error;
}

int main(void)
{
    HAL_Init();
    clock_16mhz();
    spi_init();

    /* Primera trama: prueba SPI conocida, ANTES de inicializar el ADC. */
    prepare_frame(0xF0);
    adc_status = 0;
    uint8_t initialized = 0;
    while (1) {
        memset(rx, 0, sizeof(rx));
        HAL_StatusTypeDef result = HAL_SPI_TransmitReceive(
            &hspi1, tx, rx, FRAME_BYTES, HAL_MAX_DELAY);
        if (result != HAL_OK) {
            HAL_SPI_Abort(&hspi1);
            continue;
        }
        if (rx[0] == 1) sample_rate = 100;
        else if (rx[0] == 2) sample_rate = 1000;
        else if (rx[0] == 3) sample_rate = 10000;

        if (!initialized) {
            adc_status = adc_init_safe();
            initialized = 1;
        }
        uint8_t code = capture();
        if (code != 0) tx[3] = code;
    }
}
