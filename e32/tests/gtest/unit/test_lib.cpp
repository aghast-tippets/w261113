// lib.c: memset, memcpy, strlen (CMP-30) and udelay (CMP-31)
#include <cstring>

#include "fixtures.h"

namespace e32 {
namespace {

// Scenario CMP-30-S01 (docs/features/build.feature): the support library
// matches ISO C.  T01 is the pytest-bdd binding; these are T02..T04.

TEST(LibIsoC, CMP_30_S01_T02_memset_matches_iso_c_for_lengths_0_to_64) {
  GIVEN("lib.c compiled for the host with its functions renamed");
  for (unsigned n = 0; n <= 64; n++) {
    WHEN("memset fills " + std::to_string(n) + " bytes with 0x1a5 (stored as 0xa5)");
    unsigned char ours[80], theirs[80];
    std::memset(ours, 0x5a, sizeof ours);
    std::memset(theirs, 0x5a, sizeof theirs);
    void* r = e32_memset(ours + 3, 0x1a5, n);
    std::memset(theirs + 3, 0x1a5, n);
    THEN("the buffers are identical and the destination is returned");
    EXPECT_EQ(0, std::memcmp(ours, theirs, sizeof ours)) << "n=" << n;
    EXPECT_EQ(r, ours + 3);
  }
}

TEST(LibIsoC, CMP_30_S01_T03_memcpy_matches_iso_c_for_lengths_0_to_32_at_an_offset) {
  GIVEN("lib.c compiled for the host with its functions renamed");
  unsigned char src[40];
  for (unsigned i = 0; i < sizeof src; i++) src[i] = static_cast<unsigned char>(i * 7 + 1);
  for (unsigned n = 0; n <= 32; n++) {
    WHEN("memcpy copies " + std::to_string(n) + " bytes to an odd offset");
    unsigned char ours[48], theirs[48];
    std::memset(ours, 0, sizeof ours);
    std::memset(theirs, 0, sizeof theirs);
    void* r = e32_memcpy(ours + 5, src + 1, n);
    std::memcpy(theirs + 5, src + 1, n);
    THEN("the buffers are identical and the destination is returned");
    EXPECT_EQ(0, std::memcmp(ours, theirs, sizeof ours)) << "n=" << n;
    EXPECT_EQ(r, ours + 5);
  }
}

TEST(LibIsoC, CMP_30_S01_T04_strlen_matches_iso_c_for_4_strings) {
  GIVEN("lib.c compiled for the host with its functions renamed");
  for (const char* s : {"", "a", "mimmo.c: Ready", "0123456789abcdef0123456789abcdef"}) {
    WHEN(std::string("strlen(\"") + s + "\")");
    THEN("it equals the C library's strlen");
    EXPECT_EQ(e32_strlen(s), std::strlen(s));
  }
}

// Scenario CMP-31-S02 (docs/features/unit/gpio_lib_printf.feature)

class UdelayTest : public SimTest {};

TEST_F(UdelayTest, CMP_31_S02_T01_waits_40_cycles_per_microsecond_across_wraparound) {
  GIVEN("CCOUNT advances by 7 cycles on every read and starts at fffffff0");
  sim.cpu.ccount = 0xfffffff0u;
  sim.cpu.ccount_step = 7;
  WHEN("the firmware calls udelay with 25");
  udelay(25);
  THEN("CCOUNT has advanced by at least 1000 cycles and less than 1014");
  uint32_t elapsed = sim.cpu.ccount - 0xfffffff0u;
  EXPECT_GE(elapsed, 1000u);
  EXPECT_LT(elapsed, 1014u);
}

}  // namespace
}  // namespace e32
