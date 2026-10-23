#include <stdio.h>
#include <signal.h>
#include <stdlib.h>
#include <time.h>

#include "processes.h"

// Startup delay before starting the renderer and display threads (200 milliseconds)
#define STARTUP_DELAY_NS 200000000

// Thread identifiers
pthread_t render_thread;
pthread_t daq_thread;
pthread_t fast_copy_thread;
pthread_t display_thread;

// Global variables for the frame buffers and DAQ buffer. Serve for sharing data between threads.
SyncFrame render_buffer = { .width = 640, .height = 480, .data = NULL, .frame_mutex = NULL };
SyncFrame draw_buffer = { .width = 640, .height = 480, .data = NULL, .frame_mutex = NULL };
DaqBuffer daq_buffer = { .buffer = NULL, .size = 1024, .daq_mutex = NULL, .daq_cond = NULL, .has_new_data = 0 };
FastCopyArgs fast_copy_args = { .src = &render_buffer, .dest = &draw_buffer };
RenderPack render_pack = { .frame_buffer = &render_buffer, .daq_data = &daq_buffer };

// Signal handler for graceful termination of the program.
void handle_signal(int signal);


int main() {
    // Signal handling for graceful termination.
    signal(SIGINT, handle_signal);

    printf("Starting processes...\n\r");

    render_buffer.frame_mutex = malloc(sizeof(pthread_mutex_t));
    draw_buffer.frame_mutex = malloc(sizeof(pthread_mutex_t));
    daq_buffer.daq_mutex = malloc(sizeof(pthread_mutex_t));
    daq_buffer.daq_cond = malloc(sizeof(pthread_cond_t));

    pthread_mutex_init(render_buffer.frame_mutex, NULL);
    pthread_mutex_init(draw_buffer.frame_mutex, NULL);
    pthread_mutex_init(daq_buffer.daq_mutex, NULL);
    pthread_cond_init(daq_buffer.daq_cond, NULL);
    daq_buffer.has_new_data = 0;

    int create_error = 0;

    // 1. Start the DAQ thread first
    create_error = pthread_create(&daq_thread, NULL, &daq, (void*)&daq_buffer);
    if (create_error) {
        fprintf(stderr, "Error creating DAQ thread\n");
        return 1;
    }

    // Delay a few hundred milliseconds before starting the other threads
    struct timespec start_delay = { 0, STARTUP_DELAY_NS };
    nanosleep(&start_delay, NULL);

    // 2. Start the other two threads (display_frame and renderer)
    create_error |= pthread_create(&display_thread, NULL, &display_frame, (void*)&fast_copy_args);
    create_error |= pthread_create(&render_thread, NULL, &renderer, (void*)&render_pack);
    if (create_error) {
        fprintf(stderr, "Error creating threads\n");
        return 1;
    }

    // Await the completion of all threads
    pthread_join(daq_thread, NULL);
    pthread_join(display_thread, NULL);
    pthread_join(render_thread, NULL);
    return 0;
}


// Signal handler implementation.
void handle_signal(int signal) {
    if (signal == SIGINT) {
        printf("\nSIGINT received. Terminating processes...\n");
        // Perform any necessary cleanup here, such as freeing allocated memory or closing resources.
        // First, destroy the condition variables and mutexes.
        if (daq_buffer.daq_cond) {
            pthread_cond_destroy(daq_buffer.daq_cond);
            free(daq_buffer.daq_cond);
        }
        if (render_buffer.frame_mutex) {
            pthread_mutex_destroy(render_buffer.frame_mutex);
            free(render_buffer.frame_mutex);
        }
        if (draw_buffer.frame_mutex) {
            pthread_mutex_destroy(draw_buffer.frame_mutex);
            free(draw_buffer.frame_mutex);
        }
        if (daq_buffer.daq_mutex) {
            pthread_mutex_destroy(daq_buffer.daq_mutex);
            free(daq_buffer.daq_mutex);
        }
        // Then, free the allocated buffers.
        if (render_buffer.data)  free(render_buffer.data);
        if (draw_buffer.data)    free(draw_buffer.data);
        if (daq_buffer.buffer)   free(daq_buffer.buffer);         
    }
    exit(0);
}
