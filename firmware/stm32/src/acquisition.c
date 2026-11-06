#include "acquisition.h"
#include "stm32l4xx_hal.h"
static ADC_HandleTypeDef adc;
static DMA_HandleTypeDef dma;
static TIM_HandleTypeDef timer;
static uint16_t samples[ACQUISITION_VALUES] __attribute__((aligned(4)));
_Static_assert(sizeof(samples) == 256, "window size");
static volatile acquisition_state_t state = ACQ_ERROR;
static volatile uint32_t complete, fault;
static uint32_t rate = 1000;
static bool hardware_ready;

acquisition_state_t acquisition_get_status(void) { return state; }
uint32_t acquisition_get_preset(void) { return rate; }
const uint16_t *acquisition_get_window(void) { return state == ACQ_READY ? samples : 0; }
bool acquisition_release_window(void) {
    if (state != ACQ_READY) return false;
    state = ACQ_IDLE;
    return true;
}
static bool halt(void) {
    __HAL_TIM_DISABLE(&timer);
    bool timer_ok = HAL_TIM_Base_Stop(&timer) == HAL_OK;
    bool adc_ok = HAL_ADC_Stop_DMA(&adc) == HAL_OK;
    return timer_ok && adc_ok;
}
bool acquisition_stop(void) {
    if (!hardware_ready || state == ACQ_READY) return false; /* Consumer must explicitly release. */
    if (!halt()) { state = ACQ_ERROR; return false; }
    complete = fault = 0;
    state = ACQ_IDLE;
    return true;
}
bool acquisition_set_preset(uint32_t hz) {
    if (state != ACQ_IDLE || (hz != 100 && hz != 1000 && hz != 10000)) return false;
    uint32_t clock = HAL_RCC_GetPCLK1Freq();
    if ((RCC->CFGR & RCC_CFGR_PPRE1) != 0) clock *= 2;
    if (clock % 1000000u != 0 || clock < 1000000u) return false;
    timer.Instance = TIM2;
    timer.Init.Prescaler = clock / 1000000u - 1u;
    timer.Init.Period = 1000000u / hz - 1u;
    timer.Init.CounterMode = TIM_COUNTERMODE_UP;
    timer.Init.ClockDivision = TIM_CLOCKDIVISION_DIV1;
    timer.Init.AutoReloadPreload = TIM_AUTORELOAD_PRELOAD_DISABLE;
    if (HAL_TIM_Base_Init(&timer) != HAL_OK) { state = ACQ_ERROR; return false; }
    TIM_MasterConfigTypeDef master = {0};
    master.MasterOutputTrigger = TIM_TRGO_UPDATE;
    master.MasterSlaveMode = TIM_MASTERSLAVEMODE_DISABLE;
    if (HAL_TIMEx_MasterConfigSynchronization(&timer, &master) != HAL_OK) {
        state = ACQ_ERROR; return false;
    }
    rate = hz;
    return true;
}
bool acquisition_start(void) {
    if (!hardware_ready || state != ACQ_IDLE) return false;
    complete = fault = 0;
    __HAL_TIM_SET_COUNTER(&timer, 0);
    __HAL_TIM_CLEAR_FLAG(&timer, TIM_FLAG_UPDATE);
    state = ACQ_ACQUIRING;
    if (HAL_ADC_Start_DMA(&adc, (uint32_t *)samples, ACQUISITION_VALUES) != HAL_OK) {
        halt(); state = ACQ_ERROR; return false;
    }
    if (HAL_TIM_Base_Start(&timer) != HAL_OK) {
        halt(); state = ACQ_ERROR; return false;
    }
    return true;
}
void acquisition_poll(void) {
    if (state != ACQ_ACQUIRING || (!complete && !fault)) return;
    bool stopped = halt();
    __DMB();
    state = (!stopped || fault) ? ACQ_ERROR : ACQ_READY;
}
void HAL_ADC_ConvCpltCallback(ADC_HandleTypeDef *h) {
    if (h != &adc) return;
    __HAL_TIM_DISABLE(&timer);
    __DMB();
    complete = 1;
}
void HAL_ADC_ErrorCallback(ADC_HandleTypeDef *h) {
    if (h != &adc) return;
    __HAL_TIM_DISABLE(&timer);
    fault = 1;
}
void DMA1_Channel1_IRQHandler(void) { HAL_DMA_IRQHandler(&dma); }
void ADC1_IRQHandler(void) { HAL_ADC_IRQHandler(&adc); }
bool acquisition_init(void) {
    /* Once at boot; reinitialization cannot invalidate a borrowed window. */
    static bool initialized;
    if (initialized) return false;
    initialized = true;
    __HAL_RCC_GPIOA_CLK_ENABLE();
    __HAL_RCC_DMA1_CLK_ENABLE();
    __HAL_RCC_ADC_CLK_ENABLE();
    __HAL_RCC_TIM2_CLK_ENABLE();
    GPIO_InitTypeDef pins = {0};
    pins.Pin = GPIO_PIN_0 | GPIO_PIN_1;
    pins.Mode = GPIO_MODE_ANALOG_ADC_CONTROL;
    pins.Pull = GPIO_NOPULL;
    HAL_GPIO_Init(GPIOA, &pins);
    dma.Instance = DMA1_Channel1;
    dma.Init.Request = DMA_REQUEST_0;
    dma.Init.Direction = DMA_PERIPH_TO_MEMORY;
    dma.Init.PeriphInc = DMA_PINC_DISABLE;
    dma.Init.MemInc = DMA_MINC_ENABLE;
    dma.Init.PeriphDataAlignment = DMA_PDATAALIGN_HALFWORD;
    dma.Init.MemDataAlignment = DMA_MDATAALIGN_HALFWORD;
    dma.Init.Mode = DMA_NORMAL;
    dma.Init.Priority = DMA_PRIORITY_HIGH;
    if (HAL_DMA_Init(&dma) != HAL_OK) return false;
    __HAL_LINKDMA(&adc, DMA_Handle, dma);
    adc.Instance = ADC1;
    adc.Init.ClockPrescaler = ADC_CLOCK_SYNC_PCLK_DIV2;
    adc.Init.Resolution = ADC_RESOLUTION_12B;
    adc.Init.DataAlign = ADC_DATAALIGN_RIGHT;
    adc.Init.ScanConvMode = ADC_SCAN_ENABLE;
    adc.Init.EOCSelection = ADC_EOC_SEQ_CONV;
    adc.Init.NbrOfConversion = 2;
    adc.Init.ExternalTrigConv = ADC_EXTERNALTRIG_T2_TRGO;
    adc.Init.ExternalTrigConvEdge = ADC_EXTERNALTRIGCONVEDGE_RISING;
    adc.Init.DMAContinuousRequests = DISABLE;
    adc.Init.Overrun = ADC_OVR_DATA_PRESERVED;
    if (HAL_ADC_Init(&adc) != HAL_OK) return false;
    ADC_ChannelConfTypeDef channel = {0};
    channel.SamplingTime = ADC_SAMPLETIME_47CYCLES_5;
    channel.SingleDiff = ADC_SINGLE_ENDED;
    channel.OffsetNumber = ADC_OFFSET_NONE;
    channel.Channel = ADC_CHANNEL_5;
    channel.Rank = ADC_REGULAR_RANK_1;
    if (HAL_ADC_ConfigChannel(&adc, &channel) != HAL_OK) return false;
    channel.Channel = ADC_CHANNEL_6;
    channel.Rank = ADC_REGULAR_RANK_2;
    if (HAL_ADC_ConfigChannel(&adc, &channel) != HAL_OK) return false;
    if (HAL_ADCEx_Calibration_Start(&adc, ADC_SINGLE_ENDED) != HAL_OK) return false;
    HAL_NVIC_SetPriority(DMA1_Channel1_IRQn, 1, 0);
    HAL_NVIC_EnableIRQ(DMA1_Channel1_IRQn);
    HAL_NVIC_SetPriority(ADC1_IRQn, 1, 0);
    HAL_NVIC_EnableIRQ(ADC1_IRQn);
    state = ACQ_IDLE;
    hardware_ready = acquisition_set_preset(rate);
    if (!hardware_ready) state = ACQ_ERROR;
    return hardware_ready;
}
