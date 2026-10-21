# Windows toolchain, cross-compiling from Linux: MinGW-w64 for the C/C++
# libraries, cargo-xwin (clang + the MSVC CRT) for the Tauri desktop app,
# NSIS for its installer. Tesseract links "Ws2_32", which only matches the
# MinGW library on a case-insensitive file system, hence the link.
FROM debian:trixie

ARG RUST_VERSION=1.98.0
ARG TAURI_CLI_VERSION=2.12.4
ARG CARGO_XWIN_VERSION=0.23.1

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential cmake pkg-config curl ca-certificates xz-utils \
        file python3 git zip \
        g++-mingw-w64-x86-64-posix gcc-mingw-w64-x86-64-posix \
        clang lld llvm nsis \
    && rm -rf /var/lib/apt/lists/* \
    && update-alternatives --set x86_64-w64-mingw32-gcc \
        /usr/bin/x86_64-w64-mingw32-gcc-posix \
    && update-alternatives --set x86_64-w64-mingw32-g++ \
        /usr/bin/x86_64-w64-mingw32-g++-posix \
    && ln -s libws2_32.a /usr/x86_64-w64-mingw32/lib/libWs2_32.a

ENV RUSTUP_HOME=/opt/rustup CARGO_HOME=/opt/cargo PATH=/opt/cargo/bin:$PATH
RUN curl -sSf https://sh.rustup.rs | sh -s -- -y --profile minimal \
        --default-toolchain $RUST_VERSION \
        --target x86_64-pc-windows-msvc \
    && cargo install tauri-cli --version $TAURI_CLI_VERSION --locked \
    && cargo install cargo-xwin --version $CARGO_XWIN_VERSION --locked \
    && rm -rf $CARGO_HOME/registry $CARGO_HOME/git
