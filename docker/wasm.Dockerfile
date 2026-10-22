# WebAssembly toolchain: Emscripten for the libraries and the web build.
FROM emscripten/emsdk:4.0.23

RUN apt-get update && apt-get install -y --no-install-recommends \
        pkg-config xz-utils file \
    && rm -rf /var/lib/apt/lists/*

# The checkout is mounted from the host and owned by another user; git
# refuses to read such a repository unless it is trusted. The build reads
# the commit for the version shown in the window (mk/version.mk).
RUN git config --system --add safe.directory '*'
