// main.c (CMP-32)
#include "fixtures.h"

namespace e32 {
namespace {

class MainTest : public SimTest {};

// Scenario CMP-32-S02
TEST_F(MainTest, CMP_32_S02_T01_main_prints_banner_starts_interrupts_and_enters_monitor) {
  E32_IN_FRESH_PROCESS({
    WHEN("main runs until the monitor waits for input");
    EXPECT_THROW(e32_main(), InputExhausted);
    THEN("the banner and the memory line are shown");
    EXPECT_TRUE(ConsoleShows("\ne32: bare-metal ESP32, built ")) << Console();
    EXPECT_TRUE(ConsoleShows("\nbss 0x")) << Console();
    AND("the monitor announces itself");
    EXPECT_TRUE(ConsoleShows("mimmo.c: Ready to get input (h for help)\n> ")) << Console();
    AND("CPU lines 6 and 17 are enabled and UART0 is routed to line 17");
    EXPECT_EQ(sim.cpu.intenable & ((1u << 6) | (1u << 17)), (1u << 6) | (1u << 17));
    EXPECT_EQ(sim.soc.MatrixLine(34), 17u);
  });
}

}  // namespace
}  // namespace e32
