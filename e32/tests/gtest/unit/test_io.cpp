// io.c: putc/puts (CMP-15), getc/gets (CMP-16), receive interrupt
// (CMP-17) and serial_setup (CMP-18)
#include <algorithm>

#include "fixtures.h"

using ::testing::_;
using ::testing::InSequence;

namespace e32 {
namespace {

class IoTest : public SimTest {};

// Scenario CMP-15-S02
TEST_F(IoTest, CMP_15_S02_T01_newline_is_sent_as_cr_lf) {
  GIVEN("the UART transmit FIFO is empty");
  WHEN("the firmware calls puts with \"ok\\n\"");
  e32_puts("ok\n");
  THEN("the UART transmits the bytes 6f 6b 0d 0a");
  EXPECT_EQ(Hex(sim.Console()), "6f 6b 0d 0a");
}

// Scenario CMP-15-S03
TEST_F(IoTest, CMP_15_S03_T01_putc_waits_while_the_tx_fifo_is_nearly_full) {
  GIVEN("the UART transmit FIFO holds 126 bytes for the next 3 status reads");
  sim.soc.txcnt_script = {126, 126, 126};
  THEN("the status register is read 4 times before the FIFO write");
  {
    InSequence order;
    EXPECT_CALL(bus, Read(kUartStatus)).Times(4);
    EXPECT_CALL(bus, Write(0x41, kUartFifo)).Times(1);
  }
  WHEN("the firmware calls putc with \"A\"");
  e32_putc('A');
  AND("the UART transmits the byte 41");
  EXPECT_EQ(Hex(sim.Console()), "41");
}

// Scenario CMP-18-S02
TEST_F(IoTest, CMP_18_S02_T01_serial_setup_waits_for_the_rom_output_to_drain) {
  GIVEN("the UART transmit FIFO holds 5 bytes for the next 2 status reads");
  sim.soc.txcnt_script = {5, 5};
  WHEN("the firmware calls serial_setup");
  serial_setup();
  THEN("the status register was read 3 times");
  EXPECT_EQ(sim.soc.status_reads, 3);
  AND("no UART register was written");
  EXPECT_TRUE(sim.soc.WritesIn(kUart0, kUart0 + 0x100).empty());
}

// Scenario CMP-16-S02 (Scenario Outline: line editing in gets)
struct GetsRow { const char* input; int size; const char* line; const char* echo; };
class GetsEditing : public IoTest, public ::testing::WithParamInterface<GetsRow> {};

TEST_P(GetsEditing, CMP_16_S02_T01_line_editing_in_gets) {
  const GetsRow& row = GetParam();
  GIVEN(std::string("the UART receives the bytes ") + row.input);
  sim.soc.Receive(Bytes(row.input));
  WHEN("the firmware calls gets with a buffer of " + std::to_string(row.size) + " bytes");
  char buf[80];
  std::fill(std::begin(buf), std::end(buf), '#');
  int n = e32_gets(buf, row.size);
  THEN(std::string("the line read is \"") + row.line + "\"");
  EXPECT_STREQ(buf, row.line);
  EXPECT_EQ(n, static_cast<int>(std::string(row.line).size()));
  AND(std::string("the echo is ") + row.echo);
  EXPECT_EQ(Hex(sim.Console()), Hex(Bytes(row.echo)));
}

INSTANTIATE_TEST_SUITE_P(
    Examples, GetsEditing,
    ::testing::Values(
        GetsRow{"\"ab\" 0d", 80, "ab", "\"ab\" 0d 0a"},
        GetsRow{"\"ab\" 08 \"c\" 0d", 80, "ac", "\"ab\" 08 20 08 \"c\" 0d 0a"},
        GetsRow{"\"ab\" 7f 7f 7f \"c\" 0d", 80, "c", "\"ab\" 08 20 08 08 20 08 \"c\" 0d 0a"},
        GetsRow{"\"a\" 01 1b \"b\" 0a", 80, "ab", "\"ab\" 0d 0a"},
        GetsRow{"\"abcdef\" 0d", 4, "abc", "\"abc\" 0d 0a"}),
    [](const ::testing::TestParamInfo<GetsRow>& i) { return "row" + std::to_string(i.index + 1); });

// Interrupt mode can't be left once entered, so these run in a child.

// Scenario CMP-17-S02
TEST_F(IoTest, CMP_17_S02_T01_serial_irq_init_routes_uart0_to_a_cpu_line) {
  E32_IN_FRESH_PROCESS({
    WHEN("the firmware calls serial_irq_init with line 17");
    sim.soc.Poke(kUartConf1, 0x00007f60);
    serial_irq_init(17);
    THEN("UART_CONF1 has a receive threshold of 1 and its other bits kept");
    EXPECT_EQ(sim.soc.Peek(kUartConf1), 0x00007f01u);
    AND("UART_INT_CLR was written with ffffffff before UART_INT_ENA was written with 1");
    auto w = sim.soc.writes;
    auto clr = std::find(w.begin(), w.end(), std::make_pair(kUartIntClr, 0xffffffffu));
    auto ena = std::find(w.begin(), w.end(), std::make_pair(kUartIntEna, 1u));
    EXPECT_TRUE(clr != w.end() && ena != w.end() && clr < ena);
    AND("interrupt matrix source 34 is routed to line 17");
    EXPECT_EQ(sim.soc.MatrixLine(34), 17u);
    AND("CPU line 17 is enabled");
    EXPECT_NE(sim.cpu.intenable & (1u << 17), 0u);
  });
}

// Scenario CMP-16-S03
TEST_F(IoTest, CMP_16_S03_T01_getc_sleeps_until_the_uart_interrupt_brings_a_byte) {
  E32_IN_FRESH_PROCESS({
    GIVEN("serial_irq_init was called with line 17");
    serial_irq_init(17);
    uint32_t before = irq_count(17);
    AND("the UART receives \"x\" while the CPU is waiting for an interrupt");
    bool sent = false;
    sim.cpu.on_idle = [&] {
      if (sent) return false;
      sim.soc.Receive("x");
      return sent = true;
    };
    WHEN("the firmware calls getc");
    int c = e32_getc();
    THEN("it returns \"x\"");
    EXPECT_EQ(c, 'x');
    AND("the CPU executed waiti at least once");
    EXPECT_GE(sim.cpu.waiti_count, 1);
    AND("interrupt line 17 was dispatched once");
    EXPECT_EQ(irq_count(17), before + 1);
  });
}

// Scenario CMP-17-S03
TEST_F(IoTest, CMP_17_S03_T01_bytes_beyond_the_256_byte_ring_are_dropped) {
  E32_IN_FRESH_PROCESS({
    GIVEN("serial_irq_init was called with line 17");
    serial_irq_init(17);
    WHEN("300 bytes arrive before the firmware reads any");
    std::string burst;
    for (int i = 0; i < 300; i++) burst.push_back(static_cast<char>(i & 0xff));
    sim.soc.Receive(burst);
    THEN("the next 256 calls to getc return the first 256 bytes in order");
    for (int i = 0; i < 256; i++) ASSERT_EQ(e32_getc(), i) << "call " << i + 1;
    AND("the 257th call to getc waits for new input instead of returning a dropped byte");
    EXPECT_THROW(e32_getc(), InputExhausted);
  });
}

}  // namespace
}  // namespace e32
