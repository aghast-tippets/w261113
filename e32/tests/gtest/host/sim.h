// sim.h -- the simulated ESP32 that the host-compiled firmware runs on.
//
// The firmware's readl/writel/RSR/WSR/irq_save/waiti calls (see
// e32_host.h) land on the Sim installed by the current test.  A Sim is a
// FakeSoc (memory, UART0, interrupt matrix, RTC reset) behind a Bus
// pointer, plus a small model of the LX6 interrupt logic: CCOUNT,
// CCOMPARE0, INTENABLE, latched lines, PS.INTLEVEL and level-1 dispatch.
//
// Tests can put a gmock MockBus in front of the FakeSoc to set
// expectations on individual register accesses.
#ifndef E32_TESTS_SIM_H
#define E32_TESTS_SIM_H

#include <cstdint>
#include <deque>
#include <functional>
#include <map>
#include <string>
#include <utility>
#include <vector>

#include <gmock/gmock.h>

namespace e32 {

// Thrown through the firmware (compiled with -fexceptions) to end loops
// that never return on the target.
struct InputExhausted {};          // waiti with nothing left to happen
struct Rebooted {};                // RTC_CNTL_OPTIONS0.SW_SYS_RST written
struct Trapped { std::string what; };  // ill / break / bad sp

// Register addresses the tests talk about (from include/regs.h)
constexpr uint32_t kUart0 = 0x3ff40000;
constexpr uint32_t kUartFifo = kUart0 + 0x00;
constexpr uint32_t kUartIntEna = kUart0 + 0x0c;
constexpr uint32_t kUartIntClr = kUart0 + 0x10;
constexpr uint32_t kUartStatus = kUart0 + 0x1c;
constexpr uint32_t kUartConf1 = kUart0 + 0x24;
constexpr uint32_t kRtcOptions0 = 0x3ff48000;
constexpr uint32_t kGpioBase = 0x3ff44000;
constexpr uint32_t kIoMuxBase = 0x3ff49000;
constexpr uint32_t IntrMap(int source) { return 0x3ff00104 + 4 * source; }

// Everything readl/writel touches goes through a Bus.
class Bus {
 public:
  virtual ~Bus() = default;
  virtual uint32_t Read(uint32_t addr) = 0;
  virtual void Write(uint32_t val, uint32_t addr) = 0;
};

// gmock bus: set expectations on single accesses; by default it
// forwards to a fake so that unmentioned accesses still behave.
class MockBus : public Bus {
 public:
  MOCK_METHOD(uint32_t, Read, (uint32_t addr), (override));
  MOCK_METHOD(void, Write, (uint32_t val, uint32_t addr), (override));

  void DelegateTo(Bus& fake) {
    ON_CALL(*this, Read).WillByDefault(
        [&fake](uint32_t a) { return fake.Read(a); });
    ON_CALL(*this, Write).WillByDefault(
        [&fake](uint32_t v, uint32_t a) { fake.Write(v, a); });
  }
};

// Memory, UART0, interrupt matrix and the RTC reset bit.
class FakeSoc : public Bus {
 public:
  uint32_t Read(uint32_t addr) override;
  void Write(uint32_t val, uint32_t addr) override;

  void Poke(uint32_t addr, uint32_t val) { mem_[addr] = val; }
  uint32_t Peek(uint32_t addr) const;

  // UART0
  void Receive(const std::string& bytes);
  std::deque<uint8_t> rx;            // bytes waiting in the RX FIFO
  std::string tx;                    // every byte written to the TX FIFO
  std::deque<uint32_t> txcnt_script; // TXCNT for the next STATUS reads
  int status_reads = 0;
  bool UartIrqAsserted() const;

  // Interrupt matrix: CPU line a peripheral source is routed to
  uint32_t MatrixLine(int source) const { return Peek(IntrMap(source)); }

  // Every write, in order, as (address, value)
  std::vector<std::pair<uint32_t, uint32_t>> writes;
  std::vector<std::pair<uint32_t, uint32_t>> WritesIn(uint32_t lo,
                                                      uint32_t hi) const;

 private:
  static constexpr int kMaxIdlePolls = 10000;
  std::map<uint32_t, uint32_t> mem_;
  int idle_polls_ = 0;
};

// The LX6 interrupt logic, as far as the firmware can observe it.
struct Cpu {
  uint32_t ccount = 0;
  uint32_t ccount_step = 1;     // cycles that pass per CCOUNT read
  uint32_t ccompare0 = 0;
  bool timer_pending = false;   // line 6
  uint32_t intenable = 0;
  uint32_t latched = 0;         // INTSET-raised (software) lines
  uint32_t intlevel = 0;        // PS.INTLEVEL
  int waiti_count = 0;
  std::vector<uint32_t> intclear_writes;
  std::map<std::string, uint32_t> other;  // any other special register
  // Called by waiti when nothing is pending; return true after making
  // something happen (e.g. a byte arriving), false if nothing will.
  std::function<bool()> on_idle;
};

class Sim {
 public:
  Sim();
  ~Sim();
  Sim(const Sim&) = delete;
  Sim& operator=(const Sim&) = delete;

  static Sim& Current();

  FakeSoc soc;
  Cpu cpu;
  Bus* bus = &soc;

  // What the hooks in e32_host.h call
  uint32_t ReadBus(uint32_t addr) { return bus->Read(addr); }
  void WriteBus(uint32_t val, uint32_t addr) { bus->Write(val, addr); }
  uint32_t Ccount();
  uint32_t Rsr(const std::string& sr);
  void Wsr(const std::string& sr, uint32_t v);
  uint32_t IrqSave();
  void IrqRestore(uint32_t ps);
  void Waiti0();

  // Lines currently requesting an interrupt (the INTERRUPT register)
  uint32_t Pending() const;
  // Take a level-1 interrupt now if one is pending, enabled and unmasked
  void MaybeDispatch();
  // Advance CCOUNT, raising the timer line if CCOMPARE0 is crossed
  void Advance(uint32_t cycles);

  const std::string& Console() const { return soc.tx; }

 private:
  bool in_dispatch_ = false;
};

}  // namespace e32

#endif  // E32_TESTS_SIM_H
