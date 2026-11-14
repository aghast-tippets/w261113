// panic.c: fault report (CMP-28), key wait and reboot (CMP-29).
// panic_handler runs once per process on the target (a second entry
// hangs on purpose), so every test runs it in a fresh child.
#include <cstring>

#include "fixtures.h"

using ::testing::_;

namespace e32 {
namespace {

panic_frame Frame(uint32_t kind, uint32_t cause) {
  panic_frame f;
  std::memset(&f, 0, sizeof f);
  f.kind = kind;
  f.exccause = cause;
  f.ps = 0x00060530;
  f.epc[0] = 0x400815db;   // EPC1
  f.depc = 0x40081000;
  f.a[0] = 0x80081658;     // return address of a call8
  for (int i = 1; i < 16; i++) f.a[i] = 0x11111111u * (i % 16);
  return f;
}

class PanicTest : public SimTest {
 protected:
  // Runs panic_handler; it ends by waiting for a key (none queued:
  // InputExhausted) or by rebooting (a key queued: Rebooted).
  void RunPanic(panic_frame& f) {
    try {
      panic_handler(&f);
      ADD_FAILURE() << "panic_handler returned";
    } catch (const InputExhausted&) {
    } catch (const Rebooted&) {
    }
  }
};

// Scenario CMP-28-S01 (Scenario Outline)
struct ReportRow { uint32_t kind, cause; const char* heading; const char* pc_line; };
class FaultReport : public PanicTest, public ::testing::WithParamInterface<ReportRow> {};

TEST_P(FaultReport, CMP_28_S01_T01_report_names_the_cause_and_the_registers) {
  const ReportRow& row = GetParam();
  E32_IN_FRESH_PROCESS({
    GIVEN("a panic frame of kind " + std::to_string(row.kind) + " with cause " +
          std::to_string(row.cause));
    panic_frame f = Frame(row.kind, row.cause);
    WHEN("panic_handler runs");
    RunPanic(f);
    THEN(std::string("the console shows \"") + row.heading + "\"");
    EXPECT_TRUE(ConsoleShows(std::string("\n") + row.heading + "\n")) << Console();
    AND(std::string("the console shows \"") + row.pc_line + "\"");
    EXPECT_TRUE(ConsoleShows(std::string("\n") + row.pc_line + "\n")) << Console();
    AND("the console shows the register lines, the caller and the reboot prompt");
    EXPECT_TRUE(ConsoleShows("a0  80081658  a1  11111111  a2  22222222  a3  33333333\n")) << Console();
    EXPECT_TRUE(ConsoleShows("called from ~40081658\n")) << Console();
    EXPECT_TRUE(ConsoleShows("Press any key to reboot\n")) << Console();
  });
}

INSTANTIATE_TEST_SUITE_P(
    Examples, FaultReport,
    ::testing::Values(
        ReportRow{1, 28, "*** Fatal exception 28: LoadProhibited",
                  "pc  400815db  ps  00060530  excvaddr 00000000"},
        ReportRow{1, 0, "*** Fatal exception 0: IllegalInstruction", "pc  400815db  ps  00060530"},
        ReportRow{1, 6, "*** Fatal exception 6: IntegerDivideByZero", "pc  400815db  ps  00060530"},
        ReportRow{2, 29, "*** Kernel exception 29: StoreProhibited",
                  "pc  400815db  ps  00060530  excvaddr 00000000"},
        ReportRow{3, 29, "*** Double exception (cause 29 while handling an exception at 400815db)",
                  "pc  40081000  ps  00060530  excvaddr 00000000"}),
    [](const ::testing::TestParamInfo<ReportRow>& i) { return "row" + std::to_string(i.index + 1); });

// Scenario CMP-28-S02
TEST_F(PanicTest, CMP_28_S02_T01_high_level_interrupt_reports_level_and_pending_lines) {
  E32_IN_FRESH_PROCESS({
    GIVEN("a panic frame of kind 19 (level 3) with EPC3 40082000 and EPS3 00060023");
    panic_frame f = Frame(0x13, 0);
    f.epc[2] = 0x40082000;
    f.eps[1] = 0x00060023;
    AND("the INTERRUPT register reads 20000000");
    sim.cpu.latched = 1u << 29;
    WHEN("panic_handler runs");
    RunPanic(f);
    THEN("the heading, the level line and the pc line are shown");
    EXPECT_TRUE(ConsoleShows("\n*** Unexpected high-level interrupt\n")) << Console();
    EXPECT_TRUE(ConsoleShows("\n    level 3, pending 20000000\n")) << Console();
    EXPECT_TRUE(ConsoleShows("\npc  40082000  ps  00060023\n")) << Console();
  });
}

// Scenario CMP-29-S02
TEST_F(PanicTest, CMP_29_S02_T01_key_press_after_the_report_reboots_the_chip) {
  E32_IN_FRESH_PROCESS({
    GIVEN("a panic frame of kind 1 with cause 0");
    panic_frame f = Frame(1, 0);
    AND("the UART will receive \"q\" after the report");
    sim.soc.Receive("q");
    WHEN("panic_handler runs");
    EXPECT_THROW(panic_handler(&f), Rebooted);
    THEN("80000000 is written to RTC_CNTL_OPTIONS0 at 3ff48000, and nothing after it");
    ASSERT_FALSE(sim.soc.writes.empty());
    EXPECT_EQ(sim.soc.writes.back(), std::make_pair(kRtcOptions0, 0x80000000u));
    AND("the key was consumed");
    EXPECT_TRUE(sim.soc.rx.empty());
  });
}

}  // namespace
}  // namespace e32
