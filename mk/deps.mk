# Third-party libraries, each built with its own build system into $(PREFIX)

LIB_CFLAGS := $(OPT_FLAGS)
# Looked up by the shell: make itself would trip over the cmake/ folder
# that Emscripten has on the PATH
CMAKE_BIN := $(shell command -v cmake)

# Libraries are found by explicit paths: cross toolchains only search their
# own sysroot
CMAKE_COMMON := -DCMAKE_BUILD_TYPE=Release -DBUILD_SHARED_LIBS=OFF \
    -DCMAKE_INSTALL_PREFIX=$(PREFIX) -DCMAKE_C_FLAGS="$(LIB_CFLAGS)" \
    -DZLIB_LIBRARY=$(PREFIX)/lib/libz.a -DZLIB_INCLUDE_DIR=$(PREFIX)/include

# Images are decoded by MuPDF; Leptonica only processes pixels in memory.
# It needs zlib for the text Tesseract writes into PDF.
LEPTONICA_CMAKE := -DCMAKE_CXX_FLAGS="$(LIB_CFLAGS)" -DBUILD_PROG=OFF \
    -DSW_BUILD=OFF -DENABLE_ZLIB=ON -DENABLE_PNG=OFF -DENABLE_GIF=OFF \
    -DENABLE_JPEG=OFF -DENABLE_TIFF=OFF -DENABLE_WEBP=OFF \
    -DENABLE_OPENJPEG=OFF

# Pages run in parallel instead of OpenMP; the SIMD kernels are chosen at
# run time, so the build is not tied to the build machine's CPU.
# IMAGEDATA_AS_PIX keeps text line images as they are instead of encoding
# them as PNG, which Leptonica is built without. LEPT_TIFF_RESULT answers
# a check that cross builds cannot run: Leptonica has no TIFF either.
TESSERACT_CMAKE := -DBUILD_TRAINING_TOOLS=OFF -DBUILD_TESTS=OFF \
    -DLEPT_TIFF_RESULT=1 \
    -DCMAKE_CXX_FLAGS="$(LIB_CFLAGS) -DTESSERACT_IMAGEDATA_AS_PIX" \
    -DLeptonica_DIR=$(PREFIX)/lib/cmake/leptonica \
    -DDISABLE_ARCHIVE=ON -DDISABLE_CURL=ON -DDISABLE_TIFF=ON \
    -DGRAPHICS_DISABLED=ON -DOPENMP_BUILD=OFF -DENABLE_NATIVE=OFF \
    -DSW_BUILD=OFF -DINSTALL_CONFIGS=OFF -DENABLE_CCACHE=OFF \
    -DENABLE_PRECOMPILED_HEADERS=OFF $(TESSERACT_TARGET_CMAKE)

# Only PDF and image input; no scripting, no office formats, no CJK fonts.
# It uses our zlib, so the programs contain only one.
MUPDF_FEATURES := USE_SYSTEM_ZLIB=yes SYS_ZLIB_CFLAGS=-I$(PREFIX)/include \
    html=no mujs=no extract=no xps=no svg=no brotli=no barcode=no \
    tesseract=no archive=no
MUPDF_DEFINES := -DTOFU -DTOFU_CJK -DFZ_ENABLE_HYPHEN=0 -DFZ_ENABLE_JS=0 \
    -DFZ_ENABLE_EPUB=0 -DFZ_ENABLE_FB2=0 -DFZ_ENABLE_MOBI=0 \
    -DFZ_ENABLE_CBZ=0 -DFZ_ENABLE_OFFICE=0 -DFZ_ENABLE_TXT=0 \
    -DFZ_ENABLE_HTML=0 -DFZ_ENABLE_SVG=0 -DFZ_ENABLE_XPS=0

# Ghostscript only writes PDF/A, so it gets the PDF writer and no extras.
# It is a separate program with its own copies of its libraries.
GS_CONFIGURE := --without-x --disable-cups --disable-gtk \
    --disable-fontconfig --disable-dbus --disable-contrib \
    --without-tesseract --without-libidn --without-libpaper --without-ijs \
    --without-pdftoraster --without-urf --without-so --without-cal \
    --without-libtiff --with-drivers=PS

$(STAMP)/zlib: $(DL)/$(ZLIB_FILE)
	$(call unpack,ZLIB,$(T)/src/zlib)
	cd $(T)/src/zlib && CC="$(CC)" AR="$(AR)" RANLIB="$(RANLIB)" \
	    CFLAGS="$(LIB_CFLAGS)" CHOST=$(HOST) ./configure --static \
	    --prefix=$(PREFIX)
	$(MAKE) -C $(T)/src/zlib -j$(JOBS) libz.a
	$(MAKE) -C $(T)/src/zlib install
	mkdir -p $(@D) && touch $@

$(STAMP)/leptonica: $(DL)/$(LEPTONICA_FILE) $(STAMP)/zlib
	$(call unpack,LEPTONICA,$(T)/src/leptonica)
	$(CMAKE) -S $(T)/src/leptonica -B $(T)/build/leptonica \
	    $(CMAKE_COMMON) $(LEPTONICA_CMAKE)
	$(CMAKE_BIN) --build $(T)/build/leptonica -j$(JOBS)
	$(CMAKE_BIN) --install $(T)/build/leptonica
	mkdir -p $(@D) && touch $@

$(STAMP)/tesseract: $(DL)/$(TESSERACT_FILE) $(STAMP)/leptonica
	$(call unpack,TESSERACT,$(T)/src/tesseract)
	$(CMAKE) -S $(T)/src/tesseract -B $(T)/build/tesseract \
	    $(CMAKE_COMMON) $(TESSERACT_CMAKE)
	$(CMAKE_BIN) --build $(T)/build/tesseract -j$(JOBS)
	$(CMAKE_BIN) --install $(T)/build/tesseract
	mkdir -p $(@D) && touch $@

$(STAMP)/mupdf: $(DL)/$(MUPDF_FILE) $(STAMP)/zlib
	$(call unpack,MUPDF,$(T)/src/mupdf)
	$(MAKE) -C $(T)/src/mupdf -j$(JOBS) build=release \
	    OUT=$(T)/build/mupdf $(MUPDF_TARGET_FLAGS) $(MUPDF_FEATURES) \
	    XCFLAGS="$(MUPDF_DEFINES) $(MUPDF_TARGET_DEFINES) $(LIB_CFLAGS)" libs
	mkdir -p $(PREFIX)/include $(PREFIX)/lib
	cp -r $(T)/src/mupdf/include/mupdf $(PREFIX)/include/
	cp $(T)/build/mupdf/libmupdf.a $(T)/build/mupdf/libmupdf-third.a \
	    $(PREFIX)/lib/
	mkdir -p $(@D) && touch $@

$(STAMP)/ghostscript-src: $(DL)/$(GHOSTSCRIPT_FILE)
	$(call unpack,GHOSTSCRIPT,$(T)/src/ghostscript)
	mkdir -p $(@D) && touch $@

$(STAMP)/ghostscript: $(STAMP)/ghostscript-src $(GS_DEPS)
	cd $(T)/src/ghostscript && $(GS_CONFIGURE_ENV) ./configure \
	    CFLAGS="$(LIB_CFLAGS)" $(GS_CONFIGURE) $(GS_TARGET_FLAGS)
	$(MAKE) -C $(T)/src/ghostscript -j$(JOBS) gs
	touch $@

LIBS_STAMPS := $(STAMP)/tesseract $(STAMP)/mupdf

deps: $(LIBS_STAMPS) $(STAMP)/ghostscript

.PHONY: deps
