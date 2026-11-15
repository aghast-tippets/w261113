// pp_printf.c: formatter core and the two entry points (CMP-19, CMP-20)
#include <cstdio>
#include <functional>

#include "fixtures.h"

namespace e32 {
namespace {

// Scenario CMP-19-S01 (docs/features/unit/printf.feature): pp_sprintf matches
// ISO C for the supported subset.  One test per Examples row; the row's
// format and arguments are applied to both pp_sprintf and snprintf.

struct FormatCase {
  const char* name;
  std::function<int(char*)> ours;    // pp_sprintf(buf, fmt, args...)
  std::function<int(char*)> theirs;  // snprintf(buf, 128, fmt, args...)
};

// The row's format goes to pp_sprintf as written; snprintf gets the
// host-C equivalent (identical except for the two rows noted below).
#define E32_FMT_CASE(fmt, iso_fmt, ...)                                 \
  FormatCase {                                                          \
    fmt, [](char* b) { return pp_sprintf(b, fmt, __VA_ARGS__); },       \
        [](char* b) { return std::snprintf(b, 128, iso_fmt, __VA_ARGS__); } \
  }

class PrintfIsoC : public ::testing::TestWithParam<FormatCase> {};

TEST_P(PrintfIsoC, CMP_19_S01_T02_pp_sprintf_matches_snprintf) {
  const FormatCase& c = GetParam();
  GIVEN("pp_printf.c compiled for the host");
  WHEN(std::string("I format ") + c.name);
  char ours[128] = {}, theirs[128] = {};
  int n_ours = c.ours(ours);
  int n_theirs = c.theirs(theirs);
  THEN("pp_sprintf produces the same string as snprintf");
  EXPECT_STREQ(ours, theirs);
  AND("it returns the same length");
  EXPECT_EQ(n_ours, n_theirs);
}

INSTANTIATE_TEST_SUITE_P(
    Examples, PrintfIsoC,
    ::testing::Values(
        E32_FMT_CASE("%d %i %u", "%d %i %u", -42, 0, 3000000000u),
        E32_FMT_CASE("%x %X %08x", "%x %X %08x", 0xdeadbeefu, 0xabcu, 0x12u),
        E32_FMT_CASE("%8x|%-8x|", "%8x|%-8x|", 0x12u, 0x12u),
        E32_FMT_CASE("%5d|%-5d|%05d|%-05d|", "%5d|%-5d|%05d|%-5d|", -3, -3, -3, -3),
        E32_FMT_CASE("%s|%10s|%-10s|", "%s|%10s|%-10s|", "hi", "hi", "hi"),
        E32_FMT_CASE("%c%%", "%c%%", 'z'),
        E32_FMT_CASE("%lu %ld %zu", "%u %d %u", 7u, -7, 9u),
        E32_FMT_CASE("%d", "%d", static_cast<int>(-2147483647 - 1)),
        E32_FMT_CASE("%u", "%u", 0u),
        E32_FMT_CASE("%-3c|", "%-3c|", 'a')),
    [](const ::testing::TestParamInfo<FormatCase>& info) {
      return "row" + std::to_string(info.index + 1);
    });

// Notes on the table above, kept honest:
// * "%-05d": ISO C ignores '0' when '-' is given; the host compiler warns
//   about the combination, so snprintf gets the equivalent "%-5d".
// * "%lu %ld %zu": on the 32-bit target long and size_t are 32 bits and
//   pp_printf ignores the modifiers; the host's 64-bit long would make the
//   same varargs undefined, so pp_sprintf gets them as written with int
//   arguments, and snprintf gets the target-equivalent "%u %d %u".

// Scenario SW-FMT-01-S01 (docs/features/software/printf.feature): cases that
// differ from or extend ISO C.

TEST(PrintfExtensions, SW_FMT_01_S01_T02_documented_differences_from_iso_c) {
  GIVEN("pp_printf.c compiled for the host");
  char buf[64];
  struct Row { const char* what; std::function<int()> run; const char* result; };
  Row rows[] = {
      {"%s with NULL", [&] { return pp_sprintf(buf, "%s", static_cast<char*>(nullptr)); }, "(null)"},
      {"%p with 0x3ffb0000", [&] { return pp_sprintf(buf, "%p", reinterpret_cast<void*>(0x3ffb0000)); }, "0x3ffb0000"},
      {"%p with 0x10", [&] { return pp_sprintf(buf, "%p", reinterpret_cast<void*>(0x10)); }, "0x00000010"},
      {"%q", [&] { return pp_sprintf(buf, "%q"); }, "q"},
      {"abc%", [&] { return pp_sprintf(buf, "abc%"); }, "abc"},
  };
  for (auto& row : rows) {
    WHEN(std::string("I format ") + row.what);
    int n = row.run();
    THEN(std::string("the result is \"") + row.result + "\"");
    EXPECT_STREQ(buf, row.result);
    EXPECT_EQ(n, static_cast<int>(std::string(row.result).size()));
  }
}

// Scenario CMP-20-S01 (docs/features/unit/printf.feature)

class PpPrintfTest : public SimTest {};

TEST_F(PpPrintfTest, CMP_20_S01_T01_sends_output_through_putc_and_returns_length) {
  WHEN("the firmware calls pp_printf with \"x=%d\\n\" and 42");
  int n = pp_printf("x=%d\n", 42);
  THEN("it returns 5");
  EXPECT_EQ(n, 5);
  AND("the UART transmits the bytes \"x=42\" 0d 0a");
  EXPECT_EQ(Hex(sim.Console()), Hex(Bytes("\"x=42\" 0d 0a")));
}

}  // namespace
}  // namespace e32
