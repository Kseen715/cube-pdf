# Native Linux build, run in docker/linux.Dockerfile

HOST := x86_64-linux-gnu
PACKAGE := desktop
EXE :=
CC := gcc
CXX := g++
RANLIB := ranlib
AR := ar
CMAKE := cmake
OPT_FLAGS := -O2

MUPDF_TARGET_FLAGS := HAVE_X11=no HAVE_GLUT=no
GS_TARGET_FLAGS :=
TESSERACT_TARGET_CMAKE :=

# Only glibc stays dynamic, so the binaries run on any newer distribution
CORE_LDFLAGS := -static-libstdc++ -static-libgcc -pthread
CORE_OBJS_EXTRA :=

TAURI_TRIPLE := x86_64-unknown-linux-gnu
# No AppImage: it would bundle GTK, WebKitGTK and their LGPL libraries,
# which the packages take from the distribution instead
TAURI_BUNDLES := deb,rpm

TAURI_ENV :=
TAURI_BUILD_FLAGS :=

define package_desktop
	cp $(TAURI_BUNDLE)/deb/*.deb $(TAURI_BUNDLE)/rpm/*.rpm $(DIST)/
endef
