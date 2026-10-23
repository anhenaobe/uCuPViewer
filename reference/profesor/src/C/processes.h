#pragma once

#include <stddef.h>
#include <sched.h>
#include <stdio.h>
#include <unistd.h>
#include <pthread.h>
#include <stdint.h>

// Define a structure to hold frame data
typedef struct {
    uint16_t width;
    uint16_t height;
    uint8_t* data;
    pthread_mutex_t* frame_mutex; // Mutex for synchronizing access to the frame data
} SyncFrame;

// Structure to hold fast copy source and destination buffers
typedef struct {
    SyncFrame* src;
    SyncFrame* dest;
} FastCopyArgs;

// Structure to hold DAQ buffer and size
typedef struct {
    uint16_t* buffer;
    pthread_mutex_t* daq_mutex; // Mutex for synchronizing access to the buffer
    pthread_cond_t* daq_cond;   // Condition variable for DAQ and renderer synchronization
    uint8_t has_new_data;       // Condition flag indicating DAQ has produced new data
    size_t size;
} DaqBuffer;

// Structure to hold memory frame buffer and DAQ data.
typedef struct {
    SyncFrame* frame_buffer;
    DaqBuffer* daq_data;
} RenderPack;

extern pthread_t render_thread, daq_thread, fast_copy_thread, display_thread;

// Function prototypes for the processes
void* renderer(void* arg);
void* daq(void* arg);
void* fast_copy(void* arg);
void* display_frame(void* arg);
