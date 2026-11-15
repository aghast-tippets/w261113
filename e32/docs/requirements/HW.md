# Hardware requirements (HW)

Level 5. What must the *hardware* do? These requirements are allocated from
the target-hardware subsystem (SS-TGT), and from the subsystems whose
behaviour relies on hardware properties. The hardware is bought, not built,
so these requirements constrain **which boards are suitable**, and record the
hardware facts the software relies on. They are verified by inspection,
analysis, or a hardware test.

---

### HW-01 — SoC
- **Type:** Hardware
- **EARS:** Ubiquitous
- **Priority:** Must
- **Statement:** The target shall be an ESP32 (Xtensa LX6, ESP32-D0WD/D0WDQ6 family) with 520 KB internal SRAM. The firmware uses only the PRO CPU; the ROM holds the APP CPU in reset.
- **Derives from:** SUB-TGT-01
- **Rationale:** Needed to meet SUB-TGT-01 (Target board).
- **Verified by:** VER-HW-01

### HW-02 — Crystal
- **Type:** Hardware
- **EARS:** Ubiquitous
- **Priority:** Must
- **Statement:** The board shall use a 40 MHz crystal, so that the ROM's UART0 set-up gives 115200 baud and `CPU_HZ` = 40 MHz holds while the CPU runs from the crystal.
- **Derives from:** SUB-TGT-01, SUB-TIME-03
- **Rationale:** Needed to meet SUB-TGT-01 (Target board); SUB-TIME-03 (Busy-wait delay).
- **Verified by:** VER-HW-02

### HW-03 — SPI flash
- **Type:** Hardware
- **EARS:** Ubiquitous
- **Priority:** Must
- **Statement:** The SPI flash shall operate in DIO mode at 40 MHz and hold at least `0x1000` plus the image size. The image header declares 4 MB.
- **Derives from:** SUB-TGT-01, SUB-BLD-04
- **Rationale:** Needed to meet SUB-TGT-01 (Target board); SUB-BLD-04 (Image conversion).
- **Verified by:** VER-HW-03

### HW-04 — Serial connection
- **Type:** Hardware
- **EARS:** Ubiquitous
- **Priority:** Must
- **Statement:** UART0 TXD (GPIO1) and RXD (GPIO3) shall be connected to a USB-serial bridge that the host can open as `PORT`.
- **Derives from:** SUB-TGT-01
- **Rationale:** Needed to meet SUB-TGT-01 (Target board).
- **Verified by:** VER-HW-04

### HW-05 — Boot and reset controls
- **Type:** Hardware
- **EARS:** Event-driven
- **Priority:** Must
- **Statement:** When GPIO0 is held low while EN is released, the board shall enter ROM download mode. The board shall provide a means to pulse EN, by a button or by the bridge's DTR/RTS circuit.
- **Derives from:** SUB-TGT-01
- **Rationale:** Needed to meet SUB-TGT-01 (Target board).
- **Verified by:** VER-HW-04

### HW-06 — Indicator LED
- **Type:** Hardware
- **EARS:** Optional feature
- **Priority:** Must
- **Statement:** Where blink mode is used, an LED shall be connected to `LED_GPIO` (GPIO2 by default) such that it is visibly lit at one level and off at the other.
- **Derives from:** SUB-TGT-02
- **Rationale:** Needed to meet SUB-TGT-02 (Indicator LED).
- **Verified by:** VER-HW-05

### HW-07 — Flash pins
- **Type:** Hardware
- **EARS:** Ubiquitous
- **Priority:** Must
- **Statement:** On the target module, GPIO6–GPIO11 are connected to the SPI flash and shall be treated as unavailable to the application.
- **Derives from:** SUB-GPIO-02
- **Rationale:** Needed to meet SUB-GPIO-02 (Pin protection).
- **Verified by:** VER-HW-06

### HW-08 — Input-only pins
- **Type:** Hardware
- **EARS:** Ubiquitous
- **Priority:** Must
- **Statement:** GPIO34–GPIO39 are input-only pads without output drivers. GPIO24 and GPIO28–31 do not exist, and GPIO20 is bonded out only on some ESP32 packages.
- **Derives from:** SUB-GPIO-02
- **Rationale:** Needed to meet SUB-GPIO-02 (Pin protection).
- **Verified by:** VER-HW-06

### HW-09 — Free SRAM after hand-over
- **Type:** Hardware
- **EARS:** State-driven
- **Priority:** Must
- **Statement:** While the firmware runs, IRAM `0x40080000`–`0x4009FFFF` and DRAM `0x3FFB0000`–`0x3FFDBFFF` shall be usable by the application, with no ROM data that must be preserved.
- **Derives from:** SUB-BLD-02
- **Rationale:** Needed to meet SUB-BLD-02 (Memory layout).
- **Verified by:** VER-HW-07

### HW-10 — IRAM access width
- **Type:** Hardware
- **EARS:** Unwanted behaviour
- **Priority:** Must
- **Statement:** If IRAM is accessed with an 8- or 16-bit load or store, then the hardware raises an exception. The layout therefore keeps byte-addressed data out of IRAM.
- **Derives from:** SUB-BLD-02
- **Rationale:** Needed to meet SUB-BLD-02 (Memory layout).
- **Verified by:** VER-HW-07

### HW-11 — Boot ROM behaviour relied on
- **Type:** Hardware
- **EARS:** Event-driven
- **Priority:** Must
- **Statement:** When the chip resets, the boot ROM shall:
  - load the segmented image from flash `0x1000` (in SPI boot), or over UART0 (in download mode);
  - verify the XOR checksum;
  - leave UART0 configured at 115200 8N1;
  - call the entry point with the windowed ABI.
- **Derives from:** SUB-BLD-04, SUB-TGT-01, SUB-BOOT-03
- **Rationale:** Needed to meet SUB-BLD-04 (Image conversion); SUB-TGT-01 (Target board); SUB-BOOT-03 (Inherit the console set-up).
- **Verified by:** VER-HW-08

### HW-12 — Software system reset
- **Type:** Hardware
- **EARS:** Event-driven
- **Priority:** Must
- **Statement:** When bit 31 (`SW_SYS_RST`) of `RTC_CNTL_OPTIONS0` is written as 1, the chip shall perform a full system reset and boot through the ROM, which reports `rst:0x3 (SW_RESET)`.
- **Derives from:** SUB-FLT-03
- **Rationale:** Needed to meet SUB-FLT-03 (Reboot).
- **Verified by:** VER-HW-09

### HW-13 — CPU core configuration
- **Type:** Hardware
- **EARS:** Ubiquitous
- **Priority:** Must
- **Statement:** The LX6 core configuration shall provide:
  - 64 windowed address registers;
  - zero-overhead loops;
  - 32-bit divide with the IntegerDivideByZero exception;
  - `CCOUNT` with `CCOMPARE0` on interrupt line 6;
  - a level-1 software interrupt on line 7, and a level-3 one on line 29;
  - the level-1 line mask `0x000637FF`;
  - `EXCM` level 3;
  - `MISC0`–`MISC3`;
  - the vector offsets listed in IF-05.
- **Derives from:** SUB-EXC-01, SUB-EXC-03, SUB-EXC-05, SUB-TIME-01
- **Rationale:** Needed to meet SUB-EXC-01 (Register-window spill and fill); SUB-EXC-03 (Interrupt context); SUB-EXC-05 (Route faults); SUB-TIME-01 (Periodic tick).
- **Verified by:** VER-HW-10

### HW-14 — No external memory
- **Type:** Hardware
- **EARS:** Ubiquitous
- **Priority:** Must
- **Statement:** The target shall not need PSRAM or any other external memory. Boards with PSRAM are acceptable, but it stays unused.
- **Derives from:** SUB-TGT-01
- **Rationale:** Needed to meet SUB-TGT-01 (Target board).
- **Verified by:** VER-HW-01
