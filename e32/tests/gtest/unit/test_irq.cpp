// irq.c: matrix, requests, dispatch (CMP-10, CMP-11, CMP-12)
#include <vector>

#include "fixtures.h"

using ::testing::_;
using ::testing::AnyNumber;

namespace e32 {
namespace {

class IrqTest : public SimTest {};

// Scenario CMP-10-S02
TEST_F(IrqTest, CMP_10_S02_T01_irq_init_routes_all_69_sources_to_line_6) {
  GIVEN("source 34 is routed to line 17 and INTENABLE is 00020040");
  sim.soc.Poke(IntrMap(34), 17);
  sim.cpu.intenable = 0x00020040;
  WHEN("the firmware calls irq_init");
  irq_init();
  THEN("all 69 sources from 3ff00104 to 3ff00214 are routed to line 6");
  for (int s = 0; s < 69; s++) EXPECT_EQ(sim.soc.Peek(IntrMap(s)), 6u) << "source " << s;
  EXPECT_EQ(IntrMap(68), 0x3ff00214u);
  EXPECT_EQ(sim.soc.writes.size(), 69u);
  AND("INTENABLE is 0 and INTCLEAR was written with ffffffff");
  EXPECT_EQ(sim.cpu.intenable, 0u);
  EXPECT_THAT(sim.cpu.intclear_writes, ::testing::Contains(0xffffffffu));
}

// Scenario CMP-10-S03
TEST_F(IrqTest, CMP_10_S03_T01_irq_map_writes_one_matrix_register) {
  EXPECT_CALL(bus, Write(_, _)).Times(0);
  EXPECT_CALL(bus, Write(0x11, 0x3ff0018c)).Times(1);
  WHEN("the firmware calls irq_map with source 34 and line 17");
  irq_map(34, 17);
  THEN("00000011 is written to 3ff0018c and nothing else is written");
}

// Scenario CMP-11-S02
struct RequestRow { int line; int result; uint32_t intenable; };
class IrqRequest : public IrqTest, public ::testing::WithParamInterface<RequestRow> {};

void NoOp(int, void*) {}

TEST_P(IrqRequest, CMP_11_S02_T01_only_level_1_lines_can_be_requested) {
  const RequestRow& row = GetParam();
  GIVEN("INTENABLE is 00000000");
  sim.cpu.intenable = 0;
  WHEN("irq_request(" + std::to_string(row.line) + ", handler, 0)");
  int r = irq_request(row.line, NoOp, nullptr);
  THEN("it returns " + std::to_string(row.result) + " and INTENABLE is as expected");
  EXPECT_EQ(r, row.result);
  EXPECT_EQ(sim.cpu.intenable, row.intenable);
  irq_disable(row.line >= 0 && row.line < 32 ? row.line : 0);  // leave line state clean
}

INSTANTIATE_TEST_SUITE_P(
    Examples, IrqRequest,
    ::testing::Values(RequestRow{0, 0, 0x1}, RequestRow{13, 0, 0x2000}, RequestRow{17, 0, 0x20000},
                      RequestRow{11, -1, 0}, RequestRow{19, -1, 0}, RequestRow{29, -1, 0},
                      RequestRow{32, -1, 0}, RequestRow{-1, -1, 0}),
    [](const ::testing::TestParamInfo<RequestRow>& i) {
      return i.param.line < 0 ? std::string("line_minus1") : "line" + std::to_string(i.param.line);
    });

// Scenario CMP-12-S02
std::vector<int>* g_order = nullptr;
void Record(int irq, void* arg) {
  g_order->push_back(irq);
  if (irq == 17) Sim::Current().soc.rx.clear();  // as uart_rx_irq drains the FIFO
}

TEST_F(IrqTest, CMP_12_S02_T01_pending_handlers_run_lowest_line_first_latched_cleared) {
  std::vector<int> order;
  g_order = &order;
  GIVEN("handlers are installed on lines 7 and 17");
  sim.cpu.intlevel = 3;  // keep them from running before both are pending
  ASSERT_EQ(irq_request(7, Record, nullptr), 0);
  ASSERT_EQ(irq_request(17, Record, nullptr), 0);
  uint32_t before7 = irq_count(7), before17 = irq_count(17);
  AND("lines 7 and 17 are both pending");
  sim.cpu.latched |= 1u << 7;
  sim.soc.Poke(IntrMap(34), 17);
  sim.soc.Poke(kUartIntEna, 1);
  sim.soc.Receive("x");
  WHEN("the CPU takes a level-1 interrupt");
  sim.cpu.intlevel = 0;
  sim.MaybeDispatch();
  THEN("the handler for line 7 runs before the handler for line 17");
  EXPECT_EQ(order, (std::vector<int>{7, 17}));
  AND("INTCLEAR was written with 00000080 and never with 00020000");
  EXPECT_THAT(sim.cpu.intclear_writes, ::testing::Contains(0x80u));
  EXPECT_THAT(sim.cpu.intclear_writes, ::testing::Not(::testing::Contains(0x20000u)));
  AND("irq_count reports one more interrupt on each line");
  EXPECT_EQ(irq_count(7), before7 + 1);
  EXPECT_EQ(irq_count(17), before17 + 1);
  irq_disable(7);
  irq_disable(17);
  g_order = nullptr;
}

// Scenario CMP-12-S03
TEST_F(IrqTest, CMP_12_S03_T01_pending_line_without_handler_is_disabled) {
  GIVEN("line 9 is enabled without a handler and pending");
  sim.cpu.intlevel = 3;
  irq_enable(9);
  sim.cpu.latched |= 1u << 9;  // raised, and held until something clears it
  WHEN("the CPU takes a level-1 interrupt");
  sim.cpu.intlevel = 0;
  sim.MaybeDispatch();
  THEN("the console shows \"irq 9: no handler, disabled\"");
  EXPECT_TRUE(ConsoleShows("irq 9: no handler, disabled\n")) << Console();
  AND("INTENABLE bit 9 is 0");
  EXPECT_EQ(sim.cpu.intenable & (1u << 9), 0u);
}

}  // namespace
}  // namespace e32
