#include "processes.h"
#include "colors.h"

// Define the data acquisition period in nanoseconds (500 milliseconds). Should be adjusted 
// to compensate for the time taken by the data acquisition function itself.
#define DAQ_PERIOD_NS 500000000

void private_daq_function(uint16_t* buffer, size_t size) {
    // Placeholder for the actual data acquisition logic.
    // This function would typically communicate with hardware to fill the buffer with data.
    // For example, it might read sensor values or other input data and store it in the buffer.
    // The implementation details would depend on the specific requirements of the data acquisition process.
    printf("%s[i] Data acquisition function executed. Buffer size: %zu\r\n%s", 
        ANSI_COLOR_GREEN, size, ANSI_COLOR_RESET);
}

// Placeholder for the daq function, which would typically be defined elsewhere.
void* daq(void* arg) {
    struct timespec tp = { 0, DAQ_PERIOD_NS };
    DaqBuffer* daq_buffer = (DaqBuffer*)arg;
    // Placeholder for data acquisition function implementation
    while (1) {
        printf("%sData acquisition execution.\r\n%s", ANSI_COLOR_BLUE, ANSI_COLOR_RESET);
        uint8_t lock_error = pthread_mutex_lock(daq_buffer->daq_mutex);
        if (lock_error) {
            printf("%s[E] Data acquisition: skipped due to mutex lock.\r\n%s", ANSI_COLOR_RED, ANSI_COLOR_RESET);
        }
        else {
            // This function implements hardware communication and data dump from microcontroller.
            private_daq_function(daq_buffer->buffer, daq_buffer->size);
            printf("%s[i] Data acquisition performed.\r\n%s", ANSI_COLOR_GREEN, ANSI_COLOR_RESET);
            daq_buffer->has_new_data = 1;
            pthread_mutex_unlock(daq_buffer->daq_mutex);
            // Signal the condition that new DAQ data is available and daq_mutex has been released
            pthread_cond_signal(daq_buffer->daq_cond);
        }
        nanosleep(&tp, NULL); // seconds.
    }
    return NULL;
}
