// gpio.c: pad table, validity, direction and levels (CMP-21, CMP-22, CMP-23)
#include "fixtures.h"

using ::testing::_;
using ::testing::InSequence;
using ::testing::Return;

namespace e32 {
namespace {

constexpr uint32_t kOutW1ts = kGpioBase + 0x08, kOutW1tc = kGpioBase + 0x0c;
constexpr uint32_t kOut1W1ts = kGpioBase + 0x14, kOut1W1tc = kGpioBase + 0x18;
constexpr uint32_t kEnableW1ts = kGpioBase + 0x24, kEnable1W1tc = kGpioBase + 0x34;
constexpr uint32_t kGpioIn = kGpioBase + 0x3c, kGpioIn1 = kGpioBase + 0x40;
constexpr uint32_t GpioPin(int n) { return kGpioBase + 0x88 + 4 * n; }
constexpr uint32_t FuncOutSel(int n) { return kGpioBase + 0x530 + 4 * n; }
constexpr uint32_t kFunIe = 1 << 9;

class GpioTest : public SimTest {};

// Scenario CMP-21-S01 (docs/features/unit/gpio.feature): GPIO unit test
// against a fake register file.  T01 is the pytest-bdd binding.

TEST_F(GpioTest, CMP_21_S01_T02_flash_pin_is_refused_with_no_register_written) {
  GIVEN("gpio.c compiled for the host with a recording register bus");
  WHEN("I call gpio_dir_af(7, 1, 1, 0)");
  EXPECT_CALL(bus, Write(_, _)).Times(0);
  int r = gpio_dir_af(7, 1, 1, 0);
  THEN("it returns -1");
  EXPECT_EQ(r, -1);
}

TEST_F(GpioTest, CMP_21_S01_T03_gpio2_output_writes_registers_in_order) {
  GIVEN("gpio.c compiled for the host with a recording register bus");
  THEN("the writes are, in order: IO_MUX, GPIO_PIN2, FUNC2_OUT_SEL, OUT_W1TS, ENABLE_W1TS");
  {
    InSequence order;
    EXPECT_CALL(bus, Write((2 << 12) | kFunIe, 0x3ff49040));
    EXPECT_CALL(bus, Write(0, GpioPin(2)));
    EXPECT_CALL(bus, Write(0x500, FuncOutSel(2)));
    EXPECT_CALL(bus, Write(0x4, kOutW1ts));
    EXPECT_CALL(bus, Write(0x4, kEnableW1ts));
  }
  WHEN("I call gpio_dir_af(2, 1, 1, 0)");
  EXPECT_EQ(gpio_dir_af(2, 1, 1, 0), 0);
}

// Scenario CMP-21-S02 (docs/features/unit/gpio.feature)

struct PadRow { int gpio; uint32_t mux; };
class GpioPadTable : public GpioTest, public ::testing::WithParamInterface<PadRow> {};

TEST_P(GpioPadTable, CMP_21_S02_T01_pad_maps_to_its_io_mux_register) {
  const PadRow& row = GetParam();
  WHEN("gpio_dir_af(" + std::to_string(row.gpio) + ", input, AF0)");
  EXPECT_CALL(bus, Write((2 << 12) | kFunIe, row.mux)).Times(1);
  EXPECT_EQ(gpio_dir_af(row.gpio, 0, 0, 0), 0);
  THEN("its IO_MUX register is written with function 2 and input enabled");
}

INSTANTIATE_TEST_SUITE_P(
    Examples, GpioPadTable,
    ::testing::Values(PadRow{0, 0x3ff49044}, PadRow{2, 0x3ff49040}, PadRow{4, 0x3ff49048},
                      PadRow{12, 0x3ff49034}, PadRow{23, 0x3ff4908c}, PadRow{25, 0x3ff49024},
                      PadRow{33, 0x3ff49020}, PadRow{36, 0x3ff49004}, PadRow{39, 0x3ff49010}),
    [](const ::testing::TestParamInfo<PadRow>& i) { return "gpio" + std::to_string(i.param.gpio); });

// Scenario CMP-21-S03

struct RefusedRow { int gpio; int output; int af; };
class GpioRefused : public GpioTest, public ::testing::WithParamInterface<RefusedRow> {};

TEST_P(GpioRefused, CMP_21_S03_T01_invalid_pin_or_function_touches_no_register) {
  const RefusedRow& row = GetParam();
  EXPECT_CALL(bus, Write(_, _)).Times(0);
  EXPECT_CALL(bus, Read(_)).Times(0);
  WHEN("gpio_dir_af(" + std::to_string(row.gpio) + ", " + std::to_string(row.output) +
       ", 0, " + std::to_string(row.af) + ")");
  int r = gpio_dir_af(row.gpio, row.output, 0, row.af);
  THEN("it returns -1 and no register was written");
  EXPECT_EQ(r, -1);
}

INSTANTIATE_TEST_SUITE_P(
    Examples, GpioRefused,
    ::testing::Values(RefusedRow{-1, 0, 0}, RefusedRow{6, 0, 0}, RefusedRow{11, 1, 0},
                      RefusedRow{24, 0, 0}, RefusedRow{28, 0, 0}, RefusedRow{40, 0, 0},
                      RefusedRow{34, 1, 0}, RefusedRow{2, 0, 6}, RefusedRow{2, 0, -1}),
    [](const ::testing::TestParamInfo<RefusedRow>& i) {
      return "row" + std::to_string(i.index + 1);
    });

// Scenario CMP-21-S04

struct AfRow { int af; uint32_t value; };
class GpioAfSwap : public GpioTest, public ::testing::WithParamInterface<AfRow> {};

TEST_P(GpioAfSwap, CMP_21_S04_T01_alternate_functions_0_and_2_are_swapped) {
  const AfRow& row = GetParam();
  GIVEN("IO_MUX register 3ff49040 holds 00002b00");
  sim.soc.Poke(0x3ff49040, 0x00002b00);
  EXPECT_CALL(bus, Write(row.value, 0x3ff49040)).Times(1);
  WHEN("gpio_dir_af(2, input, AF" + std::to_string(row.af) + ")");
  EXPECT_EQ(gpio_dir_af(2, 0, 0, row.af), 0);
}

INSTANTIATE_TEST_SUITE_P(Examples, GpioAfSwap,
                         ::testing::Values(AfRow{0, 0x2b00}, AfRow{2, 0x0b00}, AfRow{3, 0x3b00}),
                         [](const ::testing::TestParamInfo<AfRow>& i) {
                           return "af" + std::to_string(i.param.af);
                         });

// Scenario CMP-22-S01

TEST_F(GpioTest, CMP_22_S01_T01_upper_port_input_clears_its_enable_bit) {
  WHEN("gpio_dir_af(35, input, AF0)");
  EXPECT_CALL(bus, Write(0x8, kEnable1W1tc)).Times(1);
  EXPECT_EQ(gpio_dir_af(35, 0, 0, 0), 0);
  THEN("00000008 is written to GPIO_ENABLE1_W1TC");
}

// Scenario CMP-23-S01

struct LevelRow { int gpio; int value; uint32_t bit; uint32_t reg; int level; };
class GpioLevels : public GpioTest, public ::testing::WithParamInterface<LevelRow> {};

TEST_P(GpioLevels, CMP_23_S01_T01_levels_are_set_cleared_and_read_on_both_ports) {
  const LevelRow& row = GetParam();
  GIVEN("GPIO_IN reads 00000010 and GPIO_IN1 reads 00000002");
  ON_CALL(bus, Read(kGpioIn)).WillByDefault(Return(0x10));
  ON_CALL(bus, Read(kGpioIn1)).WillByDefault(Return(0x2));
  WHEN("the firmware sets gpio " + std::to_string(row.gpio) + " to " + std::to_string(row.value));
  EXPECT_CALL(bus, Write(row.bit, row.reg)).Times(1);
  gpio_set(row.gpio, row.value);
  THEN("gpio_get reads the input register's bit");
  EXPECT_EQ(gpio_get(row.gpio), row.level);
}

INSTANTIATE_TEST_SUITE_P(
    Examples, GpioLevels,
    ::testing::Values(LevelRow{4, 1, 0x10, kOutW1ts, 1}, LevelRow{4, 0, 0x10, kOutW1tc, 1},
                      LevelRow{5, 1, 0x20, kOutW1ts, 0}, LevelRow{33, 1, 0x2, kOut1W1ts, 1},
                      LevelRow{33, 0, 0x2, kOut1W1tc, 1}),
    [](const ::testing::TestParamInfo<LevelRow>& i) { return "row" + std::to_string(i.index + 1); });

}  // namespace
}  // namespace e32
