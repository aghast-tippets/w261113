// wdt.c (CMP-14)
#include "fixtures.h"

using ::testing::_;
using ::testing::InSequence;

namespace e32 {
namespace {

class WdtTest : public SimTest {};

// Scenario CMP-14-S02 (unit/irq_timer_wdt.feature)
TEST_F(WdtTest, CMP_14_S02_T01_unlocks_clears_and_relocks_the_three_watchdogs_in_order) {
  constexpr uint32_t kKey = 0x50d83aa1;
  struct Wdt { uint32_t wprotect, config0; };
  const Wdt order_of_watchdogs[] = {
      {0x3ff480a4, 0x3ff4808c},   // RTC
      {0x3ff5f064, 0x3ff5f048},   // TIMG0
      {0x3ff60064, 0x3ff60048},   // TIMG1
  };
  THEN("the register writes are, in order: RTC, TIMG0, TIMG1 (unlock, off, lock)");
  // gmock tries the newest expectation first: this catch-all only sees
  // writes that none of the expected ones below match.
  EXPECT_CALL(bus, Write(_, _)).Times(0);
  {
    InSequence order;
    for (const Wdt& w : order_of_watchdogs) {
      EXPECT_CALL(bus, Write(kKey, w.wprotect));
      EXPECT_CALL(bus, Write(0, w.config0));
      EXPECT_CALL(bus, Write(0, w.wprotect));
    }
  }
  WHEN("the firmware calls wdt_disable");
  wdt_disable();
}

}  // namespace
}  // namespace e32
