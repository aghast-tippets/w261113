// fixtures.h -- shared GoogleTest fixtures and helpers for the e32 suite.
#ifndef E32_TESTS_FIXTURES_H
#define E32_TESTS_FIXTURES_H

#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <string>
#include <vector>

#include <gmock/gmock.h>
#include <gtest/gtest-spi.h>
#include <gtest/gtest.h>

#include "bdd.h"
#include "firmware.h"
#include "sim.h"

namespace e32 {

// A fresh simulated SoC per test, with a NiceMock bus in front of it.
// Accesses without an expectation go straight to the FakeSoc, so tests
// only spell out the accesses they care about.
class SimTest : public ::testing::Test {
 protected:
  void SetUp() override {
    bus.DelegateTo(sim.soc);
    sim.bus = &bus;
    // Baseline: any access is allowed.  A test's own EXPECT_CALLs are
    // newer, so gmock matches them first; without this baseline, every
    // access a test did not name would count as an unexpected call.
    EXPECT_CALL(bus, Read(::testing::_)).Times(::testing::AnyNumber());
    EXPECT_CALL(bus, Write(::testing::_, ::testing::_)).Times(::testing::AnyNumber());
  }

  // Console output with CR LF folded to LF
  std::string Console() const {
    std::string out;
    for (char c : sim.Console())
      if (c != '\r') out.push_back(c);
    return out;
  }

  bool ConsoleShows(const std::string& text) const {
    return Console().find(text) != std::string::npos;
  }

  Sim sim;
  ::testing::NiceMock<MockBus> bus;
};

// The monitor driven through its console: queue input lines, run mimmo()
// until it waits for more input, then look at what it printed.
class MonitorTest : public SimTest {
 protected:
  void Enter(const std::string& line) { sim.soc.Receive(line + "\r"); }

  // Runs the command loop until the simulated UART runs dry
  void RunMonitor() { EXPECT_THROW(mimmo(), InputExhausted); }

  // Output lines, without prompts and without the echo of typed lines
  std::vector<std::string> Replies() const;
};

// Bytes written as in the .feature files: "text" 0d 0a ...
std::string Bytes(const std::string& spec);
// Hex dump "6f 6b 0d 0a" of a byte string, for readable failures
std::string Hex(const std::string& bytes);

}  // namespace e32

namespace e32 {

// Runs `body` in the (forked) child of a death test: collects its
// failures, prints them on stderr for the parent's report, and exits
// with 1 if there were any, 0 otherwise.
template <class Body>
[[noreturn]] void RunAndExit(Body body, void* mock) {
  ::testing::TestPartResultArray results;
  {
    ::testing::ScopedFakeTestPartResultReporter reporter(
        ::testing::ScopedFakeTestPartResultReporter::INTERCEPT_ONLY_CURRENT_THREAD, &results);
    body();
    ::testing::Mock::VerifyAndClearExpectations(mock);
  }
  int failed = 0;
  for (int i = 0; i < results.size(); i++) {
    const ::testing::TestPartResult& r = results.GetTestPartResult(i);
    if (!r.failed()) continue;
    failed++;
    std::fprintf(stderr, "%s:%d: Failure\n%s\n", r.file_name() ? r.file_name() : "?",
                 r.line_number(), r.message());
  }
  std::fflush(stderr);
  std::_Exit(failed ? 1 : 0);
}

}  // namespace e32

// Some firmware state only moves one way (serial_irq_init sets interrupt
// mode for good, panic_handler never returns), so tests that touch it run
// their body in a forked child: a fresh copy of every static.  The
// child's failures are reported through the parent's EXPECT_EXIT.
#define E32_IN_FRESH_PROCESS(...)                                             \
  EXPECT_EXIT(::e32::RunAndExit([&] { __VA_ARGS__; }, &bus),                  \
              ::testing::ExitedWithCode(0), "")

#endif  // E32_TESTS_FIXTURES_H
