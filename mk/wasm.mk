# WebAssembly build with Emscripten, run in docker/wasm.Dockerfile

HOST := wasm32-unknown-emscripten
PACKAGE := web
EXE := .js
CC := emcc
CXX := em++
RANLIB := emranlib
AR := emar
CMAKE := emcmake cmake
# MuPDF needs wasm exceptions and longjmp; everything shares the settings
WASM_FLAGS := -fwasm-exceptions -sSUPPORT_LONGJMP=wasm
OPT_FLAGS := -O3 -msimd128 $(WASM_FLAGS)

MUPDF_TARGET_FLAGS := OS=wasm
MUPDF_TARGET_DEFINES :=

# There is no cpuid in wasm: build only the SSE4.1 kernels, which Emscripten
# maps to wasm SIMD, and let the patched simddetect.cpp pick them
TESSERACT_TARGET_CMAKE := -DHAVE_AVX=OFF -DHAVE_AVX2=OFF -DHAVE_AVX512F=OFF \
    -DHAVE_FMA=OFF -DHAVE_SSE4_1=ON

# Ghostscript becomes an ES module whose main() web/js/worker.js calls
GS_LDFLAGS := $(WASM_FLAGS) -sMODULARIZE=1 -sEXPORT_ES6=1 \
    -sEXPORT_NAME=Ghostscript -sINVOKE_RUN=0 -sEXIT_RUNTIME=0 \
    -sALLOW_MEMORY_GROWTH=1 -sENVIRONMENT=worker \
    -sEXPORTED_RUNTIME_METHODS=callMain,FS
GS_CONFIGURE_ENV := emconfigure
GS_TARGET_FLAGS := --host=$(HOST) --build=x86_64-pc-linux-gnu CCAUX=gcc \
    --disable-threading --disable-sse2 --with-exe-ext=.js \
    LDFLAGS="$(GS_LDFLAGS)"
