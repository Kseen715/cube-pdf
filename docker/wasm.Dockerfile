# WebAssembly toolchain: Emscripten for the libraries and the web build.
FROM emscripten/emsdk:4.0.23

RUN apt-get update && apt-get install -y --no-install-recommends \
        pkg-config xz-utils file \
    && rm -rf /var/lib/apt/lists/*
