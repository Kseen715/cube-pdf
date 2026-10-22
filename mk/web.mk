# The web version: a static site with the core and Ghostscript compiled to
# WebAssembly, the page from web/ and the language models. It lands in
# $(DIST), ready for GitHub Pages.

WASM_OUT := $(T)/wasm
SITE_TESSDATA := tessdata/$(TESSDATA_VERSION)/

CORE_WASM_FLAGS := -lembind -sMODULARIZE=1 -sEXPORT_ES6=1 \
    -sEXPORT_NAME=OcrCore -sENVIRONMENT=worker -sALLOW_MEMORY_GROWTH=1 \
    -sMAXIMUM_MEMORY=4GB -sSTACK_SIZE=8MB -sFORCE_FILESYSTEM=1 \
    -sEXPORTED_RUNTIME_METHODS=FS

$(WASM_OUT)/ocr-core.js: $(call core_objs,$(CORE_COMMON) wasm.cpp)
	mkdir -p $(@D)
	$(CXX) -o $@ $^ $(CORE_LIBS) $(OPT_FLAGS) $(CORE_WASM_FLAGS)

$(WASM_OUT)/gs.js: $(STAMP)/ghostscript
	mkdir -p $(@D)
	cp $(T)/src/ghostscript/bin/gs.js $(T)/src/ghostscript/bin/gs.wasm $(@D)/

# The one value the page needs from deps/versions.mk
$(T)/build-info.js: deps/versions.mk
	mkdir -p $(@D)
	echo "export const TESSDATA_PATH = '$(SITE_TESSDATA)';" > $@

site: $(WASM_OUT)/ocr-core.js $(WASM_OUT)/gs.js $(T)/build-info.js \
    $(TESSDATA_LANGS:%=$(TESSDATA_DIR)/%.traineddata) $(NOTICES) \
    $(STAMP)/fonts
	rm -rf $(DIST)
	mkdir -p $(DIST)/wasm $(DIST)/$(SITE_TESSDATA)
	cp -r web/. $(DIST)/
	cp $(T)/build-info.js $(DIST)/js/
	rm -rf $(DIST)/fonts && cp -r $(FONTS_DIR) $(DIST)/fonts
	cp $(WASM_OUT)/*.js $(WASM_OUT)/*.wasm $(DIST)/wasm/
	cp $(TESSDATA_LANGS:%=$(TESSDATA_DIR)/%.traineddata) \
	    $(DIST)/$(SITE_TESSDATA)
	cp LICENSE $(DIST)/LICENSE.txt
	cp $(NOTICES) $(DIST)/THIRD-PARTY-NOTICES.txt
	cp assets/icon.png $(DIST)/icon.png

all: site

.PHONY: site
