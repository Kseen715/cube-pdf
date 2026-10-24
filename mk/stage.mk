# The app shell, staged under $(STAGE) and laid out like the repository, so
# the app builds never write into the source tree: desktop/ and the page
# from web/ with its fonts, version, license and notices. mk/desktop.mk
# and mk/apk.mk add what their apps carry and build from there.

STAGE := $(T)/stage
# Cargo's own build folder, if one was made in desktop/, stays out
STAGE_SOURCES := $(shell find desktop web -path desktop/target -prune \
    -o -type f -print)
STAGE_DEPS := $(NOTICES) $(STAMP)/fonts $(VERSION_JS) LICENSE \
    assets/icon.png assets/icon-android.png assets/icon.json $(STAGE_SOURCES)

# Crates and the downloaded MSVC runtime are kept in the build directory
TAURI_ENV_COMMON := CARGO_HOME=$(B)/cargo-home CARGO_TARGET_DIR=$(T)/cargo

# $(call stage_app,ICON_FLAGS): stage the shell; ICON_FLAGS go to
# "cargo tauri icon", which writes the icons of the app from the manifest
# assets/icon.json
define stage_app
	rm -rf $(STAGE)
	mkdir -p $(STAGE)
	tar -c --exclude=desktop/target desktop web | tar -x -C $(STAGE)
	cp $(VERSION_JS) $(STAGE)/web/js/
	sed -i 's/^  "productName": .*/&\n  "version": "$(PACKAGE_VERSION)",/' \
	    $(STAGE)/desktop/tauri.conf.json
	rm -rf $(STAGE)/web/fonts && cp -r $(FONTS_DIR) $(STAGE)/web/fonts
	for dir in desktop web; do \
	    cp LICENSE $(STAGE)/$$dir/LICENSE.txt; \
	    cp $(NOTICES) $(STAGE)/$$dir/THIRD-PARTY-NOTICES.txt; done
	cp assets/icon.png $(STAGE)/web/icon.png
	cd $(STAGE)/desktop && cargo tauri icon $(CURDIR)/assets/icon.json $(1)
endef
