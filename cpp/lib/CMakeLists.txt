# ZhC Core Library

# Collect source files
file(GLOB_RECURSE ZHC_SOURCES
  ${CMAKE_CURRENT_SOURCE_DIR}/*.cpp
)

# Define the zhc_core library
add_library(zhc_core STATIC ${ZHC_SOURCES})

target_include_directories(zhc_core PUBLIC
  ${CMAKE_CURRENT_SOURCE_DIR}/../include
  ${CMAKE_CURRENT_SOURCE_DIR}          # For TokenKinds.def
  ${LLVM_INCLUDE_DIRS}
)

target_compile_features(zhc_core PUBLIC cxx_std_20)

target_compile_options(zhc_core PRIVATE
  ${WARNING_FLAGS}
  ${SAN_FLAGS}
  ${COVERAGE_FLAGS}
)

target_link_options(zhc_core PUBLIC
  ${SAN_FLAGS}
  ${COVERAGE_FLAGS}
)

target_link_libraries(zhc_core PUBLIC ${LLVM_LIBS})

# Precompiled Headers for faster compilation
target_precompile_headers(zhc_core PRIVATE
  <vector>
  <string>
  <memory>
  <unordered_map>
  <cstdint>
  <zhc/Common.h>
)

# Set output properties
set_target_properties(zhc_core PROPERTIES
  ARCHIVE_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib
)