cmake_minimum_required(VERSION 3.14)
project(hft_ingestion LANGUAGES CXX)

# Set C++ standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Optimization flags for HFT performance
set(CMAKE_CXX_FLAGS_RELEASE "-O3 -DNDEBUG -march=native -mtune=native")
set(CMAKE_CXX_FLAGS_DEBUG "-g -O0 -Wall -Wextra")

# Default to Release build if not specified
if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release)
endif()

# Include directories
include_directories(${CMAKE_CURRENT_SOURCE_DIR})

# Source files
set(SOURCES
    message_parser.cpp
)

# Headers
set(HEADERS
    message_types.hpp
    message_parser.hpp
)

# Create static library for the parser
add_library(hft_ingestion_static STATIC ${SOURCES} ${HEADERS})

# Create shared library for Python bindings
add_library(hft_ingestion_shared SHARED ${SOURCES} ${HEADERS})

# Set properties for shared library
set_target_properties(hft_ingestion_shared PROPERTIES
    VERSION 1.0
    SOVERSION 1
    OUTPUT_NAME hft_ingestion
)

# Find and link pybind11 for Python bindings (optional)
find_package(pybind11 QUIET)
if(pybind11_FOUND)
    pybind11_add_module(hft_ingestion_py 
        python_bindings.cpp
        ${SOURCES}
    )
    
    target_compile_definitions(hft_ingestion_py PRIVATE VERSION_INFO=${EXAMPLE_VERSION_INFO})
    target_compile_features(hft_ingestion_py PRIVATE cxx_std_17)
endif()

# Create test executable
add_executable(parser_test test_parser.cpp)
target_link_libraries(parser_test hft_ingestion_static)

# Installation rules
install(TARGETS hft_ingestion_static hft_ingestion_shared
    LIBRARY DESTINATION lib
    ARCHIVE DESTINATION lib
    RUNTIME DESTINATION bin
)

install(FILES ${HEADERS} DESTINATION include/hft/ingestion)

# Performance testing executable
add_executable(parser_benchmark benchmark_parser.cpp)
target_link_libraries(parser_benchmark hft_ingestion_static)

# Compiler-specific optimizations
if(CMAKE_CXX_COMPILER_ID STREQUAL "GNU")
    target_compile_options(hft_ingestion_static PRIVATE 
        -ffast-math 
        -funroll-loops 
        -finline-functions
    )
    target_compile_options(hft_ingestion_shared PRIVATE 
        -ffast-math 
        -funroll-loops 
        -finline-functions
    )
elseif(CMAKE_CXX_COMPILER_ID STREQUAL "Clang")
    target_compile_options(hft_ingestion_static PRIVATE 
        -ffast-math 
        -funroll-loops
    )
    target_compile_options(hft_ingestion_shared PRIVATE 
        -ffast-math 
        -funroll-loops
    )
endif()

# Enable testing
enable_testing()
add_test(NAME parser_unit_tests COMMAND parser_test) 