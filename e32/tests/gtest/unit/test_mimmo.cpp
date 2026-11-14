// mimmo.c: number parsing (CMP-24), command loop (CMP-25), self test (CMP-26)
#include <algorithm>

#include "fixtures.h"

using ::testing::Return;

namespace e32 {
namespace {

// Scenario CMP-24-S02 (Scenario Outline: numbers are parsed strictly)
struct ParseRow { const char* line; const char* reply; };
class NumberParsing : public MonitorTest, public ::testing::WithParamInterface<ParseRow> {};

TEST_P(NumberParsing, CMP_24_S02_T01_numbers_are_parsed_strictly) {
  const ParseRow& row = GetParam();
  GIVEN("memory word 3ffb1000 holds 0000cafe");
  sim.soc.Poke(0x3ffb1000, 0xcafe);
  WHEN(std::string("the operator enters \"") + row.line + "\"");
  Enter(row.line);
  RunMonitor();
  THEN(std::string("the console shows \"") + row.reply + "\"");
  auto replies = Replies();
  ASSERT_FALSE(replies.empty()) << Console();
  EXPECT_EQ(replies.front(), row.reply) << Console();
}

INSTANTIATE_TEST_SUITE_P(
    Examples, NumberParsing,
    ::testing::Values(ParseRow{"r 3ffb1000", "read 3ffb1000"},
                      ParseRow{"r 0x3ffb1000", "read 3ffb1000"},
                      ParseRow{"r 0X3FFB1000", "read 3ffb1000"},
                      ParseRow{"r   3ffb1000", "read 3ffb1000"},
                      ParseRow{"r 3ffb100g", "?? (h for help)"},
                      ParseRow{"r 0x", "?? (h for help)"},
                      ParseRow{"r 3ffb1000x", "?? (h for help)"},
                      ParseRow{"p 1a", "?? (h for help)"},
                      ParseRow{"p 0x2", "?? (h for help)"}),
    [](const ::testing::TestParamInfo<ParseRow>& i) { return "row" + std::to_string(i.index + 1); });

// Scenario CMP-25-S01
TEST_F(MonitorTest, CMP_25_S01_T01_read_write_and_dump_answer_in_documented_formats) {
  GIVEN("memory words 3ffb2000 to 3ffb201c hold 00000000 to 00000007");
  for (uint32_t i = 0; i < 8; i++) sim.soc.Poke(0x3ffb2000 + 4 * i, i);
  WHEN("the operator enters \"w 3ffb2000 cafe\", \"r 3ffb2000\" and \"d 3ffb2000 8\"");
  Enter("w 3ffb2000 cafe");
  Enter("r 3ffb2000");
  Enter("d 3ffb2000 8");
  RunMonitor();
  THEN("the console shows exactly the documented replies");
  EXPECT_THAT(Replies(), ::testing::ElementsAre(
                             "write 3ffb2000 = 0000cafe",
                             "read 3ffb2000",
                             "0000cafe",
                             "3ffb2000: 0000cafe 00000001 00000002 00000003",
                             "3ffb2010: 00000004 00000005 00000006 00000007"))
      << Console();
}

// Scenario CMP-25-S02 (Scenario Outline: GPIO commands report their outcome)
struct GpioCmdRow { const char* line; const char* reply; };
class GpioCommands : public MonitorTest, public ::testing::WithParamInterface<GpioCmdRow> {};

TEST_P(GpioCommands, CMP_25_S02_T01_gpio_commands_report_their_outcome) {
  const GpioCmdRow& row = GetParam();
  GIVEN("GPIO_IN reads 00000010");
  ON_CALL(bus, Read(kGpioBase + 0x3c)).WillByDefault(Return(0x10));
  WHEN(std::string("the operator enters \"") + row.line + "\"");
  Enter(row.line);
  RunMonitor();
  THEN(std::string("the console shows \"") + row.reply + "\"");
  EXPECT_THAT(Replies(), ::testing::ElementsAre(row.reply)) << Console();
}

INSTANTIATE_TEST_SUITE_P(
    Examples, GpioCommands,
    ::testing::Values(
        GpioCmdRow{"p 2 1", "gpio 2 <- 1"}, GpioCmdRow{"p 2 5", "gpio 2 <- 1"},
        GpioCmdRow{"p 4", "gpio 4 = 1"}, GpioCmdRow{"p 5", "gpio 5 = 0"},
        GpioCmdRow{"p 7 1", "invalid gpio (6..11 are flash, 34..39 are input only)"},
        GpioCmdRow{"a 2 3", "gpio 2: function 3"}, GpioCmdRow{"a 2 6", "invalid gpio or function"}),
    [](const ::testing::TestParamInfo<GpioCmdRow>& i) { return "row" + std::to_string(i.index + 1); });

// Scenario CMP-25-S03
TEST_F(MonitorTest, CMP_25_S03_T01_prompt_before_every_read_and_blank_lines_ignored) {
  WHEN("the operator enters \"\", \"   \" and \"h\"");
  Enter("");
  Enter("   ");
  Enter("h");
  RunMonitor();
  THEN("the console shows the prompt \"> \" 4 times");
  const std::string out = Console();
  size_t prompts = 0;
  // The help text contains "> " too ("<addr> "), so count line starts only
  for (size_t at = out.find("\n> "); at != std::string::npos; at = out.find("\n> ", at + 1))
    prompts++;
  EXPECT_EQ(prompts, 4u) << out;
  AND("the console does not show \"??\"");
  EXPECT_EQ(out.find("??"), std::string::npos) << out;
  AND("the console shows the help line for h");
  EXPECT_TRUE(ConsoleShows("h                     this help")) << out;
}

// Scenario CMP-26-S02
TEST_F(MonitorTest, CMP_26_S02_T01_self_test_passes_on_the_simulated_cpu) {
  GIVEN("the 100 Hz tick is running");
  sim.cpu.ccount_step = 101;
  timer_init(100);
  WHEN("the operator enters \"s\"");
  Enter("s");
  RunMonitor();
  THEN("every check reports ok and the summary is \"all ok\"");
  for (const char* line : {"recursion 200 deep: 20100 (ok)", "VLA after spill:   919 (ok)",
                           "software irq:      1 hit (ok)", "all ok"})
    EXPECT_TRUE(ConsoleShows(line)) << "missing \"" << line << "\" in:\n" << Console();
  EXPECT_FALSE(ConsoleShows("BAD")) << Console();
  AND("CPU line 7 is disabled afterwards");
  EXPECT_EQ(sim.cpu.intenable & (1u << 7), 0u);
  irq_disable(6);
}

}  // namespace
}  // namespace e32
