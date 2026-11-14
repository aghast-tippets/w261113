# Bare-metal ESP32: no ESP-IDF, no SDK, no libc.
#
#   make            build e32.elf and e32.bin
#   make ram        load into RAM over the serial port and run (like tools/program)
#   make flash      write to flash at 0x1000, where the ROM looks (like progrom)
#   make qemu       boot it in Espressif's QEMU, if you have it

CROSS_COMPILE ?= xtensa-esp32-elf-
CC       = $(CROSS_COMPILE)gcc
OBJDUMP  = $(CROSS_COMPILE)objdump
SIZE     = $(CROSS_COMPILE)size
HOSTCC  ?= cc

PORT    ?= /dev/ttyUSB0
ESPTOOL ?= esptool.py
QEMU    ?= qemu-system-xtensa

# -mtext-section-literals keeps each literal pool next to its code in IRAM
CFLAGS  = -Os -g -Wall -ffreestanding -nostdlib -Iinclude \
	  -mtext-section-literals $(EXTRA_CFLAGS)
LDFLAGS = -nostdlib -T esp32.lds -Wl,-Map=e32.map
LIBGCC  = $(shell $(CC) -print-libgcc-file-name)

OBJS = vectors.o boot.o wdt.o irq.o timer.o panic.o io.o lib.o pp_printf.o gpio.o mimmo.o main.o

all: e32.bin

%.o: %.S
	$(CC) $(CFLAGS) -c $< -o $@

%.o: %.c include/*.h
	$(CC) $(CFLAGS) -c $< -o $@

e32.elf: $(OBJS) esp32.lds
	$(CC) $(CFLAGS) $(LDFLAGS) $(OBJS) $(LIBGCC) -o $@
	$(SIZE) $@

tools/mkimage: tools/mkimage.c
	$(HOSTCC) -O2 -Wall $< -o $@

e32.bin: e32.elf tools/mkimage
	./tools/mkimage $< $@

e32.dis: e32.elf
	$(OBJDUMP) -d $< > $@

ram: e32.bin
	$(ESPTOOL) --chip esp32 -p $(PORT) --no-stub load_ram $<

# "keep" stops esptool from rewriting the header we built
flash: e32.bin
	$(ESPTOOL) --chip esp32 -p $(PORT) -b 460800 write_flash \
		-fm keep -ff keep -fs keep 0x1000 $<

flash.img: e32.bin
	dd if=/dev/zero bs=1M count=4 status=none | tr '\0' '\377' > $@
	dd if=$< of=$@ bs=4096 seek=1 conv=notrunc status=none

qemu: flash.img
	$(QEMU) -nographic -machine esp32 \
		-drive file=flash.img,if=mtd,format=raw

clean:
	rm -f *.o e32.elf e32.bin e32.map e32.dis flash.img tools/mkimage

.PHONY: all ram flash qemu clean
