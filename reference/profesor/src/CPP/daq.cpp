#include "processes.hpp"
#include "colors.hpp"

#include <iostream>
#include <chrono>
#include <thread>

// Data acquisition period (500 milliseconds)
inline constexpr auto DAQ_PERIOD = std::chrono::milliseconds(500);

void private_daq_function(uint16_t* buffer, size_t size) {
    (void)buffer; // Placeholder for actual hardware communication
    std::cout << colors::GREEN << "[i] Data acquisition function executed. Buffer size: "
              << size << "\r\n" << colors::RESET;
}

void daq(DaqBuffer& daq_buffer, const std::atomic<bool>& running) {
    while (running.load(std::memory_order_relaxed)) {
        std::cout << colors::BLUE << "Data acquisition execution.\r\n" << colors::RESET;

        {
            // Blocking lock matching pthread_mutex_lock in C
            std::unique_lock<std::mutex> lock(daq_buffer.daq_mutex);

            // Implements hardware communication and data dump from microcontroller
            private_daq_function(daq_buffer.buffer.data(), daq_buffer.size());
            std::cout << colors::GREEN << "[i] Data acquisition performed.\r\n"
                      << colors::RESET;
            daq_buffer.has_new_data = 1;

            lock.unlock();

            // Signal condition variable that new DAQ data is available
            daq_buffer.daq_cond.notify_one();
        }

        std::this_thread::sleep_for(DAQ_PERIOD);
    }
}

