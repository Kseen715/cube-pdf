# Android toolchain: the NDK cross-compiles the C/C++ libraries and
# ocr-pdf-core for every ABI, the SDK, Gradle and Tauri build the APK.
# sdkmanager checks the hashes of the SDK packages itself.
FROM ubuntu:22.04

ARG RUST_VERSION=1.98.0
ARG TAURI_CLI_VERSION=2.12.4
ARG TOOLS_ZIP=commandlinetools-linux-16111833_latest.zip
# The SHA-256 of TOOLS_ZIP
ARG TOOLS_HASH=0877a1d048fe4a24efe2eff536ca4223f7adeb58648bb81909d33c446918cfa8
ARG NDK_VERSION=29.0.14206865
ARG ANDROID_PLATFORM=android-37.0
ARG BUILD_TOOLS=36.0.0

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential cmake pkg-config curl ca-certificates xz-utils \
        file python3 git unzip openjdk-17-jdk-headless \
    && rm -rf /var/lib/apt/lists/*

ENV ANDROID_HOME=/opt/android-sdk \
    JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
ENV NDK_HOME=$ANDROID_HOME/ndk/$NDK_VERSION
RUN curl -fsSL -o /tmp/tools.zip \
        https://dl.google.com/android/repository/$TOOLS_ZIP \
    && echo "$TOOLS_HASH  /tmp/tools.zip" | sha256sum -c - \
    && mkdir -p $ANDROID_HOME/cmdline-tools \
    && unzip -q /tmp/tools.zip -d $ANDROID_HOME/cmdline-tools \
    && mv $ANDROID_HOME/cmdline-tools/cmdline-tools \
        $ANDROID_HOME/cmdline-tools/latest \
    && rm /tmp/tools.zip \
    && yes | $ANDROID_HOME/cmdline-tools/latest/bin/sdkmanager --licenses \
        > /dev/null \
    && $ANDROID_HOME/cmdline-tools/latest/bin/sdkmanager --install \
        "ndk;$NDK_VERSION" "platforms;$ANDROID_PLATFORM" \
        "build-tools;$BUILD_TOOLS" platform-tools > /dev/null \
    && chmod -R a+rwX $ANDROID_HOME

ENV RUSTUP_HOME=/opt/rustup CARGO_HOME=/opt/cargo PATH=/opt/cargo/bin:$PATH
RUN curl -sSf https://sh.rustup.rs | sh -s -- -y --profile minimal \
        --default-toolchain $RUST_VERSION \
        --target aarch64-linux-android --target x86_64-linux-android \
    && cargo install tauri-cli --version $TAURI_CLI_VERSION --locked \
    && rm -rf $CARGO_HOME/registry $CARGO_HOME/git

# The checkout is mounted from the host and owned by another user; git
# refuses to read such a repository unless it is trusted. The build reads
# the commit for the version shown in the window (mk/version.mk).
RUN git config --system --add safe.directory '*'
