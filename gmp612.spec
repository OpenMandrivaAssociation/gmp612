%global debug_package %{nil}
%global _find_debuginfo_opts --no-ar-files
Summary:	GMP 6.1.2 static library for the GHC bootstrap
Name:		gmp612
Version:	6.1.2
Release:	1
License:	LGPLv3+
Group:		Development/Other
Url:		https://gmplib.org/
# Private static GMP. Does not replace the system gmp, so no Epoch.
# GHC before 8.0 cannot use GMP 6.2+ (lazy mpz_init).
ExclusiveArch:	x86_64 znver1
Source0:	gmp-6.1.2.tar.xz
Source1:	gmp612-build.sh
Source2:	%{name}.rpmlintrc

BuildRequires:	m4
BuildRequires:	gcc
BuildRequires:	make
BuildRequires:	diffutils
BuildRequires:	binutils
BuildRequires:	xz

%description
Static GMP 6.1.2 used by the source-only GHC bootstrap through GHC 7.8.
Installed under %{_libdir}/gmp612 so it does not provide libgmp.so.10.
GHC 8.0 and later use the system GMP.

%prep
set -eu
cd %{_builddir}
rm -rf gmp612-root
mkdir -p gmp612-root
cp -a %{SOURCE0} gmp612-root/gmp-6.1.2.tar.xz
set +u

%build
set -eu
bash %{SOURCE1} "%{_builddir}/gmp612-root"
set +u

%install
set -eu
mkdir -p %{buildroot}%{_libdir}
rm -rf %{buildroot}%{_libdir}/gmp612
cp -a %{_builddir}/gmp612-root/dest %{buildroot}%{_libdir}/gmp612
test -f %{buildroot}%{_libdir}/gmp612/lib/libgmp.a
test -f %{buildroot}%{_libdir}/gmp612/include/gmp.h
if find %{buildroot}%{_libdir}/gmp612 -name 'libgmp.so*' | grep -q .; then
	echo "gmp612: refusing to ship a shared library" >&2
	exit 1
fi
set +u

%files
%{_libdir}/gmp612/

%check
set -eu
inc=%{buildroot}%{_libdir}/gmp612/include
lib=%{buildroot}%{_libdir}/gmp612/lib
cat > t.c << 'EOF'
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
gcc -O2 -std=gnu11 -I"$inc" -o t t.c -L"$lib" -lgmp
test "$(./t)" = "0"
if readelf -d ./t | grep -q 'NEEDED.*libgmp\.so'; then
	echo "gmp612: test program needs libgmp.so" >&2
	exit 1
fi
set +u
