# Project configuration
TARGET      ?= test

# Compiler and tools
CXX         ?= g++

# Compilation flags
DEBUG       ?= 0
ifeq ($(DEBUG), 1)
    CXXFLAGS ?= -Wall -Wextra -std=c++20 -g3 -O0 -DDEBUG
else
    CXXFLAGS ?= -Wall -Wextra -std=c++20 -O2
endif

# POSIX threads flag for compilation and linking
CXXFLAGS    += -pthread
CPPFLAGS    ?= -I. -MMD -MP
LDFLAGS     ?=
LDLIBS      ?= -pthread

# Source, object, and dependency files
SRCS        := $(wildcard *.cpp)
OBJS        := $(SRCS:.cpp=.o)
DEPS        := $(SRCS:.cpp=.d)

.PHONY: all clean run debug release help info

# Default target
all: $(TARGET)

# Link executable
$(TARGET): $(OBJS)
	$(CXX) $(OBJS) $(LDFLAGS) $(LDLIBS) -o $@

# Compile C++ source files into object files
%.o: %.cpp
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) -c $< -o $@

# Include generated header dependencies
-include $(DEPS)

# Debug build
debug:
	@$(MAKE) DEBUG=1

# Release build
release:
	@$(MAKE) DEBUG=0

# Run the program
run: $(TARGET)
	./$(TARGET)

# Clean build artifacts
clean:
	rm -f $(OBJS) $(DEPS) $(TARGET)

# Show build configuration details
info:
	@echo "Target:         $(TARGET)"
	@echo "Compiler (CXX): $(CXX)"
	@echo "CXXFLAGS:       $(CXXFLAGS)"
	@echo "CPPFLAGS:       $(CPPFLAGS)"
	@echo "LDFLAGS:        $(LDFLAGS)"
	@echo "LDLIBS:         $(LDLIBS)"
	@echo "Source files:   $(SRCS)"
	@echo "Object files:   $(OBJS)"

# Help message
help:
	@echo "Makefile usage for $(TARGET):"
	@echo "  make              Build release executable (default: $(TARGET))"
	@echo "  make debug        Build with debug symbols (-g3 -O0 -DDEBUG)"
	@echo "  make release      Build optimized release binary (-O2)"
	@echo "  make run          Build and execute the program"
	@echo "  make clean        Remove build artifacts (*.o, *.d, $(TARGET))"
	@echo "  make info         Print configuration variables and file lists"
	@echo "  make help         Show this help message"
	@echo ""
	@echo "Override variables:"
	@echo "  make CXX=clang++  Use an alternative C++ compiler"
	@echo "  make DEBUG=1      Enable debug mode directly"
	@echo "  make TARGET=foo   Change output binary name"

