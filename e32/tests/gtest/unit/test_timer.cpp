// timer.c (CMP-13) and udelay against the tick (CMP-31)
#include "fixtures.h"

namespace e32 {
namespace {

class TimerTest : public SimTest {
 protected:
  void TearDown() override { irq_disable(6); }
};

// Scenario CMP-13-S02
TEST_F(TimerTest, CMP_13_S02_T01_timer_init_programs_compare_one_period_ahead) {
  GIVEN("CCOUNT is 1000");
  sim.cpu.ccount = 1000;
  sim.cpu.ccount_step = 1;
  WHEN("the firmware calls timer_init with 100");
  timer_init(100);
  THEN("CCOMPARE0 is 401000 plus the cycles that elapsed while reading CCOUNT");
  EXPECT_EQ(sim.cpu.ccompare0, 1000u + 400000u);  // CCOUNT was read once, at 1000
  AND("CPU line 6 is enabled");
  EXPECT_NE(sim.cpu.intenable & (1u << 6), 0u);
}

// Scenario CMP-13-S03 (regression: a compare value behind CCOUNT stalled the tick)
TEST_F(TimerTest, CMP_13_S03_T01_tick_catches_up_when_ccount_passed_the_compare) {
  GIVEN("timer_init was called with 100 and jiffies is 0");
  sim.cpu.intlevel = 3;
  timer_init(100);
  jiffies = 0;
  uint32_t last = sim.cpu.ccompare0;
  AND("CCOUNT has advanced 3 periods and 10 cycles past the last compare value");
  sim.cpu.ccount = last + 3 * 400000 + 10;
  sim.cpu.timer_pending = true;
  WHEN("the CPU takes the timer interrupt");
  sim.cpu.intlevel = 0;
  sim.MaybeDispatch();
  THEN("jiffies is 4");
  EXPECT_EQ(u32{jiffies}, 4u);
  AND("CCOMPARE0 is ahead of CCOUNT");
  EXPECT_GT(static_cast<int32_t>(sim.cpu.ccompare0 - sim.cpu.ccount), 0);
}

// Scenario CMP-13-S04
TEST_F(TimerTest, CMP_13_S04_T01_about_ten_ticks_elapse_during_a_100ms_delay) {
  GIVEN("timer_init was called with 100 and jiffies is 0");
  sim.cpu.ccount_step = 97;  // any small step: CCOUNT runs while the loop spins
  timer_init(100);
  jiffies = 0;
  WHEN("the firmware calls udelay with 100000");
  udelay(100000);
  THEN("jiffies is between 9 and 11");
  EXPECT_GE(u32{jiffies}, 9u);
  EXPECT_LE(u32{jiffies}, 11u);
}

}  // namespace
}  // namespace e32
