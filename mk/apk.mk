# The Android app: Tauri wraps the page from web/ into an APK, which also
# carries ocr-pdf-core and Ghostscript for every ABI in $(ANDROID_ABIS)
# and the language models. The APK lands in $(DIST): signed when the
# environment names a keystore (desktop/gen/android/app/build.gradle.kts),
# unsigned otherwise.
#
# The build of the first ABI runs this; the other ABIs' programs come from
# make runs of their own, each in its own build directory.

include mk/stage.mk

ANDROID_PROJECT := $(STAGE)/desktop/gen/android
JNI_LIBS := $(ANDROID_PROJECT)/app/src/main/jniLibs
APK_DIR := $(ANDROID_PROJECT)/app/build/outputs/apk/universal/release
# Tauri's names for the Rust targets of the ABIs
TAURI_TARGET_arm64-v8a := aarch64
TAURI_TARGET_x86_64 := x86_64
# Gradle keeps what it downloads in the build directory, as Cargo does
APK_ENV := $(TAURI_ENV_COMMON) GRADLE_USER_HOME=$(B)/gradle-home

# The ABI builds share $(DL): fetch it here first, so that they never
# download the same file at the same time
abis: $(SOURCE_FILES) $(TESSDATA_FILES)
	+for abi in $(filter-out $(ABI),$(ANDROID_ABIS)); do \
	    $(MAKE) ABI=$$abi core || exit 1; done

# Android runs programs only from the APK's native library folder, so the
# programs go there under library names (desktop/src/android.rs)
$(STAMP)/stage: core abis $(STAGE_DEPS)
	$(call stage_app,)
	for abi in $(ANDROID_ABIS); do \
	    bin=$(B)/android-$$abi/bin; mkdir -p $(JNI_LIBS)/$$abi; \
	    $(NDK_BIN)/llvm-strip -o $(JNI_LIBS)/$$abi/libocr_pdf_core.so \
	        $$bin/ocr-pdf-core || exit 1; \
	    $(NDK_BIN)/llvm-strip -o $(JNI_LIBS)/$$abi/libocr_pdf_gs.so \
	        $$bin/ocr-pdf-gs || exit 1; done
	mkdir -p $(ANDROID_PROJECT)/app/src/main/assets
	cp -r $(BIN)/tessdata $(ANDROID_PROJECT)/app/src/main/assets/
	mkdir -p $(@D) && touch $@

$(STAMP)/apk: $(STAMP)/stage
	cd $(STAGE)/desktop && $(APK_ENV) cargo tauri android build --apk \
	    --target $(foreach abi,$(ANDROID_ABIS),$(TAURI_TARGET_$(abi)))
	rm -rf $(DIST)
	mkdir -p $(DIST)
	cp $(APK_DIR)/*.apk $(DIST)/
	cp LICENSE $(NOTICES) $(DIST)/
	touch $@

apk: $(STAMP)/apk

all: apk

.PHONY: abis apk
