// End to end: tools/mkimage run as a process on crafted Xtensa ELF files
// (SW-IMG-01..05).  The Gherkin T01 bindings of these scenarios run
// against the real e32.elf, which needs the cross compiler; these tests
// need only the host compiler.
#include <cstdlib>
#include <numeric>
#include <unistd.h>

#include <gmock/gmock.h>
#include <gtest/gtest.h>

#include "bdd.h"
#include "process.h"

using ::testing::HasSubstr;

namespace e32 {
namespace {

class MkimageE2E : public ::testing::Test {
 protected:
  void SetUp() override {
    char tmpl[] = "/tmp/e32-mkimage-XXXXXX";
    ASSERT_NE(mkdtemp(tmpl), nullptr);
    dir_ = tmpl;
  }
  void TearDown() override { RunCommand({"rm", "-rf", dir_}); }

  std::string Path(const std::string& name) const { return dir_ + "/" + name; }

  RunResult Mkimage(const XtensaElf& elf, const std::string& name = "in.elf") {
    WriteFile(Path(name), elf.Bytes());
    return RunCommand({E32_MKIMAGE, Path(name), Path("out.bin")});
  }

  // A firmware-shaped ELF: DRAM data (odd length) then IRAM code
  static XtensaElf Firmware() {
    std::vector<uint8_t> dram(13), iram(40);
    std::iota(dram.begin(), dram.end(), 0x30);
    std::iota(iram.begin(), iram.end(), 0x80);
    return XtensaElf().Entry(0x40080300).Load(0x3ffb0000, dram).Load(0x40080000, iram);
  }

  std::string dir_;
};

// Scenario SW-IMG-01-S01 (docs/features/software/image.feature): invalid input is rejected
TEST_F(MkimageE2E, SW_IMG_01_S01_T02_invalid_input_is_rejected_with_exit_status_1) {
  struct Row { std::vector<std::string> args; const char* message; };
  const Row rows[] = {
      {{}, "use:"},
      {{std::string(E32_ROOT) + "/Makefile", Path("x.bin")}, "not a 32-bit LE Xtensa ELF"},
      {{E32_MKIMAGE, Path("x.bin")}, "not a 32-bit LE Xtensa ELF"},  // a host ELF
      {{"/nonexistent", Path("x.bin")}, "No such file or directory"},
  };
  for (const Row& row : rows) {
    std::vector<std::string> argv{E32_MKIMAGE};
    argv.insert(argv.end(), row.args.begin(), row.args.end());
    WHEN("I run mkimage with " + std::to_string(row.args.size()) + " argument(s)");
    RunResult r = RunCommand(argv);
    THEN(std::string("the exit status is 1 and the output contains \"") + row.message + "\"");
    EXPECT_EQ(r.exit_status, 1) << r.output;
    EXPECT_THAT(r.output, HasSubstr(row.message));
  }
}

// Scenario SW-IMG-03-S01 (docs/features/software/image.feature): unloadable ELF files are rejected
TEST_F(MkimageE2E, SW_IMG_03_S01_T02_unloadable_elf_files_are_rejected) {
  XtensaElf many;
  for (int i = 0; i < 17; i++) many.Load(0x3ffb0000 + 0x100 * i, {1, 2, 3, 4});
  XtensaElf none = XtensaElf().Other(XtensaElf::kPtLoad, 0x3ffc0000, {}, 0)  // bss only
                       .Other(XtensaElf::kPtNote, 0, {9, 9, 9, 9}, 4);
  XtensaElf truncated = XtensaElf().Other(XtensaElf::kPtLoad, 0x40080000, {1, 2, 3, 4}, 4096);
  struct Row { const char* file; const XtensaElf* elf; const char* message; };
  const Row rows[] = {{"many.elf", &many, "too many segments"},
                      {"none.elf", &none, "nothing to load"},
                      {"truncated.elf", &truncated, "past end of file"}};
  for (const Row& row : rows) {
    GIVEN(std::string("an Xtensa ELF file \"") + row.file + "\"");
    WHEN("I run mkimage on it");
    RunResult r = Mkimage(*row.elf, row.file);
    THEN(std::string("the exit status is 1 and the output contains \"") + row.message + "\"");
    EXPECT_EQ(r.exit_status, 1) << r.output;
    EXPECT_THAT(r.output, HasSubstr(row.message));
  }
}

// Scenario SW-IMG-04-S01 (docs/features/software/image.feature): header bytes are as specified
TEST_F(MkimageE2E, SW_IMG_04_S01_T02_header_bytes_are_as_specified) {
  GIVEN("a two-segment firmware ELF with entry 0x40080300");
  RunResult r = Mkimage(Firmware());
  ASSERT_EQ(r.exit_status, 0) << r.output;
  std::vector<uint8_t> img = ReadFile(Path("out.bin"));
  ASSERT_GE(img.size(), 24u);
  struct Row { int offset; uint8_t value; const char* meaning; };
  const Row rows[] = {{0, 0xe9, "magic"}, {1, 0x02, "segment count"}, {2, 0x02, "SPI mode DIO"},
                      {3, 0x20, "4 MB, 40 MHz"}, {8, 0xee, "WP pin disabled"},
                      {12, 0x00, "chip ID low byte"}, {17, 0xff, "max revision low byte"},
                      {18, 0xff, "max revision high byte"}, {23, 0x00, "no SHA-256 appended"}};
  for (const Row& row : rows) {
    WHEN("I read byte " + std::to_string(row.offset) + " (" + row.meaning + ")");
    EXPECT_EQ(img[row.offset], row.value) << row.meaning;
  }
  AND("bytes 4..7 hold the entry point");
  EXPECT_EQ(img[4] | img[5] << 8 | img[6] << 16 | static_cast<uint32_t>(img[7]) << 24, 0x40080300u);
}

// Scenario SW-IMG-05-S01 (docs/features/software/image.feature): the checksum is the last byte of
// a 16-byte block
TEST_F(MkimageE2E, SW_IMG_05_S01_T02_checksum_closes_a_16_byte_block) {
  GIVEN("a two-segment firmware ELF, the first segment 13 bytes long");
  XtensaElf elf = Firmware();
  RunResult r = Mkimage(elf);
  ASSERT_EQ(r.exit_status, 0) << r.output;
  std::vector<uint8_t> img = ReadFile(Path("out.bin"));
  THEN("the size of the image is a multiple of 16");
  EXPECT_EQ(img.size() % 16, 0u);
  AND("its last byte equals 0xef XOR every segment data byte");
  uint8_t sum = 0xef;
  for (int i = 0; i < 13; i++) sum ^= static_cast<uint8_t>(0x30 + i);
  for (int i = 0; i < 40; i++) sum ^= static_cast<uint8_t>(0x80 + i);
  ASSERT_FALSE(img.empty());
  EXPECT_EQ(img.back(), sum);
  AND("each segment is word-padded behind its address and padded length");
  ASSERT_GE(img.size(), 24u + 8 + 16 + 8 + 40);
  EXPECT_EQ(img[24] | img[25] << 8 | img[26] << 16 | static_cast<uint32_t>(img[27]) << 24, 0x3ffb0000u);
  EXPECT_EQ(img[28], 16);                      // 13 rounded up to a word
  EXPECT_EQ(img[32 + 12], 0x30 + 12);          // last data byte
  EXPECT_EQ(img[32 + 13], 0);                  // padding
}

}  // namespace
}  // namespace e32
