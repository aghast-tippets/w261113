// End to end: the real firmware in Espressif's QEMU with the real boot ROM.
// Needs $QEMU (or qemu-system-xtensa on PATH) and flash.img, which
// `make flash.img` builds with the cross compiler.  Skipped otherwise.
#include <cerrno>
#include <chrono>
#include <csignal>
#include <cstdlib>
#include <cstring>
#include <fcntl.h>
#include <poll.h>
#include <regex>
#include <sys/stat.h>
#include <sys/wait.h>
#include <unistd.h>

#include <gtest/gtest.h>

#include "bdd.h"

namespace e32 {
namespace {

std::string FindQemu() {
  if (const char* q = std::getenv("QEMU")) return q;
  const char* path = std::getenv("PATH");
  std::string dirs = path ? path : "";
  size_t start = 0;
  while (start <= dirs.size()) {
    size_t end = dirs.find(':', start);
    std::string candidate = dirs.substr(start, end - start) + "/qemu-system-xtensa";
    if (access(candidate.c_str(), X_OK) == 0) return candidate;
    if (end == std::string::npos) break;
    start = end + 1;
  }
  return "";
}

// QEMU with the serial console on its stdin/stdout.
class QemuE2E : public ::testing::Test {
 protected:
  void SetUp() override {
    std::string qemu = FindQemu();
    std::string flash = std::string(E32_ROOT) + "/flash.img";
    struct stat st;
    if (qemu.empty()) GTEST_SKIP() << "QEMU not found: set QEMU or put qemu-system-xtensa on PATH";
    if (stat(flash.c_str(), &st) != 0)
      GTEST_SKIP() << "flash.img not built: run `make flash.img` (needs xtensa-esp32-elf-gcc)";

    int to_qemu[2], from_qemu[2];
    ASSERT_EQ(pipe(to_qemu), 0);
    ASSERT_EQ(pipe(from_qemu), 0);
    pid_ = fork();
    ASSERT_GE(pid_, 0);
    if (pid_ == 0) {
      dup2(to_qemu[0], 0);
      dup2(from_qemu[1], 1);
      dup2(from_qemu[1], 2);
      std::string drive = "file=" + flash + ",if=mtd,format=raw";
      execl(qemu.c_str(), qemu.c_str(), "-nographic", "-machine", "esp32", "-drive",
            drive.c_str(), "-serial", "stdio", "-monitor", "none", static_cast<char*>(nullptr));
      _exit(127);
    }
    close(to_qemu[0]);
    close(from_qemu[1]);
    in_ = to_qemu[1];
    out_ = from_qemu[0];
  }

  void TearDown() override {
    if (pid_ > 0) {
      kill(pid_, SIGTERM);
      waitpid(pid_, nullptr, 0);
    }
    if (in_ >= 0) close(in_);
    if (out_ >= 0) close(out_);
  }

  // Reads until `rx` matches the transcript (from `from`) or time runs out
  bool WaitFor(const std::string& rx, int seconds = 20) {
    auto deadline = std::chrono::steady_clock::now() + std::chrono::seconds(seconds);
    std::regex re(rx);
    while (true) {
      if (std::regex_search(transcript_.substr(from_), re)) return true;
      auto left = std::chrono::duration_cast<std::chrono::milliseconds>(
          deadline - std::chrono::steady_clock::now()).count();
      if (left <= 0) return false;
      pollfd p{out_, POLLIN, 0};
      if (poll(&p, 1, static_cast<int>(left)) <= 0) continue;
      char buf[1024];
      ssize_t n = read(out_, buf, sizeof buf);
      if (n <= 0) return false;
      transcript_.append(buf, static_cast<size_t>(n));
    }
  }

  void Enter(const std::string& line) {
    from_ = transcript_.size();
    std::string bytes = line + "\r";
    ASSERT_EQ(write(in_, bytes.data(), bytes.size()), static_cast<ssize_t>(bytes.size()));
  }

  std::string transcript_;
  size_t from_ = 0;
  pid_t pid_ = -1;
  int in_ = -1, out_ = -1;
};

// Scenario IF-03-S01 (docs/features/interface/console.feature): banner and prompt after boot
TEST_F(QemuE2E, IF_03_S01_T02_banner_and_prompt_after_flash_boot) {
  WHEN("the firmware is booted in QEMU from flash");
  THEN("the console shows the banner, the memory line and the prompt");
  EXPECT_TRUE(WaitFor(R"(e32: bare-metal ESP32, built \w{3} [ \d]\d \d{4} \d\d:\d\d:\d\d\r\n)"))
      << transcript_;
  EXPECT_TRUE(WaitFor(R"(bss 0x3ffb[0-9a-f]{4}-0x3ffb[0-9a-f]{4}, stack top 0x3ffdc000\r\n)"))
      << transcript_;
  EXPECT_TRUE(WaitFor(R"(mimmo\.c: Ready to get input \(h for help\)\r\n> )")) << transcript_;
}

// Scenario CMP-26-S01 (docs/features/unit/self_test.feature): self test passes after a flash boot
TEST_F(QemuE2E, CMP_26_S01_T02_self_test_passes_after_flash_boot) {
  GIVEN("the firmware is booted in QEMU from flash");
  ASSERT_TRUE(WaitFor("> ")) << transcript_;
  WHEN("I enter \"s\"");
  Enter("s");
  THEN("every check reports ok and the console shows \"all ok\"");
  ASSERT_TRUE(WaitFor(R"(all ok|FAILED)")) << transcript_;
  std::string reply = transcript_.substr(from_);
  for (const char* line : {"recursion 200 deep: 20100 (ok)", "VLA after spill:   919 (ok)",
                           "software irq:      1 hit (ok)", "all ok"})
    EXPECT_NE(reply.find(line), std::string::npos) << line << "\n" << reply;
  EXPECT_EQ(reply.find("BAD"), std::string::npos) << reply;
}

}  // namespace
}  // namespace e32
