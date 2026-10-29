# The typefaces of the window, Oswald, Manrope and JetBrains Mono: only the
# Latin and Cyrillic subsets the page uses. web.mk and desktop.mk put
# $(FONTS_DIR) next to the page as fonts/; web/app.css loads them from there.
# The tarballs are unpacked under $(T)/src, where collect_licenses.py reads
# their license.

FONTS_DIR := $(T)/fonts
FONT_SUBSETS := latin cyrillic

# $(call font_subsets,PACKAGE,NAME): unpack PACKAGE's tarball into
# $(T)/src/NAME and copy its subsets to $(FONTS_DIR)/NAME-latin.woff2 and
# so on
define font_subsets
	$(call unpack,$(1),$(T)/src/$(2))
	for s in $(FONT_SUBSETS); do \
	    cp $(T)/src/$(2)/files/$(2)-$$s-wght-normal.woff2 \
	        $(FONTS_DIR)/$(2)-$$s.woff2 || exit 1; \
	done
endef

$(STAMP)/fonts: $(FONT_FILES)
	rm -rf $(FONTS_DIR)
	mkdir -p $(FONTS_DIR)
	$(call font_subsets,OSWALD,oswald)
	$(call font_subsets,MANROPE,manrope)
	$(call font_subsets,JETBRAINS_MONO,jetbrains-mono)
	mkdir -p $(@D) && touch $@
