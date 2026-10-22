# The desktop app: Tauri wraps the page from web/ and ships ocr-pdf-core,
# ocr-pdf-gs and the language models with it. The bundles land in $(DIST).
#
# Everything is staged under $(T)/stage, laid out like the repository, so
# the build never writes into the source tree.

STAGE := $(T)/stage
TAURI_BUNDLE := $(T)/cargo/$(TAURI_TRIPLE)/release/bundle
SIDECAR = $(STAGE)/desktop/binaries/$(1)-$(TAURI_TRIPLE)$(EXE)

# Crates and the downloaded MSVC runtime are kept in the build directory
TAURI_ENV_COMMON := CARGO_HOME=$(B)/cargo-home CARGO_TARGET_DIR=$(T)/cargo

$(STAMP)/stage: core $(NOTICES) $(STAMP)/fonts $(VERSION_JS) LICENSE \
    assets/icon.png $(shell find desktop web -type f)
	rm -rf $(STAGE)
	mkdir -p $(STAGE)/desktop/binaries
	cp -r desktop web $(STAGE)/
	cp $(VERSION_JS) $(STAGE)/web/js/
	rm -rf $(STAGE)/web/fonts && cp -r $(FONTS_DIR) $(STAGE)/web/fonts
	cp $(BIN)/ocr-pdf-core$(EXE) $(call SIDECAR,ocr-pdf-core)
	cp $(BIN)/ocr-pdf-gs$(EXE) $(call SIDECAR,ocr-pdf-gs)
	cp -r $(BIN)/tessdata $(STAGE)/desktop/
	for dir in desktop web; do \
	    cp LICENSE $(STAGE)/$$dir/LICENSE.txt; \
	    cp $(NOTICES) $(STAGE)/$$dir/THIRD-PARTY-NOTICES.txt; done
	cp assets/icon.png $(STAGE)/web/icon.png
	cd $(STAGE)/desktop && cargo tauri icon $(CURDIR)/assets/icon.png \
	    -o icons
	mkdir -p $(@D) && touch $@

$(STAMP)/desktop: $(STAMP)/stage
	cd $(STAGE)/desktop && $(TAURI_ENV_COMMON) $(TAURI_ENV) \
	    cargo tauri build --target $(TAURI_TRIPLE) \
	    --bundles $(TAURI_BUNDLES) $(TAURI_BUILD_FLAGS)
	rm -rf $(DIST)
	mkdir -p $(DIST)
	$(package_desktop)
	cp LICENSE $(NOTICES) $(DIST)/
	touch $@

desktop: $(STAMP)/desktop

all: desktop

.PHONY: desktop
