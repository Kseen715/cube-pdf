# The version comes from the latest tag v<x.y.z> that HEAD descends from:
# the packages carry x.y.z (PACKAGE_VERSION, written into the staged
# tauri.conf.json), and js/version.js, shown at the bottom of the window,
# holds v<x.y.z>+<commit>, with +dirty when tracked files have uncommitted
# changes. Without a tag, or outside a git checkout, the version is 0.0.0.

VERSION_JS := $(T)/version.js

# Read only when the recipe runs; --no-optional-locks keeps git from
# rewriting the index of the checkout, which belongs to the host user
GIT = git --no-optional-locks
TAG = $(shell $(GIT) describe --tags --abbrev=0 --match 'v[0-9]*' \
    2>/dev/null)
PACKAGE_VERSION = $(if $(TAG),$(TAG:v%=%),0.0.0)
COMMIT = $(shell $(GIT) rev-parse --short HEAD 2>/dev/null)
DIRTY = $(shell $(GIT) diff --quiet HEAD -- || echo +dirty)
APP_VERSION = v$(PACKAGE_VERSION)$(if $(COMMIT),+$(COMMIT)$(DIRTY))

# Checked on every build, but rewritten only when the version changes, so
# the same version does not restage the desktop app
$(VERSION_JS): FORCE
	mkdir -p $(@D)
	echo "export const APP_VERSION = '$(APP_VERSION)';" > $@.new
	cmp -s $@.new $@ && rm $@.new || mv $@.new $@

FORCE:

.PHONY: FORCE
