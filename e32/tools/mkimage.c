/*
 * mkimage.c -- turn an ELF file into an image the ESP32 ROM will load.
 *
 * This does the job of tools/fix-checksum in the LPC1343 package: the
 * ROM only runs an image with the right header and checksum.
 *
 * Layout (all little endian):
 *   8 bytes   header: 0xe9, segment count, SPI mode, size|freq, entry
 *  16 bytes   extended header: wp pin, drive strength, chip id, revs...
 *   then for each segment: load address, length, data (multiple of 4)
 *   then zero padding up to 15 mod 16, then one checksum byte:
 *   0xef XORed with every data byte of every segment.
 *
 * We don't append the optional SHA-256 (the "hash appended" flag is 0):
 * the ESP32 ROM checks only the checksum, it's the ESP-IDF second stage
 * bootloader that checks hashes.
 *
 * Every PT_LOAD program header with file contents becomes a segment.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <errno.h>

#define IMG_MAGIC	0xe9
#define CKSUM_SEED	0xef
#define MAX_SEGS	16

/* Header bytes 2 and 3: DIO mode, 4MB flash, 40MHz. Safe on any module. */
#define SPI_MODE_DIO	2
#define SPI_SIZE_4MB	2
#define SPI_FREQ_40M	0

#define EM_XTENSA	94
#define PT_LOAD		1

static uint32_t get32(const uint8_t *p)
{
	return p[0] | (p[1] << 8) | (p[2] << 16) | ((uint32_t)p[3] << 24);
}

static uint16_t get16(const uint8_t *p)
{
	return p[0] | (p[1] << 8);
}

static void put32(uint8_t *p, uint32_t v)
{
	p[0] = v; p[1] = v >> 8; p[2] = v >> 16; p[3] = v >> 24;
}

static uint8_t *read_file(const char *name, long *size)
{
	FILE *f = fopen(name, "rb");
	uint8_t *buf;

	if (!f) {
		fprintf(stderr, "%s: %s\n", name, strerror(errno));
		exit(1);
	}
	fseek(f, 0, SEEK_END);
	*size = ftell(f);
	rewind(f);
	buf = malloc(*size);
	if (!buf || fread(buf, 1, *size, f) != (size_t)*size) {
		fprintf(stderr, "%s: read error\n", name);
		exit(1);
	}
	fclose(f);
	return buf;
}

int main(int argc, char **argv)
{
	uint8_t *elf, hdr[24], seghdr[8], zero[16] = {0}, cksum = CKSUM_SEED;
	uint32_t phoff, entry, off, addr, len, padded, i, j, pos;
	int phnum, phentsize, nsegs = 0;
	long size;
	FILE *out;
	struct { uint32_t off, addr, len; } seg[MAX_SEGS];

	if (argc != 3) {
		fprintf(stderr, "use: %s <in.elf> <out.bin>\n", argv[0]);
		exit(1);
	}
	elf = read_file(argv[1], &size);

	if (size < 52 || memcmp(elf, "\177ELF", 4) || elf[4] != 1
	    || elf[5] != 1 || get16(elf + 18) != EM_XTENSA) {
		fprintf(stderr, "%s: not a 32-bit LE Xtensa ELF\n", argv[1]);
		exit(1);
	}
	entry = get32(elf + 24);
	phoff = get32(elf + 28);
	phentsize = get16(elf + 42);
	phnum = get16(elf + 44);

	for (i = 0; i < (uint32_t)phnum; i++) {
		const uint8_t *ph = elf + phoff + i * phentsize;

		if (get32(ph) != PT_LOAD || get32(ph + 16) == 0)
			continue;	/* not loadable, or bss only */
		if (nsegs == MAX_SEGS) {
			fprintf(stderr, "too many segments\n");
			exit(1);
		}
		seg[nsegs].off = get32(ph + 4);
		seg[nsegs].addr = get32(ph + 12);	/* p_paddr */
		seg[nsegs].len = get32(ph + 16);	/* p_filesz */
		if (seg[nsegs].off + seg[nsegs].len > (uint32_t)size) {
			fprintf(stderr, "segment %i past end of file\n", nsegs);
			exit(1);
		}
		nsegs++;
	}
	if (!nsegs) {
		fprintf(stderr, "%s: nothing to load\n", argv[1]);
		exit(1);
	}

	memset(hdr, 0, sizeof(hdr));
	hdr[0] = IMG_MAGIC;
	hdr[1] = nsegs;
	hdr[2] = SPI_MODE_DIO;
	hdr[3] = (SPI_SIZE_4MB << 4) | SPI_FREQ_40M;
	put32(hdr + 4, entry);
	hdr[8] = 0xee;		/* WP pin: not used */
	/* 9..11 drive strength 0, 12..13 chip id 0 = ESP32, 14..16 min rev 0 */
	hdr[17] = 0xff;		/* max revision: any */
	hdr[18] = 0xff;
	/* 19..22 reserved, 23 hash appended = 0 */

	out = fopen(argv[2], "wb");
	if (!out) {
		fprintf(stderr, "%s: %s\n", argv[2], strerror(errno));
		exit(1);
	}
	fwrite(hdr, 1, sizeof(hdr), out);
	pos = sizeof(hdr);

	for (i = 0; i < (uint32_t)nsegs; i++) {
		off = seg[i].off;
		addr = seg[i].addr;
		len = seg[i].len;
		padded = (len + 3) & ~3;	/* the ROM copies words */
		put32(seghdr, addr);
		put32(seghdr + 4, padded);
		fwrite(seghdr, 1, 8, out);
		fwrite(elf + off, 1, len, out);
		fwrite(zero, 1, padded - len, out);
		for (j = 0; j < len; j++)
			cksum ^= elf[off + j];	/* padding is zero: no-op */
		pos += 8 + padded;
		printf("segment %i: 0x%08x, %u bytes\n", i, addr, padded);
	}

	/* Pad so that the checksum is the last byte of a 16-byte block */
	fwrite(zero, 1, 15 - pos % 16, out);
	fwrite(&cksum, 1, 1, out);
	pos += 15 - pos % 16 + 1;
	fclose(out);

	printf("%s: entry 0x%08x, %u bytes, checksum 0x%02x\n",
	       argv[2], entry, pos, cksum);
	return 0;
}
