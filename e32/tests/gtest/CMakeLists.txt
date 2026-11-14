# GoogleTest / GoogleMock suite for e32: unit (TDD), scenario (BDD) and
# end-to-end tests, run on the build host.
#
#   cmake -S tests/gtest -B tests/gtest/build && cmake --build tests/gtest/build
#   tests/gtest/build/e32_tests                  # or: ctest --test-dir tests/gtest/build
#
#   -DE32_RED=ON   link empty stubs instead of the firmware and mkimage, to
#                  show every test fails for want of an implementation
cmake_minimum_required(VERSION 3.16)
project(e32_tests C CXX)

option(E32_RED "Build against empty stubs (Phase 3 red check)" OFF)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_C_STANDARD 11)

find_package(GTest REQUIRED)  # Debian/Ubuntu: libgtest-dev libgmock-dev

get_filename_component(E32_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/../.." ABSOLUTE)

# --- the firmware, compiled for the host -------------------------------
# Hardware access goes to tests/gtest/host (E32_HOST, see include/types.h).
# Names that clash with the host libc are renamed for the firmware only.
set(E32_FIRMWARE_RENAMES
    putc=e32_putc puts=e32_puts getc=e32_getc gets=e32_gets
    printf=pp_printf memset=e32_memset memcpy=e32_memcpy strlen=e32_strlen
    main=e32_main)

if(E32_RED)
  set(E32_FIRMWARE_SOURCES stubs/firmware_stubs.c)
  set(E32_MKIMAGE_SOURCE stubs/mkimage_stub.c)
else()
  set(E32_FIRMWARE_SOURCES
      ${E32_ROOT}/lib.c ${E32_ROOT}/pp_printf.c ${E32_ROOT}/gpio.c
      ${E32_ROOT}/wdt.c ${E32_ROOT}/irq.c ${E32_ROOT}/timer.c
      ${E32_ROOT}/io.c ${E32_ROOT}/mimmo.c ${E32_ROOT}/panic.c
      ${E32_ROOT}/main.c)
  set(E32_MKIMAGE_SOURCE ${E32_ROOT}/tools/mkimage.c)
endif()

add_library(e32_firmware_host STATIC ${E32_FIRMWARE_SOURCES})
target_include_directories(e32_firmware_host PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/host ${E32_ROOT}/include)
target_compile_definitions(e32_firmware_host PUBLIC E32_HOST)
target_compile_definitions(e32_firmware_host PRIVATE ${E32_FIRMWARE_RENAMES})
target_compile_options(e32_firmware_host PRIVATE
    -O1 -g -Wall -ffreestanding -fno-builtin
    -fno-tree-loop-distribute-patterns
    -fexceptions                  # the simulator throws through C frames
    -Wno-pointer-to-int-cast -Wno-int-to-pointer-cast)

# --- mkimage, the host tool under end-to-end test ----------------------
add_executable(mkimage ${E32_MKIMAGE_SOURCE})
target_compile_options(mkimage PRIVATE -O2 -Wall)

# --- the test binary ----------------------------------------------------
add_executable(e32_tests
    host/sim.cpp
    support/fixtures.cpp
    unit/test_lib.cpp
    unit/test_printf.cpp
    unit/test_gpio.cpp
    unit/test_wdt.cpp
    unit/test_irq.cpp
    unit/test_timer.cpp
    unit/test_io.cpp
    unit/test_mimmo.cpp
    unit/test_panic.cpp
    unit/test_main.cpp
    e2e/test_mkimage.cpp
    e2e/test_qemu.cpp)
target_include_directories(e32_tests PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/host ${CMAKE_CURRENT_SOURCE_DIR}/support)
target_compile_definitions(e32_tests PRIVATE
    E32_ROOT="${E32_ROOT}"
    E32_MKIMAGE="$<TARGET_FILE:mkimage>")
target_compile_options(e32_tests PRIVATE -Wall)
target_link_libraries(e32_tests PRIVATE
    e32_firmware_host GTest::gmock GTest::gtest_main)
add_dependencies(e32_tests mkimage)

include(GoogleTest)
enable_testing()
gtest_discover_tests(e32_tests DISCOVERY_TIMEOUT 30)
