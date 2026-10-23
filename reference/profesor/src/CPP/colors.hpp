#pragma once

// ANSI Escape sequences for colored terminal output
namespace colors {
    inline constexpr const char* RESET   = "\x1b[0m";
    inline constexpr const char* RED     = "\x1b[31m";
    inline constexpr const char* GREEN   = "\x1b[32m";
    inline constexpr const char* YELLOW  = "\x1b[33m";
    inline constexpr const char* BLUE    = "\x1b[34m";
    inline constexpr const char* MAGENTA = "\x1b[35m";
    inline constexpr const char* CYAN    = "\x1b[36m";
    inline constexpr const char* WHITE   = "\x1b[37m";
}

// Backward-compatible macros matching the C version
#define ANSI_COLOR_RED     colors::RED
#define ANSI_COLOR_GREEN   colors::GREEN
#define ANSI_COLOR_YELLOW  colors::YELLOW
#define ANSI_COLOR_BLUE    colors::BLUE
#define ANSI_COLOR_MAGENTA colors::MAGENTA
#define ANSI_COLOR_CYAN    colors::CYAN
#define ANSI_COLOR_RESET   colors::RESET

