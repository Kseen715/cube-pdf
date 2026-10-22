# Windows build, cross-compiled with MinGW-w64 in docker/windows.Dockerfile

PACKAGE := desktop
HOST := x86_64-w64-mingw32
EXE := .exe
CC := $(HOST)-gcc
CXX := $(HOST)-g++
RANLIB := $(HOST)-ranlib
AR := $(HOST)-ar
WINDRES := $(HOST)-windres
CMAKE := cmake -DCMAKE_TOOLCHAIN_FILE=$(CURDIR)/mk/mingw.cmake
OPT_FLAGS := -O2

MUPDF_TARGET_FLAGS := OS=MINGW CC=$(CC) CXX=$(CXX) AR=$(AR) \
    HAVE_X11=no HAVE_GLUT=no HAVE_OBJCOPY=no
# MinGW defines MSVC's _M_AMD64, which turns on MuPDF's SSE4.1 code
# without the compiler flag it needs. That code (deskew) is not used here.
MUPDF_TARGET_DEFINES := -DARCH_HAS_SSE=0
TESSERACT_TARGET_CMAKE :=

# The manifest switches the process code page to UTF-8, so the narrow file
# APIs of all the C libraries accept non-ASCII paths (Windows 10 1903+)
MANIFEST_OBJ := $(T)/obj/utf8-manifest.o
GS_TARGET_FLAGS := --host=$(HOST) --build=x86_64-pc-linux-gnu CCAUX=gcc \
    --with-exe-ext=.exe LDFLAGS="-static $(MANIFEST_OBJ)"
GS_DEPS := $(MANIFEST_OBJ)

# Threads get the same 8 MB stack as on Linux
CORE_LDFLAGS := -static -Wl,--stack,8388608
CORE_OBJS_EXTRA := $(MANIFEST_OBJ)

$(MANIFEST_OBJ): mk/utf8.rc mk/utf8.manifest
	mkdir -p $(@D)
	$(WINDRES) -I mk -i $< -o $@

TAURI_TRIPLE := x86_64-pc-windows-msvc
TAURI_BUNDLES := nsis

# cargo-xwin fetches the MSVC and Windows SDK libraries. tauri-build links
# the VC runtime statically and the Universal C Runtime from Windows, so
# users need no Visual C++ redistributable.
TAURI_ENV := XWIN_ACCEPT_LICENSE=1 XWIN_CACHE_DIR=$(B)/xwin
TAURI_BUILD_FLAGS := --runner cargo-xwin

# The installer, plus a zip that runs from any folder: the same files the
# installer puts next to each other
PORTABLE := $(T)/portable/CUBE-PDF

define package_desktop
	cp $(TAURI_BUNDLE)/nsis/*-setup.exe $(DIST)/
	rm -rf $(T)/portable && mkdir -p $(PORTABLE)
	cp $(T)/cargo/$(TAURI_TRIPLE)/release/CUBE-PDF.exe $(PORTABLE)/
	cp $(BIN)/ocr-pdf-core.exe $(BIN)/ocr-pdf-gs.exe $(PORTABLE)/
	cp -r $(BIN)/tessdata $(PORTABLE)/
	cp LICENSE $(PORTABLE)/LICENSE.txt
	cp $(NOTICES) $(PORTABLE)/
	cd $(T)/portable && zip -qr $(DIST)/CUBE-PDF-windows-portable.zip CUBE-PDF
endef
