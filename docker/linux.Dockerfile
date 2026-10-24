# Linux toolchain: native libraries and the Tauri desktop app.
# Ubuntu 22.04 keeps the glibc baseline low, so the result also runs on
# older distributions.
FROM ubuntu:22.04

ARG RUST_VERSION=1.98.0
ARG TAURI_CLI_VERSION=2.12.4

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential cmake pkg-config curl ca-certificates xz-utils \
        file patchelf python3 git lcov \
        libwebkit2gtk-4.1-dev libgtk-3-dev librsvg2-dev libssl-dev \
        libayatana-appindicator3-dev libxdo-dev \
    && rm -rf /var/lib/apt/lists/*

ENV RUSTUP_HOME=/opt/rustup CARGO_HOME=/opt/cargo PATH=/opt/cargo/bin:$PATH
RUN curl -sSf https://sh.rustup.rs | sh -s -- -y --profile minimal \
        --default-toolchain $RUST_VERSION \
    && cargo install tauri-cli --version $TAURI_CLI_VERSION --locked \
    && rm -rf $CARGO_HOME/registry $CARGO_HOME/git

# The checkout is mounted from the host and owned by another user; git
# refuses to read such a repository unless it is trusted. The build reads
# the commit for the version shown in the window (mk/version.mk).
RUN git config --system --add safe.directory '*'
