# --- Compiler and Flags ---
CXX = g++
# C++ Standard
CPP_STD = -std=c++17
# Warning Flags (Recommended)
WARNING_FLAGS = -Wall -Wextra -Wpedantic
# Optimization Flags (-O2 is a good balance, -O3 potentially faster runtime but slower compile, -Og for debug)
OPT_FLAGS = -O2
# Standard Library Flag
STDLIB_FLAGS = -stdlib=libc++
# OpenMP Flag (if needed, keep it)
OMP_FLAGS = -fopenmp
# Linker Flags (can often be similar to compiler flags)
LDFLAGS = $(OMP_FLAGS) #  $(STDLIB_FLAGS)
# Aggregate CXX Flags
CXXFLAGS =  $(OMP_FLAGS) $(CPP_STD) $(OPT_FLAGS) # $(WARNING_FLAGS) $(STDLIB_FLAGS)
# Optional: Use a faster linker like lld (if installed)
# LDFLAGS += -fuse-ld=lld
# CXXFLAGS += -fuse-ld=lld

# --- Project Files ---
# Target executable name
TARGET = main

# Source Files (.cpp files needed for the TARGET executable)
SRCS = main.cpp lib/utils.cpp
# Add other .cpp files here if they are part of the main executable
# e.g. SRCS = main.cpp lib/utils.cpp lib/base.cpp lib/dijkstra.cpp

# Object files (automatically derive .o names from .cpp names)
OBJS = $(SRCS:.cpp=.o)

# Header files - Use wildcard to find all .hpp in lib, plus specific others if needed
# Changes to these headers will trigger recompilation of dependent .o files
HDRS = $(wildcard lib/*.hpp) # Finds all .hpp in lib/
# Add other specific headers if necessary: e.g. HDRS += path/to/other.hpp

# --- Build Rules ---

# Default target: Build the main executable
all: $(TARGET)

# Linking Rule: Create the final executable from object files
$(TARGET): $(OBJS)
	@echo "Linking $(TARGET)..."
	$(CXX) $(OBJS) -o $(TARGET) $(LDFLAGS)
	@echo "$(TARGET) built successfully."

# Compilation Rule (Pattern Rule): How to build any .o file from its .cpp file
# $< is the prerequisite (.cpp file), $@ is the target (.o file)
%.o: %.cpp $(HDRS) Makefile # Depend on source, headers, and the Makefile itself
	@echo "Compiling $<..."
	$(CXX) $(CXXFLAGS) -c $< -o $@

# --- Other Targets ---

# Clean Rule: Remove generated files
clean:
	@echo "Cleaning build files..."
	rm -f $(TARGET) $(OBJS) lib/*.o # Remove .o files potentially created in lib/
	@echo "Clean complete."

# Phony Targets: Targets that don't represent files
.PHONY: all clean

# Optional: Add rules for other executables if needed
# compare: misc/compare.cpp $(HDRS) Makefile
#	 $(CXX) $(CXXFLAGS) misc/compare.cpp $(wildcard lib/*.o) -o compare $(LDFLAGS) # Example: links with lib objects

# huawei: misc/huawei.cpp $(HDRS) Makefile
#	 $(CXX) $(CXXFLAGS) misc/huawei.cpp $(wildcard lib/*.o) -o huawei $(LDFLAGS) # Example: links with lib objects