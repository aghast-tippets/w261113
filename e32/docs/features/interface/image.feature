@EP-01 @FEAT-008
Feature: FEAT-008: Boot image generation
  Epic: EP-01 Build from source without an SDK   ·   Level: interface

  Supports: US-01 via STK-01 → SYS-03 → SUB-BLD-04 → IF-01
  Supports: US-02 via STK-01 → SYS-03 → SUB-BLD-04 → IF-01
  Supports: US-03 via STK-04 → SYS-04 → IF-01
  Supports: US-05 via STK-03 → SYS-05 → IF-01
  Supports: US-06 via STK-04 → SYS-04 → IF-01

  @IF-01
  Rule: IF-01: Boot image format
    EARS: The image passed from `mkimage` to the boot ROM shall consist of these parts, all little-endian:
      - an 8-byte header: magic `0xE9`, segment count (1–16), SPI mode, a byte with the flash size in the high nibble and the frequency in the low nibble, and a 32-bit entry address;
      - a 16-byte extended header: WP pin, 3 drive-strength bytes, a 16-bit chip ID, a minimum revision byte, 16-bit minimum and maximum full revisions, 4 reserved bytes and a hash-appended flag;
      - for each segment, a 32-bit load address, a 32-bit length that is a multiple of 4, and the data;
      - zero padding to 15 modulo 16, then a checksum byte equal to `0xEF` XORed with all segment data.
