#pragma once

#include <cstddef>
#include <cstdint>
#include <vector>
#include <mutex>
#include <condition_variable>
#include <atomic>
#include <thread>

// Structure to hold synchronized frame data
struct SyncFrame {
    uint16_t width{0};
    uint16_t height{0};
    std::vector<uint8_t> data;
    std::mutex frame_mutex; // Mutex for synchronizing access to the frame data

    SyncFrame(uint16_t w = 0, uint16_t h = 0)
        : width(w), height(h), data(static_cast<size_t>(w) * h, 0) {}

    // Disable copying as mutexes are non-copyable
    SyncFrame(const SyncFrame&) = delete;
    SyncFrame& operator=(const SyncFrame&) = delete;

    size_t size_bytes() const noexcept {
        return data.size();
    }
};

// Structure to hold fast copy source and destination buffers
struct FastCopyArgs {
    SyncFrame* src{nullptr};
    SyncFrame* dest{nullptr};
};

// Structure to hold DAQ buffer, mutex, condition variable, and status flag
struct DaqBuffer {
    std::vector<uint16_t> buffer;
    std::mutex daq_mutex;           // Mutex for synchronizing access to the buffer
    std::condition_variable daq_cond; // Condition variable for DAQ and renderer synchronization
    uint8_t has_new_data{0};        // Condition flag indicating DAQ has produced new data

    explicit DaqBuffer(size_t size = 1024)
        : buffer(size, 0), has_new_data(0) {}

    // Disable copying
    DaqBuffer(const DaqBuffer&) = delete;
    DaqBuffer& operator=(const DaqBuffer&) = delete;

    size_t size() const noexcept {
        return buffer.size();
    }
};

// Structure to hold memory frame buffer and DAQ data
struct RenderPack {
    SyncFrame* frame_buffer{nullptr};
    DaqBuffer* daq_data{nullptr};
};

// Function prototypes for the process worker functions
void daq(DaqBuffer& daq_buffer, const std::atomic<bool>& running);
void renderer(RenderPack& render_pack, const std::atomic<bool>& running);
void fast_copy(FastCopyArgs& buffers, const std::atomic<bool>& running);
void display_frame(FastCopyArgs& args, const std::atomic<bool>& running);

