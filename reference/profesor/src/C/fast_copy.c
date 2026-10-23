#include "processes.h"
#include "colors.h"
#include "string.h"

// Placeholder for the fast copy function, which would typically be defined elsewhere.
void* fast_copy(void* arg) {
    FastCopyArgs* buffers = (FastCopyArgs*)arg;
    // Placeholder for fast copy function implementation
    while (1) {
        printf("%s-> Fast copy execution:\r\n%s", ANSI_COLOR_BLUE, ANSI_COLOR_RESET);
        int8_t src_lock_error = pthread_mutex_trylock(buffers->src->frame_mutex);
        // Nested lock checking: first check if the source mutex is locked, then check if 
        // the destination mutex is locked.
        if (src_lock_error) {
            printf("%s[E] Fast copy: skipped due to mutex lock.\r\n%s", 
                ANSI_COLOR_RED, ANSI_COLOR_RESET);
        }
        else {  // Here src buffer is locked.
            int8_t dest_lock_error = pthread_mutex_trylock(buffers->dest->frame_mutex);
            if (dest_lock_error) {
                printf("%s[E] Fast copy: skipped due to destination mutex lock.\r\n%s", 
                    ANSI_COLOR_RED, ANSI_COLOR_RESET);
            }
            else {
                // Actual fast copy operation would go here. 
                if (buffers->dest->data && buffers->src->data) {
                    memcpy(buffers->dest->data, buffers->src->data, 
                        buffers->src->width * buffers->src->height * sizeof(uint8_t));
                }
                printf("%s[i] Fast copy: performed successfully.\r\n%s", 
                    ANSI_COLOR_GREEN, ANSI_COLOR_RESET);
                pthread_mutex_unlock(buffers->dest->frame_mutex); 
            }
            pthread_mutex_unlock(buffers->src->frame_mutex); // Unlock the src mutex
        }
        sched_yield(); // Yield to allow other threads to run
    }
    return NULL;
}
