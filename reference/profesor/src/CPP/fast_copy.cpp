#include "processes.hpp"
#include "colors.hpp"

#include <iostream>
#include <cstring>
#include <algorithm>
#include <thread>

void fast_copy(FastCopyArgs& buffers, const std::atomic<bool>& running) {
    while (running.load(std::memory_order_relaxed)) {
        std::cout << colors::BLUE << "-> Fast copy execution:\r\n" << colors::RESET;

        std::unique_lock<std::mutex> src_lock(buffers.src->frame_mutex, std::try_to_lock);
        if (!src_lock.owns_lock()) {
            std::cout << colors::RED << "[E] Fast copy: skipped due to mutex lock.\r\n"
                      << colors::RESET;
        } else {
            std::unique_lock<std::mutex> dest_lock(buffers.dest->frame_mutex, std::try_to_lock);
            if (!dest_lock.owns_lock()) {
                std::cout << colors::RED 
                        << "[E] Fast copy: skipped due to destination mutex lock.\r\n"
                        << colors::RESET;
            } else {
                if (!buffers.dest->data.empty() && !buffers.src->data.empty()) {
                    const size_t copy_size = std::min(buffers.src->size_bytes(), 
                            buffers.dest->size_bytes());
                    std::memcpy(buffers.dest->data.data(), buffers.src->data.data(), copy_size);
                }
                std::cout << colors::GREEN << "[i] Fast copy: performed successfully.\r\n"
                          << colors::RESET;
            }
        }
        std::this_thread::yield();
    }
}

