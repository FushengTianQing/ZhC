cmake_minimum_required(VERSION 3.20)
project(ZhC LANGUAGES C CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

#===-----------------------------------------------------------------------===#
# LLVM Configuration
#===-----------------------------------------------------------------------===#
# Use LLVM 20 (latest stable, installed via Homebrew)
# Note: Exclude lldb which requires libedit (not available on macOS)
find_package(LLVM REQUIRED CONFIG)

message(STATUS "Found LLVM ${LLVM_PACKAGE_VERSION}")
message(STATUS "Using LLVMConfig.cmake in: ${LLVM_DIR}")

include_directories(${LLVM_INCLUDE_DIRS})
separate_arguments(LLVM_DEFINITIONS_LIST NATIVE_COMMAND ${LLVM_DEFINITIONS})
add_definitions(${LLVM_DEFINITIONS_LIST})
link_directories(${LLVM_LIBRARY_DIRS})

# Determine LLVM link components (exclude lldb which needs libedit)
llvm_map_components_to_libnames(LLVM_LIBS
  core
  support
  mcparser
  mc
  bitreader
  bitwriter
  irreader
  target
  native
)

#===-----------------------------------------------------------------------===#
# Build Options
#===-----------------------------------------------------------------------===#
option(ENABLE_ASAN "Enable AddressSanitizer" OFF)
option(ENABLE_USAN "Enable UndefinedBehaviorSanitizer" OFF)
option(ENABLE_TSAN "Enable ThreadSanitizer" OFF)
option(ENABLE_COVERAGE "Enable code coverage" OFF)
option(ENABLE_TESTS "Enable tests" ON)

#===-----------------------------------------------------------------------===#
# Sanitizer Configuration
#===-----------------------------------------------------------------------===#
set(SAN_FLAGS "")
if(ENABLE_ASAN)
  list(APPEND SAN_FLAGS -fsanitize=address -fno-omit-frame-pointer)
  message(STATUS "AddressSanitizer enabled")
endif()
if(ENABLE_USAN)
  list(APPEND SAN_FLAGS -fsanitize=undefined)
  message(STATUS "UndefinedBehaviorSanitizer enabled")
endif()
if(ENABLE_TSAN)
  list(APPEND SAN_FLAGS -fsanitize=thread)
  message(STATUS "ThreadSanitizer enabled")
endif()

#===-----------------------------------------------------------------------===#
# Coverage Configuration
#===-----------------------------------------------------------------------===#
if(ENABLE_COVERAGE)
  set(COVERAGE_FLAGS --coverage -O0 -g)
  message(STATUS "Code coverage enabled")
else()
  set(COVERAGE_FLAGS "")
endif()

#===-----------------------------------------------------------------------===#
# Compiler Warning Flags
#===-----------------------------------------------------------------------===#
if(CMAKE_CXX_COMPILER_ID MATCHES "Clang|GNU")
  set(WARNING_FLAGS
    -Wall -Wextra -Wpedantic
    -Wno-unused-parameter
    -Wno-missing-field-initializers
    -Werror=return-type
  )
endif()

#===-----------------------------------------------------------------------===#
# Core Library
#===-----------------------------------------------------------------------===#
add_subdirectory(lib)

#===-----------------------------------------------------------------------===#
# Compiler Driver (tools/zhc)
#===-----------------------------------------------------------------------===#
add_subdirectory(tools/zhc)

#===-----------------------------------------------------------------------===#
# Tests
#===-----------------------------------------------------------------------===#
if(ENABLE_TESTS)
  include(CTest)
  include(FetchContent)
  
  # GoogleTest via FetchContent
  FetchContent_Declare(
    googletest
    GIT_REPOSITORY https://github.com/google/googletest.git
    GIT_TAG v1.14.0
  )
  set(gtest_force_shared_crt ON CACHE BOOL "" FORCE)
  FetchContent_MakeAvailable(googletest)
  
  add_subdirectory(test)
endif()