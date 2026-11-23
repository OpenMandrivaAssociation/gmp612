#!/bin/bash
# GMP 6.1.2, static only.
# GHC before 8.0 treats a zero mpz result as a Haskell closure. GMP 6.2
# made mpz_init lazy and leaves that pointer in libgmp's data segment, so
# every hop before GHC 8.0 links this archive instead of the system GMP.
# The archive is installed under %{_libdir}/gmp612. There is no libgmp.so,
# so the dynamic linker cannot pick up the system libgmp.so.10.
set -euo pipefail

ROOT=${1:?usage: gmp612-build.sh ROOT}
PREFIX=$ROOT/dest
WORK=$ROOT/work
SRC=$ROOT/gmp-6.1.2.tar.xz

export TMPDIR=$WORK/tmp
mkdir -p "$TMPDIR" "$WORK/src" "$PREFIX"
unset CFLAGS CXXFLAGS LDFLAGS CPPFLAGS RPM_OPT_FLAGS RPM_LD_FLAGS || true

if [ ! -f "$WORK/src/gmp-6.1.2/configure" ]; then
	tar -C "$WORK/src" -xJf "$SRC"
fi
cd "$WORK/src/gmp-6.1.2"
if [ ! -f Makefile ]; then
	./configure --prefix="$PREFIX" \
		--disable-shared --enable-static --with-pic \
		--disable-assembly --disable-cxx \
		CFLAGS="-O2 -std=gnu11"
fi
make -j8
make check
make install

if find "$PREFIX" -name 'libgmp.so*' | grep -q .; then
	echo "gmp612: shared library was installed" >&2
	exit 1
fi
# libtool's .la records the build prefix. Nothing in this chain uses it.
rm -f "$PREFIX/lib/libgmp.la"
test -f "$PREFIX/lib/libgmp.a"
test -f "$PREFIX/include/gmp.h"

cat > "$WORK/t.c" << 'EOF'
#include <gmp.h>
#include <stdio.h>
int main(void) {
	mpz_t a, b;
	char buf[32];
	mpz_init_set_ui(a, 0);
	mpz_init_set_ui(b, 5);
	mpz_mul(a, a, b);
	mpz_get_str(buf, 10, a);
	puts(buf);
	return 0;
}
EOF
gcc -O2 -std=gnu11 -I"$PREFIX/include" -o "$WORK/t" "$WORK/t.c" -L"$PREFIX/lib" -lgmp
got=$("$WORK/t" | tr -d '[:space:]')
[ "$got" = "0" ]
if readelf -d "$WORK/t" | grep -q 'NEEDED.*libgmp\.so'; then
	echo "gmp612: test program needs libgmp.so" >&2
	readelf -d "$WORK/t" >&2
	exit 1
fi
printf 'GMP612_DONE %s\n' "$PREFIX/lib/libgmp.a"
