# The OCR core: ocr-pdf-core and ocr-pdf-gs for the desktop, or the
# WebAssembly modules for the web (their link step is in mk/web.mk)

CORE_SRC := core/src

# The goal "coverage" (mk/test.mk) builds the core instrumented for gcov,
# unoptimized so that lines map to code, apart from the normal build
ifneq ($(filter coverage,$(MAKECMDGOALS)),)
COV := -coverage
COV_FLAGS := -O0 --coverage
CORE_LDFLAGS += --coverage
endif

CORE_OBJ := $(T)/obj/core$(COV)
BIN := $(T)/bin$(COV)

CORE_COMMON := pdf.c ocr.cpp image.cpp pdfa.cpp
CORE_NATIVE := cli.cpp process.cpp

CORE_CFLAGS := $(OPT_FLAGS) $(COV_FLAGS) -I$(PREFIX)/include -Wall \
    -MMD -MP
CORE_CXXFLAGS := $(CORE_CFLAGS) -std=c++17
# With MinGW the static libraries are named libtesseract55.a and
# libleptonica-1.87.0.dll (sic); the patterns find them on every target
CORE_LIBS = -L$(PREFIX)/lib $(wildcard $(PREFIX)/lib/libtesseract*.a) \
    $(wildcard $(PREFIX)/lib/libleptonica*) -lmupdf -lmupdf-third -lz

core_objs = $(patsubst %,$(CORE_OBJ)/%.o,$(basename $(1)))

$(CORE_OBJ)/%.o: $(CORE_SRC)/%.c $(LIBS_STAMPS)
	mkdir -p $(@D)
	$(CC) $(CORE_CFLAGS) -c $< -o $@

$(CORE_OBJ)/%.o: $(CORE_SRC)/%.cpp $(LIBS_STAMPS)
	mkdir -p $(@D)
	$(CXX) $(CORE_CXXFLAGS) -c $< -o $@

-include $(wildcard $(CORE_OBJ)/*.d)

$(BIN)/ocr-pdf-core$(EXE): $(call core_objs,$(CORE_COMMON) $(CORE_NATIVE)) \
    $(CORE_OBJS_EXTRA)
	mkdir -p $(@D)
	$(CXX) -o $@ $^ $(CORE_LIBS) $(CORE_LDFLAGS)

$(BIN)/ocr-pdf-gs$(EXE): $(STAMP)/ghostscript
	mkdir -p $(@D)
	cp $(T)/src/ghostscript/bin/gs$(EXE) $@

TESSDATA_OUT := $(BIN)/tessdata

$(TESSDATA_OUT)/%.traineddata: $(TESSDATA_DIR)/%.traineddata
	mkdir -p $(@D)
	cp $< $@

core: $(BIN)/ocr-pdf-core$(EXE) $(BIN)/ocr-pdf-gs$(EXE) \
    $(TESSDATA_LANGS:%=$(TESSDATA_OUT)/%.traineddata)
