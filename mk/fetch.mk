# Downloads into $(DL), checked against the SHA-256 in deps/versions.mk

# $(call download,URL,SHA256): fetch URL into $@ unless it is already there
define download
	mkdir -p $(@D)
	curl -fsSL --retry 3 -o $@.part '$(1)'
	echo '$(2)  $@.part' | sha256sum -c --quiet -
	mv $@.part $@
endef

$(foreach p,$(SOURCE_PACKAGES) $(FONT_PACKAGES),$(eval \
    $(DL)/$($(p)_FILE): ; $$(call download,$($(p)_URL),$($(p)_SHA256))))

TESSDATA_DIR := $(DL)/tessdata-$(TESSDATA_VERSION)
TESSDATA_FILES := $(TESSDATA_LANGS:%=$(TESSDATA_DIR)/%.traineddata)

$(TESSDATA_DIR)/%.traineddata:
	$(call download,$(TESSDATA_URL)/$*.traineddata,$(TESSDATA_$*_SHA256))

# $(call unpack,PACKAGE,DIR): a fresh copy of the tarball, with the patches
# from deps/patches/<package>-*.patch applied
define unpack
	rm -rf $(2) && mkdir -p $(2)
	tar xf $(DL)/$($(1)_FILE) -C $(2) --strip-components=1
	for p in $(wildcard deps/patches/$(call lc,$(1))-*.patch); do \
	    patch -d $(2) -p1 < $$p || exit 1; done
endef

lc = $(shell echo $(1) | tr A-Z a-z)

SOURCE_FILES := $(foreach p,$(SOURCE_PACKAGES),$(DL)/$($(p)_FILE))
FONT_FILES := $(foreach p,$(FONT_PACKAGES),$(DL)/$($(p)_FILE))
SOURCES_DIR ?= $(DIST)/sources

downloads: $(SOURCE_FILES) $(FONT_FILES) $(TESSDATA_FILES)

# The source of everything compiled into the programs, for releases
sources: $(SOURCE_FILES)
	mkdir -p $(SOURCES_DIR)
	cp $^ $(SOURCES_DIR)/

.PHONY: downloads sources
