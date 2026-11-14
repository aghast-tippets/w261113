#!/bin/sh
# Build a bare xtensa-esp32-elf gcc (C only, no libc) from source.
#
# The only Espressif-specific input is the "overlay": the files that
# describe the ESP32's Xtensa LX6 core configuration (which options and
# instructions it has).  They are dropped into the binutils and gcc trees
# before configuring.  Takes ~30 minutes on two cores.
#
# Needs: git, a host gcc/g++, make, flex, bison, texinfo, libgmp/mpfr/mpc-dev
set -e

PREFIX=${PREFIX:-$HOME/xtensa-esp32}
WORK=${WORK:-$PWD/toolchain-build}
J=${J:-$(nproc)}

mkdir -p "$WORK" && cd "$WORK"
[ -d overlays ] || git clone --depth 1 https://github.com/espressif/xtensa-overlays overlays
[ -d binutils ] || git clone --depth 1 -b esp-2.47.0_20261109 https://github.com/espressif/binutils-gdb binutils
[ -d gcc ] || git clone --depth 1 -b esp-14.4.0_20261030 https://github.com/espressif/gcc gcc

cp -r overlays/xtensa_esp32/binutils/* binutils/
cp -r overlays/xtensa_esp32/gcc/* gcc/

mkdir -p b-binutils && cd b-binutils
../binutils/configure --target=xtensa-esp32-elf --prefix="$PREFIX" \
	--disable-nls --disable-werror --disable-gdb --disable-gdbserver \
	--disable-sim --disable-gprofng --disable-libdecnumber --disable-readline
make -j"$J" && make install
cd ..

export PATH="$PREFIX/bin:$PATH"
mkdir -p b-gcc && cd b-gcc
../gcc/configure --target=xtensa-esp32-elf --prefix="$PREFIX" \
	--enable-languages=c --without-headers --with-newlib \
	--disable-nls --disable-shared --disable-threads --disable-libssp \
	--disable-libquadmath --disable-libgomp --disable-libatomic \
	--disable-multilib --disable-werror
make -j"$J" all-gcc all-target-libgcc
make install-gcc install-target-libgcc

echo "Done: add $PREFIX/bin to your PATH"
