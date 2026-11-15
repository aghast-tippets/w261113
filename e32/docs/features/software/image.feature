@EP-01 @FEAT-007
Feature: FEAT-007: Boot image generation
  Epic: EP-01 Build from source without an SDK   ·   Level: software

  Supports: US-01 via STK-01 → SYS-03 → SUB-BLD-04 → SW-IMG-02
  Supports: US-02 via STK-01 → SYS-03 → SUB-BLD-04 → SW-IMG-02
  Supports: US-03 via SW-IMG-01
  Supports: US-05 via STK-03 → SYS-03 → SUB-BLD-04 → SW-IMG-02
  Supports: US-06 via STK-04 → SYS-03 → SUB-BLD-04 → SW-IMG-02

  @SW-IMG-01
  Rule: SW-IMG-01: Usage
    EARS: If `mkimage` is not given exactly two arguments, then it shall print `use: <prog> <in.elf> <out.bin>` and exit with status 1.

    @host @SW-IMG-02 @VER-CMP-18
    Scenario Outline: SW-IMG-01-S01: Invalid input is rejected
      When I run "./tools/mkimage <arguments>"
      Then the exit status is 1
      And the output contains "<message>"

      Examples:
        | arguments                   | message                       |
        |                             | use:                          |
        | Makefile /tmp/x.bin         | not a 32-bit LE Xtensa ELF    |
        | tools/mkimage /tmp/x.bin    | not a 32-bit LE Xtensa ELF    |
        | /nonexistent /tmp/x.bin     | No such file or directory     |

  @SW-IMG-02
  Rule: SW-IMG-02: Input validation
    EARS: If the input cannot be read, is shorter than 52 bytes, lacks the ELF magic, or is not ELFCLASS32, little-endian and `EM_XTENSA` (94), then `mkimage` shall print a diagnostic naming the file and exit with status 1.

  @SW-IMG-03
  Rule: SW-IMG-03: Segments
    EARS: `mkimage` shall emit one segment per `PT_LOAD` program header with `p_filesz` > 0, in program-header order, at `p_paddr`, zero-padded to a multiple of 4 bytes. It shall fail if there are more than 16 such segments, none at all, or a segment that extends past the end of the file.

    @host @pending @VER-CMP-18
    Scenario Outline: SW-IMG-03-S01: Unloadable ELF files are rejected
      Given an Xtensa ELF file "<file>" crafted with <defect>
      When I run "./tools/mkimage <file> /tmp/x.bin"
      Then the exit status is 1
      And the output contains "<message>"

      Examples:
        | file          | defect                                    | message                |
        | many.elf      | 17 PT_LOAD segments with contents         | too many segments      |
        | none.elf      | no PT_LOAD segment with file contents     | nothing to load        |
        | truncated.elf | a segment extending past the end of file  | past end of file       |

  @SW-IMG-04
  Rule: SW-IMG-04: Header values
    EARS: `mkimage` shall write the header bytes `E9`, the segment count, `02` (DIO), `20` (4 MB, 40 MHz) and the entry point. It shall write the extended header as: WP pin `EE`, drive strengths 0, chip ID 0, minimum revision 0, maximum revision `FFFF`, reserved 0, and hash-appended 0.

    @host @VER-CMP-18
    Scenario Outline: SW-IMG-04-S01: Header bytes are as specified
      Given the firmware is built
      When I read byte <offset> of "e32.bin"
      Then its value is <value>

      Examples:
        | offset | value | meaning                  |
        | 0      | 0xe9  | magic                    |
        | 1      | 0x02  | segment count            |
        | 2      | 0x02  | SPI mode DIO             |
        | 3      | 0x20  | 4 MB, 40 MHz             |
        | 8      | 0xee  | WP pin disabled          |
        | 12     | 0x00  | chip ID low byte (ESP32) |
        | 17     | 0xff  | max revision low byte    |
        | 18     | 0xff  | max revision high byte   |
        | 23     | 0x00  | no SHA-256 appended      |

  @SW-IMG-05
  Rule: SW-IMG-05: Checksum
    EARS: `mkimage` shall append zero bytes until the file length is 15 modulo 16, then one checksum byte equal to `0xEF` XORed with every segment data byte.

    @host @VER-CMP-18
    Scenario: SW-IMG-05-S01: The checksum is the last byte of a 16-byte block
      Given the firmware is built
      Then the size of "e32.bin" is a multiple of 16
      And its last byte equals 0xef XOR every segment data byte

  @SW-IMG-06
  Rule: SW-IMG-06: Summary
    EARS: When `mkimage` succeeds, it shall print one line per segment (address and length), then the output name, entry point, total size and checksum.
