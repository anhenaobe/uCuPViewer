/*
 * NUCLEO-L432KC - Captura real de dos canales por USART2 / ST-LINK VCP.
 * SALIDA DIRECTA AL PC, sin Milk-V ni SPI. Es un rescate para validar ADC,
 * adquisicion y dashboard. No satisface el requisito SPI SBC-MCU.
 *
 * A0 = PA0 ADC1_IN5; A1 = PA1 ADC1_IN6 (0 a 3.3 V solamente).
 * VCP integrado: USART2_TX PA2 AF7, USART2_RX PA15 AF3, 115200 8N1.
 *
 * Protocolo ASCII cada ~2s:
 *   SC,seq,preset,status,adc1[0],adc2[0],...,adc1[63],adc2[63],CRC\n
 * CRC16-CCITT FALSE (poly 0x1021, init 0xFFFF) sobre el texto previo
 * a la ultima coma (sin incluir el CRC ni el salto de linea).
 * Presets seleccionables desde PC: P1\n P2\n P3\n.
 *
 * Presets son tasas nominales; se detecta sobremarcha entre ticks.
 * 10 kSa/s NO se garantiza con ADC consultado por HAL.
 */
#include "stm32l4xx_hal.h"
#include <stdint.h>
#include <stdio.h>
#include <string.h>

#define NSAMPLES 64u
#define UART_BAUD 115200u

static ADC_HandleTypeDef hadc1;
static TIM_HandleTypeDef htim2;
static UART_HandleTypeDef huart2;
static uint16_t samples[NSAMPLES][2];
static uint16_t seq_num = 0;
static uint8_t preset = 2;
static uint8_t adc_init_status = 0;

void Error_Handler(void) { while (1) { } }

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

void HAL_UART_MspInit(UART_HandleTypeDef *h)
{
    if (h->Instance != USART2) return;
    __HAL_RCC_GPIOA_CLK_ENABLE();
    __HAL_RCC_USART2_CLK_ENABLE();
    GPIO_InitTypeDef g = {0};
    g.Pin = GPIO_PIN_2;               /* PA2 -> ST-LINK virtual COM RX */
    g.Mode = GPIO_MODE_AF_PP;
    g.Pull = GPIO_PULLUP;
    g.Speed = GPIO_SPEED_FREQ_HIGH;
    g.Alternate = GPIO_AF7_USART2;
    HAL_GPIO_Init(GPIOA, &g);
    g.Pin = GPIO_PIN_15;              /* PA15 <- ST-LINK virtual COM TX */
    g.Alternate = GPIO_AF3_USART2;
    HAL_GPIO_Init(GPIOA, &g);
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

static void uart_init(void)
{
    huart2.Instance = USART2;
    huart2.Init.BaudRate = UART_BAUD;
    huart2.Init.WordLength = UART_WORDLENGTH_8B;
    huart2.Init.StopBits = UART_STOPBITS_1;
    huart2.Init.Parity = UART_PARITY_NONE;
    huart2.Init.Mode = UART_MODE_TX_RX;
    huart2.Init.HwFlowCtl = UART_HWCONTROL_NONE;
    huart2.Init.OverSampling = UART_OVERSAMPLING_16;
    huart2.Init.OneBitSampling = UART_ONE_BIT_SAMPLE_DISABLE;
    huart2.AdvancedInit.AdvFeatureInit = UART_ADVFEATURE_NO_INIT;
    if (HAL_UART_Init(&huart2) != HAL_OK) Error_Handler();
    {
        static const uint8_t banner[] = "SCOPE_BOOT,L432KC,STLINK_VCP\r\n";
        HAL_UART_Transmit(&huart2, (uint8_t *)banner, sizeof(banner)-1, 1000);
    }
}

static uint8_t adc_init(void)
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
    if (HAL_ADC_Init(&hadc1) != HAL_OK) return 10;
    if (HAL_ADCEx_Calibration_Start(&hadc1, ADC_SINGLE_ENDED) != HAL_OK) return 11;
    return 0;
}

static uint8_t one_adc(uint32_t channel, uint16_t *result)
{
    ADC_ChannelConfTypeDef c = {0};
    c.Channel = channel;
    c.Rank = ADC_REGULAR_RANK_1;
    c.SamplingTime = ADC_SAMPLETIME_47CYCLES_5;
    c.SingleDiff = ADC_SINGLE_ENDED;
    c.OffsetNumber = ADC_OFFSET_NONE;
    c.Offset = 0;
    if (HAL_ADC_ConfigChannel(&hadc1, &c) != HAL_OK) return 13;
    if (HAL_ADC_Start(&hadc1) != HAL_OK) return 14;
    if (HAL_ADC_PollForConversion(&hadc1, 5) != HAL_OK) {
        HAL_ADC_Stop(&hadc1);
        return 15;
    }
    *result = (uint16_t)HAL_ADC_GetValue(&hadc1);
    if (HAL_ADC_Stop(&hadc1) != HAL_OK) return 16;
    return 0;
}

static uint32_t rate_hz(void)
{
    return preset == 1 ? 100u : preset == 3 ? 10000u : 1000u;
}

static uint8_t acquire(void)
{
    if (adc_init_status) return adc_init_status;
    const uint32_t period_us = 1000000u / rate_hz();
    htim2.Instance = TIM2;
    htim2.Init.Prescaler = 15u;
    htim2.Init.CounterMode = TIM_COUNTERMODE_UP;
    htim2.Init.Period = period_us - 1u;
    htim2.Init.ClockDivision = TIM_CLOCKDIVISION_DIV1;
    htim2.Init.AutoReloadPreload = TIM_AUTORELOAD_PRELOAD_DISABLE;
    if (HAL_TIM_Base_Init(&htim2) != HAL_OK) return 12;
    __HAL_TIM_SET_COUNTER(&htim2, 0);
    __HAL_TIM_CLEAR_FLAG(&htim2, TIM_FLAG_UPDATE);
    if (HAL_TIM_Base_Start(&htim2) != HAL_OK) return 12;
    uint8_t status = 0;
    for (unsigned i=0; i<NSAMPLES; ++i) {
        uint32_t started = HAL_GetTick();
        while (__HAL_TIM_GET_FLAG(&htim2, TIM_FLAG_UPDATE) == RESET) {
            if (HAL_GetTick() - started > 100) { status = 18; goto finish; }
        }
        __HAL_TIM_CLEAR_FLAG(&htim2, TIM_FLAG_UPDATE);
        status = one_adc(ADC_CHANNEL_5, &samples[i][0]);
        if (!status) status = one_adc(ADC_CHANNEL_6, &samples[i][1]);
        if (status) goto finish;
        if (i < NSAMPLES-1u && __HAL_TIM_GET_FLAG(&htim2, TIM_FLAG_UPDATE)) {
            status = 17;              /* ADC+HAL demasiado lentos para preset */
            goto finish;
        }
    }
finish:
    HAL_TIM_Base_Stop(&htim2);
    return status;
}

static uint16_t crc16(const uint8_t *data, uint32_t len)
{
    uint16_t crc = 0xFFFFu;
    for (uint32_t i=0; i<len; ++i) {
        crc ^= (uint16_t)data[i] << 8;
        for (unsigned j=0; j<8; ++j)
            crc = (crc & 0x8000u) ? (uint16_t)((crc << 1) ^ 0x1021u) : (uint16_t)(crc << 1);
    }
    return crc;
}

static void send_capture(uint8_t status)
{
    /* 4 metadatos + 128 lecturas, 1200 bytes bastan ampliamente. */
    char line[1200];
    int len = snprintf(line, sizeof(line), "SC,%u,%u,%u",
                       (unsigned)seq_num++, (unsigned)preset, (unsigned)status);
    if (len < 0 || len >= (int)sizeof(line)-12) return;
    for (unsigned i=0; i<NSAMPLES; ++i) {
        int n = snprintf(line + len, sizeof(line) - (size_t)len,
                         ",%u,%u", (unsigned)samples[i][0], (unsigned)samples[i][1]);
        if (n <= 0 || n >= (int)sizeof(line) - len - 8) return;
        len += n;
    }
    uint16_t crc = crc16((const uint8_t *)line, (uint32_t)len);
    int n = snprintf(line+len, sizeof(line)-(size_t)len, ",%04X\n", crc);
    if (n <= 0 || (size_t)(len+n)>sizeof(line)) return;
    HAL_UART_Transmit(&huart2,(uint8_t *)line,(uint16_t)(len+n),2000);
}

static void poll_command(void)
{
    uint8_t c;
    static uint8_t command_waiting = 0;
    /* Timeout breve: permitir que llegue el byte siguiente del comando P1/P2/P3. */
    while (HAL_UART_Receive(&huart2,&c,1,1) == HAL_OK) {
        if (c=='P') command_waiting=1;
        else if (command_waiting && c>='1' && c<='3') {
            preset=(uint8_t)(c-'0');
            command_waiting=0;
        } else if (c=='\r' || c=='\n') { command_waiting=0; }
        else command_waiting=0;
    }
}

int main(void)
{
    HAL_Init();
    clock_16mhz();
    uart_init();
    adc_init_status = adc_init();
    memset(samples,0,sizeof(samples));
    uint32_t last = HAL_GetTick() - 4000u;
    while (1) {
        poll_command();
        if (HAL_GetTick() - last >= 4000u) {
            last = HAL_GetTick();
            uint8_t status=acquire();
            send_capture(status);
        }
        HAL_Delay(10);
    }
}
