/* NUCLEO-L432KC: osciloscopio de dos canales para Milk-V Duo S.
 * SPI modo 0 mediante GPIO en el esclavo para EVITAR el fallo de rearmado de
 * HAL_SPI_TransmitReceive / DMA observado en las pruebas previas.
 *
 * Cableado SIN CAMBIOS:
 * PB3 / D13 = SCLK (entrada)
 * PB5 / D11 = MOSI (entrada)
 * PB4 / D12 = MISO (salida)
 * PA4 / A3  = CS   (entrada, activo bajo)
 * PA0 / A0  = ADC1_IN5 (CH1)
 * PA1 / A1  = ADC1_IN6 (CH2)
 * GND compartido. Solo señales de 0 a 3.3 V en A0/A1.
 *
 * Trama: 264 bytes
 *   [0]='S', [1]='C', [2]=preset (1/2/3), [3]=status,
 *   [4..5]=secuencia little-endian,
 *   [6..261]=64 pares u16 little-endian CH1,CH2,
 *   [262..263]=CRC16-CCITT-FALSE little-endian sobre bytes 0..261.
 * El maestro envía el preset en el primer byte de cada transferencia;
 * se aplica a la captura SIGUIENTE.
 */
#include "stm32l4xx_hal.h"
#include <stdint.h>
#include <string.h>

#define NSAMPLES 64u
#define FRAME_SIZE 264u
#define DATA_END 262u

#define CS_MASK GPIO_PIN_4   /* PA4 */
#define CLK_MASK GPIO_PIN_3  /* PB3 */
#define MOSI_MASK GPIO_PIN_5 /* PB5 */
#define MISO_MASK GPIO_PIN_4 /* PB4 */

static ADC_HandleTypeDef hadc1;
static TIM_HandleTypeDef htim2;
static uint8_t tx_frame[FRAME_SIZE];
static uint8_t preset = 2u;
static uint16_t sequence = 0u;
static uint8_t adc_ready = 0u;
static uint8_t adc_error = 0x10u;

static inline uint8_t cs_high(void) { return (GPIOA->IDR & CS_MASK) != 0u; }
static inline uint8_t clk_high(void) { return (GPIOB->IDR & CLK_MASK) != 0u; }
static inline uint8_t mosi_high(void) { return (GPIOB->IDR & MOSI_MASK) != 0u; }
static inline void miso_set(uint8_t v)
{
    GPIOB->BSRR = v ? (uint32_t)MISO_MASK : ((uint32_t)MISO_MASK << 16);
}

void Error_Handler(void)
{
    while (1)
    {
    }
}

void HAL_ADC_MspInit(ADC_HandleTypeDef *h)
{
    if (h->Instance != ADC1)
        return;
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
    if (h->Instance == TIM2)
        __HAL_RCC_TIM2_CLK_ENABLE();
}

static void clock_16mhz(void)
{
    RCC_OscInitTypeDef o = {0};
    RCC_ClkInitTypeDef c = {0};
    o.OscillatorType = RCC_OSCILLATORTYPE_HSI;
    o.HSIState = RCC_HSI_ON;
    o.HSICalibrationValue = RCC_HSICALIBRATION_DEFAULT;
    o.PLL.PLLState = RCC_PLL_NONE;
    if (HAL_RCC_OscConfig(&o) != HAL_OK)
        Error_Handler();
    c.ClockType = RCC_CLOCKTYPE_SYSCLK | RCC_CLOCKTYPE_HCLK |
                  RCC_CLOCKTYPE_PCLK1 | RCC_CLOCKTYPE_PCLK2;
    c.SYSCLKSource = RCC_SYSCLKSOURCE_HSI;
    c.AHBCLKDivider = RCC_SYSCLK_DIV1;
    c.APB1CLKDivider = RCC_HCLK_DIV1;
    c.APB2CLKDivider = RCC_HCLK_DIV1;
    if (HAL_RCC_ClockConfig(&c, FLASH_LATENCY_0) != HAL_OK)
        Error_Handler();
}

static void gpio_spi_slave_init(void)
{
    __HAL_RCC_GPIOA_CLK_ENABLE();
    __HAL_RCC_GPIOB_CLK_ENABLE();
    GPIO_InitTypeDef g = {0};
    /* GPIO en vez de AF5: el STM32 detecta los flancos directamente. */
    g.Pin = CLK_MASK | MOSI_MASK;
    g.Mode = GPIO_MODE_INPUT;
    g.Pull = GPIO_PULLDOWN;
    HAL_GPIO_Init(GPIOB, &g);

    g.Pin = MISO_MASK;
    g.Mode = GPIO_MODE_OUTPUT_PP;
    g.Pull = GPIO_NOPULL;
    g.Speed = GPIO_SPEED_FREQ_HIGH;
    HAL_GPIO_Init(GPIOB, &g);
    miso_set(0);

    g.Pin = CS_MASK;
    g.Mode = GPIO_MODE_INPUT;
    g.Pull = GPIO_PULLUP;
    HAL_GPIO_Init(GPIOA, &g);
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
    if (HAL_ADC_Init(&hadc1) != HAL_OK)
        return 0x10u;
    if (HAL_ADCEx_Calibration_Start(&hadc1, ADC_SINGLE_ENDED) != HAL_OK)
        return 0x11u;
    return 0;
}

static uint8_t read_adc(uint32_t channel, uint16_t *value)
{
    ADC_ChannelConfTypeDef c = {0};
    c.Channel = channel;
    c.Rank = ADC_REGULAR_RANK_1;
    c.SamplingTime = ADC_SAMPLETIME_47CYCLES_5;
    c.SingleDiff = ADC_SINGLE_ENDED;
    c.OffsetNumber = ADC_OFFSET_NONE;
    c.Offset = 0;
    if (HAL_ADC_ConfigChannel(&hadc1, &c) != HAL_OK)
        return 0x13u;
    if (HAL_ADC_Start(&hadc1) != HAL_OK)
        return 0x14u;
    if (HAL_ADC_PollForConversion(&hadc1, 5) != HAL_OK)
    {
        HAL_ADC_Stop(&hadc1);
        return 0x15u;
    }
    *value = (uint16_t)HAL_ADC_GetValue(&hadc1);
    HAL_ADC_Stop(&hadc1);
    return 0u;
}

static void put16(uint32_t offset, uint16_t value)
{
    tx_frame[offset] = (uint8_t)value;
    tx_frame[offset + 1u] = (uint8_t)(value >> 8);
}

static uint16_t crc16(const uint8_t *data, uint32_t len)
{
    uint16_t crc = 0xFFFFu;
    for (uint32_t i = 0; i < len; i++)
    {
        crc ^= (uint16_t)data[i] << 8;
        for (uint32_t b = 0; b < 8; b++)
            crc = (crc & 0x8000u) ? (uint16_t)((crc << 1) ^ 0x1021u) : (uint16_t)(crc << 1);
    }
    return crc;
}

static uint32_t rate_hz(void)
{
    return (preset == 1u) ? 100u : (preset == 3u) ? 10000u
                                                  : 1000u;
}

static void prepare_frame(void)
{
    memset(tx_frame, 0, sizeof(tx_frame));
    tx_frame[0] = 0x53;
    tx_frame[1] = 0x43;
    tx_frame[2] = preset;
    tx_frame[3] = 0u;
    sequence++;
    put16(4u, sequence);

    if (!adc_ready)
    {
        tx_frame[3] = adc_error;
        goto finish;
    }

    uint32_t period_us = 1000000u / rate_hz();
    htim2.Instance = TIM2;
    htim2.Init.Prescaler = 15; /* 16MHz / 16 = 1 MHz */
    htim2.Init.CounterMode = TIM_COUNTERMODE_UP;
    htim2.Init.Period = period_us - 1u;
    htim2.Init.ClockDivision = TIM_CLOCKDIVISION_DIV1;
    htim2.Init.AutoReloadPreload = TIM_AUTORELOAD_PRELOAD_DISABLE;
    if (HAL_TIM_Base_Init(&htim2) != HAL_OK)
    {
        tx_frame[3] = 0x12u;
        goto finish;
    }
    __HAL_TIM_SET_COUNTER(&htim2, 0);
    __HAL_TIM_CLEAR_FLAG(&htim2, TIM_FLAG_UPDATE);
    if (HAL_TIM_Base_Start(&htim2) != HAL_OK)
    {
        tx_frame[3] = 0x12u;
        goto finish;
    }
    for (uint32_t i = 0; i < NSAMPLES; i++)
    {
        uint32_t start = HAL_GetTick();
        while (__HAL_TIM_GET_FLAG(&htim2, TIM_FLAG_UPDATE) == RESET)
        {
            if ((HAL_GetTick() - start) > 100u)
            {
                tx_frame[3] = 0x16u;
                goto stop_timer;
            }
        }
        __HAL_TIM_CLEAR_FLAG(&htim2, TIM_FLAG_UPDATE);
        uint16_t a = 0, b = 0;
        uint8_t err = read_adc(ADC_CHANNEL_5, &a); /* PA0/A0 */
        if (!err)
            err = read_adc(ADC_CHANNEL_6, &b); /* PA1/A1 */
        if (err)
        {
            tx_frame[3] = err;
            goto stop_timer;
        }
        put16(6u + i * 4u, a);
        put16(8u + i * 4u, b);
        /* Señala cuando la conversión no acaba antes del siguiente tick. */
        if (i < NSAMPLES - 1u && __HAL_TIM_GET_FLAG(&htim2, TIM_FLAG_UPDATE))
        {
            tx_frame[3] = 0x17u;
            goto stop_timer;
        }
    }
stop_timer:
    HAL_TIM_Base_Stop(&htim2);
finish:
    put16(DATA_END, crc16(tx_frame, DATA_END));
}

/* Leer un bit del maestro en el flanco ascendente; se genera un bit MISO
 * antes de ese flanco. 100ms timeout por flanco para no quedar congelado.
 * Devolver 0 si CS sube o desaparece el reloj.
 */
static uint8_t wait_clock(uint8_t desired)
{
    uint32_t start = HAL_GetTick();
    while (clk_high() != desired)
    {
        if (cs_high())
            return 0;
        if ((HAL_GetTick() - start) > 100u)
            return 0;
    }
    return 1;
}

static uint8_t slave_transfer(uint8_t *command)
{
    /* La Milk-V activa CS, espera 15ms y comienza el reloj. */
    while (cs_high())
    {
    }

    uint8_t first_byte = 0u;
    for (uint32_t i = 0; i < FRAME_SIZE; i++)
    {
        uint8_t incoming = 0u;
        uint8_t outgoing = tx_frame[i];
        for (int bit = 7; bit >= 0; bit--)
        {
            if (cs_high())
                goto abort;
            if (!wait_clock(0))
                goto abort;
            miso_set((uint8_t)((outgoing >> bit) & 1u));
            if (!wait_clock(1))
                goto abort;
            incoming = (uint8_t)((incoming << 1) | mosi_high());
            if (!wait_clock(0))
                goto abort;
        }
        if (i == 0u)
            first_byte = incoming;
    }

    /* Descarga por completo y espera que CS se libere. */
    while (!cs_high())
    {
    }
    miso_set(0);
    *command = first_byte;
    return 1u;
abort:
    miso_set(0);
    while (!cs_high())
    {
    }
    return 0u;
}

int main(void)
{
    HAL_Init();
    clock_16mhz();
    gpio_spi_slave_init();
    adc_error = adc_init_safe();
    adc_ready = (adc_error == 0u);
    prepare_frame();

    while (1)
    {
        uint8_t new_preset = 0u;
        if (slave_transfer(&new_preset))
        {
            if (new_preset >= 1u && new_preset <= 3u)
                preset = new_preset;
            /* Capturamos DESPUÉS de CS alto, preparando el próximo cuadro. */
            prepare_frame();
        }
    }
}
