# Android build for one ABI ($(ABI)), cross-compiled with the NDK in
# docker/android.Dockerfile. The programs need Android 10 (API 29): from
# there on, the app saves to Downloads without storage permissions.

ANDROID_API := 29
HOST_arm64-v8a := aarch64-linux-android
HOST_x86_64 := x86_64-linux-android
HOST := $(HOST_$(ABI))
PACKAGE := apk
EXE :=
NDK_BIN := $(NDK_HOME)/toolchains/llvm/prebuilt/linux-x86_64/bin
CC := $(NDK_BIN)/$(HOST)$(ANDROID_API)-clang
CXX := $(NDK_BIN)/$(HOST)$(ANDROID_API)-clang++
RANLIB := $(NDK_BIN)/llvm-ranlib
AR := $(NDK_BIN)/llvm-ar
CMAKE := cmake \
    -DCMAKE_TOOLCHAIN_FILE=$(NDK_HOME)/build/cmake/android.toolchain.cmake \
    -DANDROID_ABI=$(ABI) -DANDROID_PLATFORM=$(ANDROID_API)
OPT_FLAGS := -O2

MUPDF_TARGET_FLAGS := OS=Android CC=$(CC) CXX=$(CXX) AR=$(AR) \
    HAVE_X11=no HAVE_GLUT=no HAVE_OBJCOPY=no
MUPDF_TARGET_DEFINES :=
TESSERACT_TARGET_CMAKE :=

GS_TARGET_FLAGS := --host=$(HOST) --build=x86_64-pc-linux-gnu CCAUX=gcc \
    CC=$(CC) AR=$(AR) RANLIB=$(RANLIB)

# libc++ is linked statically: the APK carries no libc++_shared.so.
# Tesseract writes its messages to the Android log (liblog).
CORE_LDFLAGS := -static-libstdc++ -pthread -llog
CORE_OBJS_EXTRA :=
