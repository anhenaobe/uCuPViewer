#include <iostream>
#include <csignal>
#include <cstdlib>
#include <chrono>
#include <thread>
#include <atomic>

#include "processes.hpp"

// Startup delay before starting the renderer and display threads (200 milliseconds)
inline constexpr auto STARTUP_DELAY = std::chrono::milliseconds(200);

namespace {
    std::atomic<bool> g_running{true};
    DaqBuffer* g_daq_buffer_ptr{nullptr};

    // Signal handler for graceful termination of the program
    void handle_signal(int signal) {
        if (signal == SIGINT) {
            std::cout << "\nSIGINT received. Terminating processes...\n";
            g_running.store(false, std::memory_order_relaxed);
            if (g_daq_buffer_ptr) {
                g_daq_buffer_ptr->daq_cond.notify_all();
            }
            // Standard library objects (std::vector, etc.) clean up automatically
            std::exit(0);
        }
    }
}

int main() {
    // Signal handling for graceful termination
    std::signal(SIGINT, handle_signal);

    std::cout << "Starting processes...\n\r";

    // Frame buffers and DAQ buffer (memory managed automatically by std::vector)
    SyncFrame render_buffer(640, 480);
    SyncFrame draw_buffer(640, 480);
    DaqBuffer daq_buffer(1024);

    g_daq_buffer_ptr = &daq_buffer;

    FastCopyArgs fast_copy_args{ &render_buffer, &draw_buffer };
    RenderPack render_pack{ &render_buffer, &daq_buffer };

    // 1. Start the DAQ thread first
    std::thread daq_thread([&daq_buffer]() {
        daq(daq_buffer, g_running);
    });

    // Delay a few hundred milliseconds before starting the other threads
    std::this_thread::sleep_for(STARTUP_DELAY);

    // 2. Start the display and renderer threads
    std::thread display_thread([&fast_copy_args]() {
        display_frame(fast_copy_args, g_running);
    });

    std::thread render_thread([&render_pack]() {
        renderer(render_pack, g_running);
    });

    // Await the completion of all threads
    if (daq_thread.joinable())     daq_thread.join();
    if (display_thread.joinable()) display_thread.join();
    if (render_thread.joinable())  render_thread.join();

    return 0;
}

