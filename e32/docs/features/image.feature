@EP-01 @F-02
Feature: Boot image generation
  As a developer
  I want the ELF converted to an image the ESP32 boot ROM accepts
  So that I can load or flash the build output directly

  @host @IF-01 @SUB-BLD-04 @SW-IMG-03 @SW-IMG-06 @CMP-33 @VER-SUB-03 @VER-CMP-18
  Scenario: A valid image is decoded by an independent implementation
    Given the firmware is built
    When I run "esptool --chip esp32 image-info e32.bin"
    Then the output contains "Segments: 2"
    And the output contains "Chip ID: 0 (ESP32)"
    And the output contains "(valid)"
    And segment 0 is loaded at 0x3ffb0000 with memory type "DRAM"
    And segment 1 is loaded at 0x40080000 with memory type "IRAM"

  @host @SW-IMG-04 @VER-CMP-18
  Scenario Outline: Header bytes are as specified
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

  @host @SW-IMG-05 @VER-CMP-18
  Scenario: The checksum is the last byte of a 16-byte block
    Given the firmware is built
    Then the size of "e32.bin" is a multiple of 16
    And its last byte equals 0xef XOR every segment data byte

  @host @SW-IMG-01 @SW-IMG-02 @VER-CMP-18
  Scenario Outline: Invalid input is rejected
    When I run "./tools/mkimage <arguments>"
    Then the exit status is 1
    And the output contains "<message>"

    Examples:
      | arguments                   | message                       |
      |                             | use:                          |
      | Makefile /tmp/x.bin         | not a 32-bit LE Xtensa ELF    |
      | tools/mkimage /tmp/x.bin    | not a 32-bit LE Xtensa ELF    |
      | /nonexistent /tmp/x.bin     | No such file or directory     |

  @host @pending @SW-IMG-03 @VER-CMP-18
  Scenario Outline: Unloadable ELF files are rejected
    Given an Xtensa ELF file "<file>" crafted with <defect>
    When I run "./tools/mkimage <file> /tmp/x.bin"
    Then the exit status is 1
    And the output contains "<message>"

    Examples:
      | file          | defect                                    | message                |
      | many.elf      | 17 PT_LOAD segments with contents         | too many segments      |
      | none.elf      | no PT_LOAD segment with file contents     | nothing to load        |
      | truncated.elf | a segment extending past the end of file  | past end of file       |

  @qemu @HW-11 @SYS-04 @VER-SUB-03
  Scenario: The real boot ROM accepts the image
    Given the firmware is booted in QEMU from flash
    Then the console shows "load:0x3ffb0000"
    And the console shows "load:0x40080000"
    And the console shows a line matching /^entry 0x400803[0-9a-f]{2}$/
    And the console does not show "invalid header"
    And the console does not show "checksum"
