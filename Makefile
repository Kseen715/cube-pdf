# Builds CUBE-PDF from source, Unix style: every library is compiled from the
# tarball pinned in deps/versions.mk, with its own build system.
#
# Run it inside the matching toolchain container (docker/*.Dockerfile).
# From the host, tools/docker-make.sh does that for you:
#
#   tools/docker-make.sh linux     Linux desktop app (.deb, .AppImage)
#   tools/docker-make.sh windows   Windows desktop app (installer, .zip)
#   tools/docker-make.sh wasm      web version (a static site)
#
# Other goals: core (just ocr-pdf-core and the libraries), notices, clean.
# Finished packages land in dist/<target>/.

TARGET ?= linux
B ?= $(CURDIR)/out
DIST ?= $(CURDIR)/dist/$(TARGET)
JOBS ?= $(shell nproc)
# Independent libraries build in parallel; each target's output is printed
# in one piece, so a failure log stays readable
MAKEFLAGS += -j$(JOBS) --output-sync=target

T := $(B)/$(TARGET)
DL := $(B)/downloads
PREFIX := $(T)/prefix
STAMP := $(T)/stamp

.DEFAULT_GOAL := all
.DELETE_ON_ERROR:

include deps/versions.mk
include mk/$(TARGET).mk
include mk/fetch.mk
include mk/fonts.mk
include mk/deps.mk
include mk/core.mk
include mk/notices.mk
include mk/$(PACKAGE).mk

clean:
	rm -rf $(T) $(DIST)

.PHONY: all core clean
