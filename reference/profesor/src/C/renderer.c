#include "processes.h"
#include "colors.h"

// Define the rendering period in nanoseconds and seconds. Should be adjusted 
// to compensate for the time taken by the rendering process itself.
#define RENDER_PERIOD_NS 700000000
#define RENDER_PERIOD_S 0


void private_render_function(SyncFrame* frame_buffer, DaqBuffer* daq_data) {
    // Placeholder for the actual rendering logic.
    // This function would typically process the data in daq_data and update the frame_buffer accordingly.
    // For example, it might convert raw data into a visual representation and store it in frame_buffer->data.
    // The implementation details would depend on the specific requirements of the rendering process.
    printf("%s[i] Rendering function executed. Frame size: %dx%d, DAQ buffer size: %zu\r\n%s", 
        ANSI_COLOR_GREEN, frame_buffer->width, frame_buffer->height, daq_data->size, ANSI_COLOR_RESET);
}

// Placeholder for the renderer function, which would typically be defined elsewhere.
void* renderer(void* arg) {
    struct timespec tp = { RENDER_PERIOD_S, RENDER_PERIOD_NS };
    RenderPack* render_pack = (RenderPack*)arg;
    // Placeholder for renderer function implementation
    while (1) {
        printf("%s-> Frame rendering execution.\r\n%s", ANSI_COLOR_BLUE, ANSI_COLOR_RESET);
        uint8_t buffer_lock_error = pthread_mutex_lock(render_pack->frame_buffer->frame_mutex);
        if (buffer_lock_error) {
            printf("%s[E] Frame rendering: skipped due to mutex lock.\r\n%s", 
                ANSI_COLOR_RED, ANSI_COLOR_RESET);
        }
        else {
            uint8_t daq_lock_error = pthread_mutex_lock(render_pack->daq_data->daq_mutex);
            if (daq_lock_error) {
                printf("%s[E] Frame rendering: skipped due to DAQ mutex lock timeout.\r\n%s",
                    ANSI_COLOR_RED, ANSI_COLOR_RESET);
            }
            else {
                // Fast render function. Not thread-safe, so it must be called with the mutexes locked.
                private_render_function(render_pack->frame_buffer, render_pack->daq_data);
                printf("%s[i] Frame rendering performed.\r\n%s", ANSI_COLOR_GREEN, ANSI_COLOR_RESET);
                nanosleep(&tp, NULL); // seconds
                render_pack->daq_data->has_new_data = 0; // Mark data as processed
                pthread_mutex_unlock(render_pack->daq_data->daq_mutex);
            }
            pthread_mutex_unlock(render_pack->frame_buffer->frame_mutex);
        }

        // Wait for DAQ to produce new data and release the daq_mutex
        pthread_mutex_lock(render_pack->daq_data->daq_mutex);
        while (!render_pack->daq_data->has_new_data) {
            pthread_cond_wait(render_pack->daq_data->daq_cond, render_pack->daq_data->daq_mutex);
        }
        pthread_mutex_unlock(render_pack->daq_data->daq_mutex);
    }
    return NULL;
}
