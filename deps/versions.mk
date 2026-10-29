# Every third-party source the build downloads, with its SHA-256.
# tools/collect_licenses.py and tools/sources.sh read this file too, so it is
# the single list of what goes into the programs. Keep to plain
# "NAME := value" lines; a long value goes on the next line after a "\".

GH := https://github.com

TESSERACT_VERSION := 5.5.3
TESSERACT_HOME := $(GH)/tesseract-ocr/tesseract
TESSERACT_URL := \
    $(TESSERACT_HOME)/archive/refs/tags/$(TESSERACT_VERSION).tar.gz
TESSERACT_FILE := tesseract-$(TESSERACT_VERSION).tar.gz
TESSERACT_SHA256 := \
    9218e62793116d42a9f6d14cd9348518b27f382096eea3d0f2d1a24616bb5884

LEPTONICA_VERSION := 1.87.0
LEPTONICA_HOME := $(GH)/DanBloomberg/leptonica
LEPTONICA_FILE := leptonica-$(LEPTONICA_VERSION).tar.gz
LEPTONICA_URL := \
    $(LEPTONICA_HOME)/releases/download/$(LEPTONICA_VERSION)/$(LEPTONICA_FILE)
LEPTONICA_SHA256 := \
    c73363397f96eb1295602bf44d708a994ad42046c791bf03ea0505d829bdb6a7

MUPDF_VERSION := 1.28.5
MUPDF_HOME := https://mupdf.com
MUPDF_FILE := mupdf-$(MUPDF_VERSION)-source.tar.gz
MUPDF_URL := $(MUPDF_HOME)/downloads/archive/$(MUPDF_FILE)
MUPDF_SHA256 := \
    98a5c10cda20c3992cdf76ff6b2a1149c32bd79cc796d3f703230b1185b7e934

GHOSTSCRIPT_VERSION := 10.08.0
GHOSTSCRIPT_HOME := $(GH)/ArtifexSoftware/ghostpdl-downloads
GHOSTSCRIPT_FILE := ghostscript-$(GHOSTSCRIPT_VERSION).tar.xz
GHOSTSCRIPT_URL := \
    $(GHOSTSCRIPT_HOME)/releases/download/gs10080/$(GHOSTSCRIPT_FILE)
GHOSTSCRIPT_SHA256 := \
    c20492bc8ebb96c87fa2e52a0926e1cda8cde95d66145e018ac713fed5da38cf

ZLIB_VERSION := 1.3.2
ZLIB_HOME := $(GH)/madler/zlib
ZLIB_FILE := zlib-$(ZLIB_VERSION).tar.gz
ZLIB_URL := $(ZLIB_HOME)/releases/download/v$(ZLIB_VERSION)/$(ZLIB_FILE)
ZLIB_SHA256 := \
    bb329a0a2cd0274d05519d61c667c062e06990d72e125ee2dfa8de64f0119d16

# "tessdata" (not _fast/_best): the models Tesseract's own docs recommend
TESSDATA_VERSION := 4.1.0
TESSDATA_HOME := $(GH)/tesseract-ocr/tessdata
TESSDATA_URL := $(TESSDATA_HOME)/raw/$(TESSDATA_VERSION)
TESSDATA_LANGS := eng rus deu ita osd
TESSDATA_eng_SHA256 := \
    daa0c97d651c19fba3b25e81317cd697e9908c8208090c94c3905381c23fc047
TESSDATA_rus_SHA256 := \
    681be2c2bead1bc7bd235df88c44e8e60ae73ae866840c0ad4e3b4c247bd37c2
TESSDATA_deu_SHA256 := \
    896b3b4956503ab9daa10285db330881b2d74b70d889b79262cc534b9ec699a4
TESSDATA_ita_SHA256 := \
    4f7476c611312beb8f8e182888da08ea642d9824ae4402cc6235f61ab1406406
TESSDATA_osd_SHA256 := \
    e19f2ae860792fdf372cf48d8ce70ae5da3c4052962fe22e9de1f680c374bb0e

# Compiled into the programs; every release attaches these tarballs
SOURCE_PACKAGES := TESSERACT LEPTONICA MUPDF GHOSTSCRIPT ZLIB

# The typefaces of the window (SIL OFL 1.1), as Fontsource packs them for
# npm: each tarball holds the variable font split into script subsets,
# files/<name>-<subset>-wght-normal.woff2, and the font's LICENSE.
# *_HOME is the font's own project.
FONTSOURCE := https://registry.npmjs.org/@fontsource-variable

OSWALD_VERSION := 5.3.0
OSWALD_FILE := oswald-$(OSWALD_VERSION).tgz
OSWALD_URL := $(FONTSOURCE)/oswald/-/$(OSWALD_FILE)
OSWALD_SHA256 := \
    962bdb468592daece384e9e32d90eb84344301135488ff7adabff88443da6700
OSWALD_HOME := $(GH)/googlefonts/OswaldFont

MANROPE_VERSION := 5.3.0
MANROPE_FILE := manrope-$(MANROPE_VERSION).tgz
MANROPE_URL := $(FONTSOURCE)/manrope/-/$(MANROPE_FILE)
MANROPE_SHA256 := \
    9629a2474e2bd73944d83392c856e268193d42c3954455bd6adb3d1ea74aa27a
MANROPE_HOME := $(GH)/sharanda/manrope

JETBRAINS_MONO_VERSION := 5.3.0
JETBRAINS_MONO_FILE := jetbrains-mono-$(JETBRAINS_MONO_VERSION).tgz
JETBRAINS_MONO_URL := $(FONTSOURCE)/jetbrains-mono/-/$(JETBRAINS_MONO_FILE)
JETBRAINS_MONO_SHA256 := \
    996fe6368a480c9ce15d4de22a2682b7c40b403718fee2b15e7272f244fd993f
JETBRAINS_MONO_HOME := $(GH)/JetBrains/JetBrainsMono

FONT_PACKAGES := OSWALD MANROPE JETBRAINS_MONO
