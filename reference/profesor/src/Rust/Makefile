# Project configuration
TARGET      ?= test
CARGO       ?= cargo

.PHONY: all clean run debug release help info

# Default target: release build
all: release

# Release build
release:
	$(CARGO) build --release
	@cp target/release/$(TARGET) ./$(TARGET)

# Debug build
debug:
	$(CARGO) build
	@cp target/debug/$(TARGET) ./$(TARGET)

# Run the program
run: all
	./$(TARGET)

# Clean build artifacts
clean:
	$(CARGO) clean
	@rm -f $(TARGET)

# Show build configuration details
info:
	@echo "Target:         $(TARGET)"
	@echo "Cargo:          $(CARGO)"
	@echo "Rust compiler:  $(shell rustc --version)"

# Help message
help:
	@echo "Makefile usage for $(TARGET):"
	@echo "  make              Build release executable (default: ./$(TARGET))"
	@echo "  make debug        Build unoptimized debug binary"
	@echo "  make release      Build optimized release binary"
	@echo "  make run          Build and execute the program"
	@echo "  make clean        Remove all cargo artifacts and copied binary"
	@echo "  make info         Print Rust and Cargo version information"
	@echo "  make help         Show this help message"

