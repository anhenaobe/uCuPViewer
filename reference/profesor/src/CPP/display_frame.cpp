#include "processes.hpp"
#include "colors.hpp"

#include <iostream>
#include <chrono>
#include <thread>

// Display frame refresh period (1 second)
inline constexpr auto DISPLAY_PERIOD = std::chrono::seconds(1);

void display_frame(FastCopyArgs& /*args*/, const std::atomic<bool>& running) {
    while (running.load(std::memory_order_relaxed)) {
        std::cout << colors::BLUE << "Display frame execution.\r\n" << colors::RESET;
        // Display drawing logic would go here
        std::this_thread::sleep_for(DISPLAY_PERIOD);
    }
}

