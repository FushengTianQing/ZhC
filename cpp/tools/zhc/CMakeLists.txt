# ZhC Compiler Driver

add_executable(zhc main.cpp)

target_link_libraries(zhc PRIVATE zhc_core)

target_compile_options(zhc PRIVATE
  ${WARNING_FLAGS}
  ${SAN_FLAGS}
  ${COVERAGE_FLAGS}
)

target_link_options(zhc PRIVATE
  ${SAN_FLAGS}
  ${COVERAGE_FLAGS}
)

set_target_properties(zhc PROPERTIES
  RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin
)