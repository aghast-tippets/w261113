// process.h -- helpers for end-to-end tests: run a host command, build
// Xtensa ELF files byte by byte, read and write files.
#ifndef E32_TESTS_PROCESS_H
#define E32_TESTS_PROCESS_H

#include <cstdint>
#include <cstdio>
#include <fstream>
#include <iterator>
#include <string>
#include <sys/wait.h>
#include <vector>

namespace e32 {

struct RunResult {
  int exit_status = -1;   // -1 if the command did not exit normally
  std::string output;     // stdout and stderr, interleaved
};

inline std::string ShellQuote(const std::string& s) {
  std::string out = "'";
  for (char c : s) out += c == '\'' ? std::string("'\\''") : std::string(1, c);
  return out + "'";
}

// Runs argv through /bin/sh with stderr folded into stdout.
inline RunResult RunCommand(const std::vector<std::string>& argv) {
  std::string cmd;
  for (const auto& a : argv) cmd += (cmd.empty() ? "" : " ") + ShellQuote(a);
  cmd += " 2>&1";
  RunResult r;
  FILE* p = popen(cmd.c_str(), "r");
  if (!p) return r;
  char buf[4096];
  size_t n;
  while ((n = fread(buf, 1, sizeof buf, p)) > 0) r.output.append(buf, n);
  int status = pclose(p);
  if (WIFEXITED(status)) r.exit_status = WEXITSTATUS(status);
  return r;
}

inline std::vector<uint8_t> ReadFile(const std::string& path) {
  std::ifstream in(path, std::ios::binary);
  return std::vector<uint8_t>(std::istreambuf_iterator<char>(in), {});
}

inline void WriteFile(const std::string& path, const std::vector<uint8_t>& bytes) {
  std::ofstream out(path, std::ios::binary);
  out.write(reinterpret_cast<const char*>(bytes.data()), static_cast<std::streamsize>(bytes.size()));
}

// A 32-bit little-endian ELF for EM_XTENSA (94), program headers only.
class XtensaElf {
 public:
  static constexpr uint32_t kPtLoad = 1, kPtNote = 4;

  struct Segment {
    uint32_t type, paddr;
    std::vector<uint8_t> data;
    uint32_t claimed_size;   // p_filesz; normally data.size()
  };

  XtensaElf& Entry(uint32_t e) { entry_ = e; return *this; }
  XtensaElf& Load(uint32_t paddr, std::vector<uint8_t> data) {
    uint32_t n = static_cast<uint32_t>(data.size());
    segs_.push_back({kPtLoad, paddr, std::move(data), n});
    return *this;
  }
  XtensaElf& Other(uint32_t type, uint32_t paddr, std::vector<uint8_t> data, uint32_t claimed) {
    segs_.push_back({type, paddr, std::move(data), claimed});
    return *this;
  }

  std::vector<uint8_t> Bytes() const {
    const uint32_t ehsize = 52, phentsize = 32;
    std::vector<uint8_t> out(ehsize + phentsize * segs_.size(), 0);
    const uint8_t ident[] = {0x7f, 'E', 'L', 'F', 1, 1, 1};
    std::copy(std::begin(ident), std::end(ident), out.begin());
    Put16(out, 16, 2);           // ET_EXEC
    Put16(out, 18, 94);          // EM_XTENSA
    Put32(out, 20, 1);
    Put32(out, 24, entry_);
    Put32(out, 28, ehsize);      // e_phoff
    Put16(out, 40, ehsize);
    Put16(out, 42, phentsize);
    Put16(out, 44, static_cast<uint16_t>(segs_.size()));
    for (size_t i = 0; i < segs_.size(); i++) {
      const Segment& s = segs_[i];
      size_t ph = ehsize + i * phentsize;
      Put32(out, ph + 0, s.type);
      Put32(out, ph + 4, static_cast<uint32_t>(out.size()));  // p_offset
      Put32(out, ph + 8, s.paddr);
      Put32(out, ph + 12, s.paddr);
      Put32(out, ph + 16, s.claimed_size);
      Put32(out, ph + 20, s.claimed_size);
      Put32(out, ph + 24, 7);
      Put32(out, ph + 28, 4);
      out.insert(out.end(), s.data.begin(), s.data.end());
    }
    return out;
  }

 private:
  static void Put16(std::vector<uint8_t>& b, size_t at, uint16_t v) {
    b[at] = v & 0xff; b[at + 1] = v >> 8;
  }
  static void Put32(std::vector<uint8_t>& b, size_t at, uint32_t v) {
    for (int i = 0; i < 4; i++) b[at + i] = (v >> (8 * i)) & 0xff;
  }
  uint32_t entry_ = 0;
  std::vector<Segment> segs_;
};

}  // namespace e32

#endif  // E32_TESTS_PROCESS_H
