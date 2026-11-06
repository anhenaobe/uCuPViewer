/*
 * Osciloscopio: NUCLEO-L432KC / STM32Cube HAL / PlatformIO.
 * ADC1 (PA0/PA1) -> disparo TIM2 TRGO -> DMA1_CH1 circular.
 * SPI modo 0 ESCLAVO POR SOFTWARE con sondeo GPIO (sin EXTI):
 *  PB3=D13 SCLK, PB5=D11 MOSI, PB4=D12 MISO, PA4=A3 CS activo bajo.
 * Aplicamos el preset de MOSI byte 0 DESPUES de la transferencia.
 * Trama 264 bytes: 'S','C',preset,status,seqLE16,64*(adc0LE16,adc1LE16),CRC-16/CCITT-FALSE LE16.
 * status 0 OK, 0x20 no hay muestras todavía, 0x10.. errores ADC/timer.
 * IMPORTANTE: SPI bitbang no satisface las tasas altas propias del SPI hardware.
 */
#include "stm32l4xx_hal.h"
#include <stdint.h>
#include <string.h>

#define SAMPLES 64u
#define FRAME 264u
#define PA_CS GPIO_PIN_4
#define PB_CLK GPIO_PIN_3
#define PB_MOSI GPIO_PIN_5
#define PB_MISO GPIO_PIN_4

static volatile uint8_t dma_setup_error = 0;
static ADC_HandleTypeDef hadc1;
static DMA_HandleTypeDef hdma_adc1;
static TIM_HandleTypeDef htim2;
static volatile uint16_t adc_dma[SAMPLES * 2];
static volatile uint16_t completed_adc[SAMPLES * 2];
static volatile uint16_t completed_seq = 0;
static volatile uint8_t status_code = 0x20;
static volatile uint8_t current_preset = 2;

static uint8_t work_frame[FRAME];
static uint8_t public_frame[FRAME];
static volatile uint8_t requested_preset = 0;

void Error_Handler(void)
{
    __disable_irq();
    for (;;)
    {
        __NOP();
    }
}

static inline void miso_write(uint32_t bit)
{
    GPIOB->BSRR = bit ? (uint32_t)PB_MISO : ((uint32_t)PB_MISO << 16);
}
static inline uint32_t cs_is_low(void) { return (GPIOA->IDR & PA_CS) == 0u; }
static inline uint32_t clk_is_high(void) { return (GPIOB->IDR & PB_CLK) != 0u; }
static uint16_t crc16(const uint8_t *p, uint32_t n)
{
    uint16_t crc = 0xFFFFu;
    for (uint32_t i = 0; i < n; i++)
    {
        crc ^= (uint16_t)p[i] << 8;
        for (uint32_t k = 0; k < 8; k++)
            crc = (crc & 0x8000u) ? (uint16_t)((crc << 1) ^ 0x1021u) : (uint16_t)(crc << 1);
    }
    return crc;
}
static void put16(uint8_t *p, uint32_t offset, uint16_t v)
{
    p[offset] = (uint8_t)v;
    p[offset + 1] = (uint8_t)(v >> 8);
}

static uint32_t rate_for(uint8_t p) { return p == 1u ? 100u : p == 3u ? 10000u
                                                                      : 1000u; }

/* Configuración inicial HSI 16 MHz, prescaler TIM2=15 -> tick de 1 us. */
static void clock_init(void)
{
    RCC_OscInitTypeDef osc = {0};
    RCC_ClkInitTypeDef clk = {0};
    osc.OscillatorType = RCC_OSCILLATORTYPE_HSI;
    osc.HSIState = RCC_HSI_ON;
    osc.HSICalibrationValue = RCC_HSICALIBRATION_DEFAULT;
    osc.PLL.PLLState = RCC_PLL_NONE;
    if (HAL_RCC_OscConfig(&osc) != HAL_OK)
        Error_Handler();
    clk.ClockType = RCC_CLOCKTYPE_SYSCLK | RCC_CLOCKTYPE_HCLK | RCC_CLOCKTYPE_PCLK1 | RCC_CLOCKTYPE_PCLK2;
    clk.SYSCLKSource = RCC_SYSCLKSOURCE_HSI;
    clk.AHBCLKDivider = RCC_SYSCLK_DIV1;
    clk.APB1CLKDivider = RCC_HCLK_DIV1;
    clk.APB2CLKDivider = RCC_HCLK_DIV1;
    if (HAL_RCC_ClockConfig(&clk, FLASH_LATENCY_0) != HAL_OK)
        Error_Handler();
}

/* SPI esclavo modo 0 POR SONDEO. Sin EXTI ni SPI1 ni DMA-SPI.
 * El maestro Milk-V mantiene CS bajo, y ofrece ~200 us por semiperiodo
 * mas la latencia de sysfs. STM32 lee SCK en primer plano.
 * Una interrupcion ADC-DMA puede preemptar el sondeo brevemente.
 */
static void spi_gpio_init(void)
{
    __HAL_RCC_GPIOA_CLK_ENABLE();
    __HAL_RCC_GPIOB_CLK_ENABLE();
    GPIO_InitTypeDef g = {0};
    g.Pin = PB_MOSI | PB_CLK;
    g.Mode = GPIO_MODE_INPUT;
    g.Pull = GPIO_PULLDOWN;
    HAL_GPIO_Init(GPIOB, &g);
    g.Pin = PB_MISO;
    g.Mode = GPIO_MODE_OUTPUT_PP;
    g.Pull = GPIO_NOPULL;
    g.Speed = GPIO_SPEED_FREQ_HIGH;
    HAL_GPIO_Init(GPIOB, &g);
    miso_write(0);
    g.Pin = PA_CS;
    g.Mode = GPIO_MODE_INPUT;
    g.Pull = GPIO_PULLUP;
    HAL_GPIO_Init(GPIOA, &g);
}

/* Comprueba nivel de SCK y CS con un limite amplio para evitar bloqueos.
 * Devuelve 0 si hay timeout o CS se desactiva antes del fin.
 */
static uint8_t wait_clock(uint8_t high)
{
    uint32_t start = HAL_GetTick();
    for (;;)
    {
        if (!cs_is_low())
            return 0;
        if ((uint8_t)clk_is_high() == high)
            return 1;
        if ((uint32_t)(HAL_GetTick() - start) > 2000u)
            return 0;
    }
}

static void serve_spi_if_selected(void)
{
    if (!cs_is_low())
        return;
    uint8_t tx[FRAME];
    memcpy(tx, public_frame, FRAME);
    uint8_t command = 0;
    /* El maestro espera 15 ms entre CS=0 y el primer flanco. */
    for (uint32_t bit = 0; bit < FRAME * 8u; bit++)
    {
        uint8_t val = tx[bit >> 3];
        miso_write((val >> (7u - (bit & 7u))) & 1u);
        if (!wait_clock(1u))
            goto end_transfer;
        if (bit < 8u)
            command = (uint8_t)((command << 1u) | ((GPIOB->IDR & PB_MOSI) != 0u));
        if (!wait_clock(0u))
            goto end_transfer;
    }
    /* Se atienden los comandos solo tras una transferencia completa. */
    {
        uint32_t start = HAL_GetTick();
        while (cs_is_low() && (uint32_t)(HAL_GetTick() - start) < 2000u)
        {
        }
    }
    if (command >= 1u && command <= 3u)
        requested_preset = command;
end_transfer:
    miso_write(0);
}

void HAL_ADC_MspInit(ADC_HandleTypeDef *h)
{
    if (h->Instance != ADC1)
        return;
    __HAL_RCC_GPIOA_CLK_ENABLE();
    __HAL_RCC_ADC_CLK_ENABLE();
    __HAL_RCC_DMA1_CLK_ENABLE();
    GPIO_InitTypeDef g = {0};
    g.Pin = GPIO_PIN_0 | GPIO_PIN_1;
    g.Mode = GPIO_MODE_ANALOG_ADC_CONTROL;
    g.Pull = GPIO_NOPULL;
    HAL_GPIO_Init(GPIOA, &g);
    hdma_adc1.Instance = DMA1_Channel1;
    hdma_adc1.Init.Request = DMA_REQUEST_0; /* ADC1 en DMA1_CH1, RM0394 */
    hdma_adc1.Init.Direction = DMA_PERIPH_TO_MEMORY;
    hdma_adc1.Init.PeriphInc = DMA_PINC_DISABLE;
    hdma_adc1.Init.MemInc = DMA_MINC_ENABLE;
    hdma_adc1.Init.PeriphDataAlignment = DMA_PDATAALIGN_HALFWORD;
    hdma_adc1.Init.MemDataAlignment = DMA_MDATAALIGN_HALFWORD;
    hdma_adc1.Init.Mode = DMA_CIRCULAR;
    hdma_adc1.Init.Priority = DMA_PRIORITY_HIGH;
    /* Inicializar DMA antes de vincularlo al ADC. */
    HAL_StatusTypeDef dma_result = HAL_DMA_Init(&hdma_adc1);
    if (dma_result != HAL_OK)
    {
        dma_setup_error = 1u;
        return;
    }

    /* Equivalente a __HAL_LINKDMA(h, DMA_Handle, hdma_adc1).
       Se usan las asignaciones directas para evitar errores de macro. */
    h->DMA_Handle = &hdma_adc1;
    hdma_adc1.Parent = h;
    HAL_NVIC_SetPriority(DMA1_Channel1_IRQn, 2, 0);
    HAL_NVIC_EnableIRQ(DMA1_Channel1_IRQn);
}

void HAL_TIM_Base_MspInit(TIM_HandleTypeDef *h)
{
    if (h->Instance == TIM2)
        __HAL_RCC_TIM2_CLK_ENABLE();
}
void DMA1_Channel1_IRQHandler(void) { HAL_DMA_IRQHandler(&hdma_adc1); }

void HAL_ADC_ConvCpltCallback(ADC_HandleTypeDef *h)
{
    if (h->Instance != ADC1)
        return;
    for (uint32_t i = 0; i < SAMPLES * 2u; i++)
        completed_adc[i] = adc_dma[i];
    completed_seq++;
    status_code = 0;
}
void HAL_ADC_ErrorCallback(ADC_HandleTypeDef *h)
{
    (void)h;
    status_code = 0x17u;
}

/* ADC 12b, scan canales 5 y 6, TIM2 TRGO y DMA circular. */
static uint8_t adc_init(void)
{
    hadc1.Instance = ADC1;
    hadc1.Init.ClockPrescaler = ADC_CLOCK_SYNC_PCLK_DIV2;
    hadc1.Init.Resolution = ADC_RESOLUTION_12B;
    hadc1.Init.DataAlign = ADC_DATAALIGN_RIGHT;
    hadc1.Init.ScanConvMode = ADC_SCAN_ENABLE;
    hadc1.Init.EOCSelection = ADC_EOC_SEQ_CONV;
    hadc1.Init.LowPowerAutoWait = DISABLE;
    hadc1.Init.ContinuousConvMode = DISABLE;
    hadc1.Init.NbrOfConversion = 2;
    hadc1.Init.DiscontinuousConvMode = DISABLE;
    hadc1.Init.ExternalTrigConv = ADC_EXTERNALTRIG_T2_TRGO;
    hadc1.Init.ExternalTrigConvEdge = ADC_EXTERNALTRIGCONVEDGE_RISING;
    hadc1.Init.DMAContinuousRequests = ENABLE;
    hadc1.Init.Overrun = ADC_OVR_DATA_OVERWRITTEN;
    hadc1.Init.OversamplingMode = DISABLE;
    if (HAL_ADC_Init(&hadc1) != HAL_OK || dma_setup_error)
        return 0x10;
    if (HAL_ADCEx_Calibration_Start(&hadc1, ADC_SINGLE_ENDED) != HAL_OK)
        return 0x11;
    ADC_ChannelConfTypeDef c = {0};
    c.Channel = ADC_CHANNEL_5;
    c.Rank = ADC_REGULAR_RANK_1;
    c.SamplingTime = ADC_SAMPLETIME_47CYCLES_5;
    c.SingleDiff = ADC_SINGLE_ENDED;
    c.OffsetNumber = ADC_OFFSET_NONE;
    if (HAL_ADC_ConfigChannel(&hadc1, &c) != HAL_OK)
        return 0x13;
    c.Channel = ADC_CHANNEL_6;
    c.Rank = ADC_REGULAR_RANK_2;
    if (HAL_ADC_ConfigChannel(&hadc1, &c) != HAL_OK)
        return 0x14;
    htim2.Instance = TIM2;
    htim2.Init.Prescaler = 15;
    htim2.Init.CounterMode = TIM_COUNTERMODE_UP;
    htim2.Init.Period = 999;
    htim2.Init.ClockDivision = TIM_CLOCKDIVISION_DIV1;
    htim2.Init.AutoReloadPreload = TIM_AUTORELOAD_PRELOAD_DISABLE;
    if (HAL_TIM_Base_Init(&htim2) != HAL_OK)
        return 0x12;
    TIM_MasterConfigTypeDef m = {0};
    m.MasterOutputTrigger = TIM_TRGO_UPDATE;
    m.MasterSlaveMode = TIM_MASTERSLAVEMODE_DISABLE;
    if (HAL_TIMEx_MasterConfigSynchronization(&htim2, &m) != HAL_OK)
        return 0x12;
    return 0;
}

static uint8_t start_capture(uint8_t preset)
{
    HAL_TIM_Base_Stop(&htim2);
    HAL_ADC_Stop_DMA(&hadc1);
    current_preset = preset;
    status_code = 0x20u; /* preparar trama válida pero aún sin datos recientes */
    htim2.Instance->ARR = (1000000u / rate_for(preset)) - 1u;
    htim2.Instance->CNT = 0;
    htim2.Instance->EGR = TIM_EGR_UG;
    if (HAL_ADC_Start_DMA(&hadc1, (uint32_t *)(void *)adc_dma, SAMPLES * 2u) != HAL_OK)
        return 0x15;
    if (HAL_TIM_Base_Start(&htim2) != HAL_OK)
        return 0x16;
    return 0;
}

static void publish_frame(void)
{
    uint16_t block[SAMPLES * 2u];
    uint16_t seq;
    uint8_t status, preset;
    __disable_irq();
    for (uint32_t i = 0; i < SAMPLES * 2u; i++)
        block[i] = completed_adc[i];
    seq = completed_seq;
    status = status_code;
    preset = current_preset;
    __enable_irq();
    memset(work_frame, 0, FRAME);
    work_frame[0] = 'S';
    work_frame[1] = 'C';
    work_frame[2] = preset;
    work_frame[3] = status;
    put16(work_frame, 4, seq);
    if (status == 0u)
    {
        for (uint32_t i = 0; i < SAMPLES; i++)
        {
            put16(work_frame, 6 + 4 * i, block[2 * i]);
            put16(work_frame, 8 + 4 * i, block[2 * i + 1]);
        }
    }
    put16(work_frame, FRAME - 2, crc16(work_frame, FRAME - 2));
    __disable_irq();
    memcpy(public_frame, work_frame, FRAME);
    __enable_irq();
}

int main(void)
{
    HAL_Init();
    clock_init();
    spi_gpio_init();
    /* Cabecera SPI disponible inmediatamente, incluso si falla ADC. */
    publish_frame();
    uint8_t err = adc_init();
    if (!err)
        err = start_capture(2u);
    if (err)
        status_code = err;
    publish_frame();
    uint16_t last_seq = 0;
    uint8_t last_status = 0xFF;
    for (;;)
    {
        uint8_t request = 0;
        __disable_irq();
        request = requested_preset;
        requested_preset = 0;
        __enable_irq();
        if (request >= 1u && request <= 3u && request != current_preset)
        {
            err = start_capture(request);
            if (err)
                status_code = err;
        }
        if (last_seq != completed_seq || last_status != status_code)
        {
            last_seq = completed_seq;
            last_status = status_code;
            publish_frame();
        }
        serve_spi_if_selected();
    }
}
