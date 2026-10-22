# The typefaces of the window, IBM Plex Sans and IBM Plex Serif: only the
# Latin and Cyrillic subsets the page uses. web.mk and desktop.mk put
# $(FONTS_DIR) next to the page as fonts/; web/app.css loads them from there.
# The zips are unpacked under $(T)/src, where collect_licenses.py reads
# their license.

FONTS_DIR := $(T)/fonts
FONT_SUBSETS := Latin1 Cyrillic

# $(call font_subsets,PACKAGE,NAME): copy the subsets of PACKAGE's zip to
# $(FONTS_DIR)/NAME-latin1.woff2 and so on
define font_subsets
	python3 -m zipfile -e $(DL)/$($(1)_FILE) $(T)/src/$(2)
	for s in $(FONT_SUBSETS); do \
	    cp "$(T)/src/$(2)/$($(1)_WOFF2)-$$s.woff2" \
	        "$(FONTS_DIR)/$(2)-$$(echo $$s | tr A-Z a-z).woff2" || exit 1; \
	done
endef

$(STAMP)/fonts: $(FONT_FILES)
	rm -rf $(FONTS_DIR) $(T)/src/plex-sans $(T)/src/plex-serif
	mkdir -p $(FONTS_DIR)
	$(call font_subsets,PLEX_SANS,plex-sans)
	$(call font_subsets,PLEX_SERIF,plex-serif)
	mkdir -p $(@D) && touch $@
