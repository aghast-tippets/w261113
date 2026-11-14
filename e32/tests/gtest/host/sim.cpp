// sim.cpp -- see sim.h
#include "sim.h"

#include <cstdio>
#include <cstdlib>

#include "e32_host.h"

extern "C" {
struct irq_frame;
void irq_dispatch(struct irq_frame* f);

// Linker-script symbols that main.c prints
char __bss_start[4], __bss_end[4], _stack_top[4];
}

namespace e32 {
namespace {

Sim* g_current = nullptr;

constexpr uint32_t kLevel1Mask = 0x000637ff;   // xtensa.h LEVEL1_INT_MASK
// CPU lines whose matrix inputs are ignored (internal to the core)
constexpr uint32_t kInternalLines = (1u << 6) | (1u << 7) | (1u << 11) |
                                    (1u << 15) | (1u << 16) | (1u << 29);
constexpr int kSrcUart0 = 34;
constexpr uint32_t kPsBase = 0x00040020;       // WOE | UM, as boot.S sets

}  // namespace

// ---------------------------------------------------------------- FakeSoc

uint32_t FakeSoc::Peek(uint32_t addr) const {
  auto it = mem_.find(addr);
  return it == mem_.end() ? 0 : it->second;
}

void FakeSoc::Receive(const std::string& bytes) {
  for (unsigned char c : bytes) rx.push_back(c);
}

bool FakeSoc::UartIrqAsserted() const {
  return !rx.empty() && (Peek(kUartIntEna) & 1);
}

uint32_t FakeSoc::Read(uint32_t addr) {
  if (addr == kUartFifo) {
    if (rx.empty()) return 0;
    uint32_t c = rx.front();
    rx.pop_front();
    return c;
  }
  if (addr == kUartStatus) {
    status_reads++;
    uint32_t txcnt = 0;
    if (!txcnt_script.empty()) {
      txcnt = txcnt_script.front();
      txcnt_script.pop_front();
    }
    uint32_t rxcnt = rx.size() > 255 ? 255 : static_cast<uint32_t>(rx.size());
    // Polled receive spins on STATUS; a long run of idle polls means the
    // firmware is waiting for input the test will never send.
    if (rxcnt == 0 && txcnt == 0) {
      if (++idle_polls_ > kMaxIdlePolls) {
        idle_polls_ = 0;
        throw InputExhausted{};
      }
    } else {
      idle_polls_ = 0;
    }
    return rxcnt | (txcnt << 16);
  }
  return Peek(addr);
}

void FakeSoc::Write(uint32_t val, uint32_t addr) {
  writes.emplace_back(addr, val);
  idle_polls_ = 0;
  if (addr == kUartFifo) {
    tx.push_back(static_cast<char>(val & 0xff));
    return;
  }
  if (addr == kRtcOptions0 && (val & 0x80000000u)) {
    mem_[addr] = val;
    throw Rebooted{};
  }
  mem_[addr] = val;
}

std::vector<std::pair<uint32_t, uint32_t>> FakeSoc::WritesIn(
    uint32_t lo, uint32_t hi) const {
  std::vector<std::pair<uint32_t, uint32_t>> out;
  for (const auto& w : writes)
    if (w.first >= lo && w.first < hi) out.push_back(w);
  return out;
}

// -------------------------------------------------------------------- Sim

Sim::Sim() {
  if (g_current) {
    std::fprintf(stderr, "e32 sim: two simulators alive at once\n");
    std::abort();
  }
  g_current = this;
}

Sim::~Sim() { g_current = nullptr; }

Sim& Sim::Current() {
  if (!g_current) {
    std::fprintf(stderr, "e32 sim: firmware ran with no simulator\n");
    std::abort();
  }
  return *g_current;
}

uint32_t Sim::Pending() const {
  uint32_t p = cpu.latched;
  if (cpu.timer_pending) p |= 1u << 6;
  if (soc.UartIrqAsserted()) {
    uint32_t line = soc.MatrixLine(kSrcUart0);
    if (line < 32 && !((1u << line) & kInternalLines)) p |= 1u << line;
  }
  return p;
}

void Sim::Advance(uint32_t cycles) {
  uint32_t old = cpu.ccount;
  cpu.ccount += cycles;
  // Did CCOUNT pass CCOMPARE0 (u32 wrap-around aware)?
  if (cycles && cpu.ccompare0 - old - 1 < cycles) cpu.timer_pending = true;
}

void Sim::MaybeDispatch() {
  if (in_dispatch_ || cpu.intlevel >= 1) return;
  if (!(Pending() & cpu.intenable & kLevel1Mask)) return;
  // The vector code runs irq_dispatch with level-1 interrupts masked
  struct Guard {
    Sim* s;
    uint32_t level;
    ~Guard() {
      s->cpu.intlevel = level;
      s->in_dispatch_ = false;
    }
  } guard{this, cpu.intlevel};
  in_dispatch_ = true;
  cpu.intlevel = 1;
  uint32_t frame[24] = {};
  irq_dispatch(reinterpret_cast<struct irq_frame*>(frame));
}

uint32_t Sim::Ccount() {
  uint32_t now = cpu.ccount;
  Advance(cpu.ccount_step);
  MaybeDispatch();
  return now;
}

uint32_t Sim::Rsr(const std::string& sr) {
  if (sr == "intenable") return cpu.intenable;
  if (sr == "interrupt") return Pending();
  if (sr == "ccompare0") return cpu.ccompare0;
  if (sr == "ccount") return Ccount();
  if (sr == "ps") return kPsBase | cpu.intlevel;
  auto it = cpu.other.find(sr);
  return it == cpu.other.end() ? 0 : it->second;
}

void Sim::Wsr(const std::string& sr, uint32_t v) {
  if (sr == "intenable") {
    cpu.intenable = v;
  } else if (sr == "intclear") {
    cpu.intclear_writes.push_back(v);
    cpu.latched &= ~v;
  } else if (sr == "intset") {
    cpu.latched |= v;
  } else if (sr == "ccompare0") {
    cpu.ccompare0 = v;
    cpu.timer_pending = false;  // writing CCOMPAREn clears its interrupt
  } else if (sr == "ps") {
    cpu.intlevel = v & 0xf;
  } else {
    cpu.other[sr] = v;
  }
  MaybeDispatch();
}

uint32_t Sim::IrqSave() {
  uint32_t old = kPsBase | cpu.intlevel;
  cpu.intlevel = 3;  // rsil 3
  return old;
}

void Sim::IrqRestore(uint32_t ps) {
  cpu.intlevel = ps & 0xf;
  MaybeDispatch();
}

void Sim::Waiti0() {
  cpu.waiti_count++;
  cpu.intlevel = 0;
  if (!(Pending() & cpu.intenable & kLevel1Mask)) {
    if (!cpu.on_idle || !cpu.on_idle()) throw InputExhausted{};
  }
  MaybeDispatch();
}

}  // namespace e32

// ------------------------------------------------------------------ hooks

using e32::Sim;

extern "C" unsigned int e32_host_readl(unsigned int addr) {
  return Sim::Current().ReadBus(addr);
}
extern "C" void e32_host_writel(unsigned int val, unsigned int addr) {
  Sim::Current().WriteBus(val, addr);
}
extern "C" unsigned int e32_host_ccount(void) { return Sim::Current().Ccount(); }
extern "C" unsigned int e32_host_rsr(const char* sr) {
  return Sim::Current().Rsr(sr);
}
extern "C" void e32_host_wsr(const char* sr, unsigned int v) {
  Sim::Current().Wsr(sr, v);
}
extern "C" unsigned int e32_host_irq_save(void) {
  return Sim::Current().IrqSave();
}
extern "C" void e32_host_irq_restore(unsigned int ps) {
  Sim::Current().IrqRestore(ps);
}
extern "C" void e32_host_waiti0(void) { Sim::Current().Waiti0(); }
extern "C" void e32_host_trap(const char* what) { throw e32::Trapped{what}; }
