# THIRD-PARTY-NOTICES.txt: every component in this target's programs, with
# its license text. tools/collect_licenses.py reads the texts from the
# unpacked sources, so it runs after the libraries are built.

NOTICES := $(T)/THIRD-PARTY-NOTICES.txt

$(NOTICES): tools/collect_licenses.py deps/versions.mk web/js/config.js \
    $(wildcard licenses/* desktop/Cargo.*) $(LIBS_STAMPS) \
    $(STAMP)/ghostscript $(STAMP)/fonts
	mkdir -p $(@D)
	CXX=$(CXX) CARGO_HOME=$(B)/cargo-home \
	    python3 tools/collect_licenses.py $(TARGET) $(T) $@

notices: $(NOTICES)

.PHONY: notices
