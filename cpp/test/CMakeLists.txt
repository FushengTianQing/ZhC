# ZhC Tests

enable_testing()

# Collect test source files
file(GLOB_RECURSE TEST_SOURCES
  ${CMAKE_CURRENT_SOURCE_DIR}/unittests/*.cpp
  ${CMAKE_CURRENT_SOURCE_DIR}/integration/*.cpp
)

add_executable(zhc_tests ${TEST_SOURCES})

target_link_libraries(zhc_tests PRIVATE
  GTest::gtest_main
  zhc_core
)

target_compile_options(zhc_tests PRIVATE
  ${WARNING_FLAGS}
  ${SAN_FLAGS}
  ${COVERAGE_FLAGS}
)

target_link_options(zhc_tests PRIVATE
  ${SAN_FLAGS}
  ${COVERAGE_FLAGS}
)

target_include_directories(zhc_tests PRIVATE
  ${CMAKE_CURRENT_SOURCE_DIR}/../include
)

set_target_properties(zhc_tests PROPERTIES
  RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin
)

# Discover GoogleTest tests
include(GoogleTest)
gtest_discover_tests(zhc_tests)