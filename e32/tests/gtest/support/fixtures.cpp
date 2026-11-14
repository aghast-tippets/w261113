// fixtures.cpp -- see fixtures.h
#include "fixtures.h"

#include <cctype>
#include <sstream>

namespace e32 {

std::vector<std::string> MonitorTest::Replies() const {
  // Every prompt is followed by the echo of the line that was typed and
  // a newline; drop both, keep everything the monitor answered.
  std::vector<std::string> out;
  std::istringstream in(Console());
  std::string line;
  while (std::getline(in, line)) {
    if (line.rfind("> ", 0) == 0) continue;   // prompt + echo
    if (line == "mimmo.c: Ready to get input (h for help)") continue;
    out.push_back(line);
  }
  return out;
}

std::string Bytes(const std::string& spec) {
  std::string out;
  size_t i = 0;
  while (i < spec.size()) {
    if (std::isspace(static_cast<unsigned char>(spec[i]))) {
      i++;
    } else if (spec[i] == '"') {
      size_t end = spec.find('"', i + 1);
      out += spec.substr(i + 1, end - i - 1);
      i = end + 1;
    } else {
      out.push_back(static_cast<char>(std::stoi(spec.substr(i, 2), nullptr, 16)));
      i += 2;
    }
  }
  return out;
}

std::string Hex(const std::string& bytes) {
  std::string out;
  char buf[4];
  for (unsigned char c : bytes) {
    std::snprintf(buf, sizeof(buf), "%s%02x", out.empty() ? "" : " ", c);
    out += buf;
  }
  return out;
}

}  // namespace e32
