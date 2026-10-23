# The desktop app: Tauri wraps the page from web/ and ships ocr-pdf-core,
# ocr-pdf-gs and the language models with it. The bundles land in $(DIST).

include mk/stage.mk

TAURI_BUNDLE := $(T)/cargo/$(TAURI_TRIPLE)/release/bundle
SIDECAR = $(STAGE)/desktop/binaries/$(1)-$(TAURI_TRIPLE)$(EXE)

$(STAMP)/stage: core $(STAGE_DEPS)
	$(call stage_app,-o icons)
	mkdir -p $(STAGE)/desktop/binaries
	cp $(BIN)/ocr-pdf-core$(EXE) $(call SIDECAR,ocr-pdf-core)
	cp $(BIN)/ocr-pdf-gs$(EXE) $(call SIDECAR,ocr-pdf-gs)
	cp -r $(BIN)/tessdata $(STAGE)/desktop/
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
