#include "processes.hpp"
#include "colors.hpp"

#include <iostream>
#include <chrono>
#include <thread>

// Rendering period (700 milliseconds)
inline constexpr auto RENDER_PERIOD = std::chrono::milliseconds(700);

void private_render_function(SyncFrame* frame_buffer, DaqBuffer* daq_data) {
    std::cout << colors::GREEN << "[i] Rendering function executed. Frame size: "
              << frame_buffer->width << "x" << frame_buffer->height
              << ", DAQ buffer size: " << daq_data->size() << "\r\n"
              << colors::RESET;
}

void renderer(RenderPack& render_pack, const std::atomic<bool>& running) {
    while (running.load(std::memory_order_relaxed)) {
        std::cout << colors::BLUE << "-> Frame rendering execution.\r\n" << colors::RESET;

        {
            // Lock frame buffer and DAQ buffer (matching pthread_mutex_lock in C)
            std::unique_lock<std::mutex> frame_lock(render_pack.frame_buffer->frame_mutex);
            std::unique_lock<std::mutex> daq_lock(render_pack.daq_data->daq_mutex);

            // Fast render function. Not thread-safe, so called with mutexes held.
            private_render_function(render_pack.frame_buffer, render_pack.daq_data);
            std::cout << colors::GREEN << "[i] Frame rendering performed.\r\n"
                      << colors::RESET;
            std::this_thread::sleep_for(RENDER_PERIOD);
            render_pack.daq_data->has_new_data = 0; // Mark data as processed
        }

        // Wait for DAQ to produce new data and release daq_mutex
        std::unique_lock<std::mutex> daq_wait_lock(render_pack.daq_data->daq_mutex);
        render_pack.daq_data->daq_cond.wait(daq_wait_lock, [&] {
            return render_pack.daq_data->has_new_data != 0 || !running.load(std::memory_order_relaxed);
        });
    }
}

