# js/version.js: the version shown at the bottom of the window,
# v<version in desktop/Cargo.toml>+<commit>, with +dirty when tracked files
# have uncommitted changes. Built outside a git checkout, it is only
# v<version>.

VERSION_JS := $(T)/version.js

# Read only when the recipe runs; --no-optional-locks keeps git from
# rewriting the index of the checkout, which belongs to the host user
GIT = git --no-optional-locks
CARGO_VERSION = $(shell sed -n 's/^version = "\(.*\)"$$/\1/p' \
    desktop/Cargo.toml)
COMMIT = $(shell $(GIT) rev-parse --short HEAD 2>/dev/null)
DIRTY = $(shell $(GIT) diff --quiet HEAD -- || echo +dirty)
APP_VERSION = v$(CARGO_VERSION)$(if $(COMMIT),+$(COMMIT)$(DIRTY))

# Checked on every build, but rewritten only when the version changes, so
# the same version does not restage the desktop app
$(VERSION_JS): FORCE
	mkdir -p $(@D)
	echo "export const APP_VERSION = '$(APP_VERSION)';" > $@.new
	cmp -s $@.new $@ && rm $@.new || mv $@.new $@

FORCE:

.PHONY: FORCE
