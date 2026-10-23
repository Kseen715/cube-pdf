# Agent rules

## Keep the legal information in sync with the code

CUBE-PDF ships third-party code in four builds (Windows, Linux, Android, web), so every release has to
carry correct license notices and the source code of its copyleft parts. These files hold that
information:

| File | What it holds |
| --- | --- |
| `LICENSE` | AGPL-3.0 text for this project's own code |
| `deps/versions.mk` | Every source tarball the build compiles, with URL and SHA-256; `SOURCE_PACKAGES` lists the ones every release attaches |
| `deps/patches/` | Our changes to upstream sources, applied while unpacking |
| `tools/collect_licenses.py` | `components()`: every component in the programs, with version, SPDX license, license files and source location, per target; `ALLOWED_LICENSES` for Rust crates; `ANDROID_GROUPS` for the Android libraries; the notices header |
| `desktop/gen/android/app/gradle.lockfile` | The Android libraries (AndroidX, Kotlin, ...) in the APK, pinned; the notices list them from here |
| `licenses/` | License files for what has no source tree in the build (the GCC and MinGW-w64 runtimes, the Apache-2.0 text of the Android libraries) |
| `web/js/config.js` | `SOURCE_URL`, shown in the app and in the notices |
| `web/js/dialogs.js` | `ABOUT`: copyright line, license statement, no-warranty statement |
| `mk/stage.mk`, `mk/desktop.mk`, `mk/apk.mk`, `mk/web.mk`, `mk/windows.mk`, `mk/linux.mk`, `.github/workflows/build.yml` | Put `LICENSE` and `THIRD-PARTY-NOTICES.txt` into every package and site, and attach them and the source tarballs (`make sources`) to releases |
| `README.md` | "What is inside" table, "License" section |

Treat the legal update as part of the change itself, made in the same commit and never left
for later.

### When you change a library or tool in `deps/versions.mk`

- Update its entry in `components()` in `tools/collect_licenses.py`. The libraries that
  MuPDF and Ghostscript bundle (FreeType, libjpeg, OpenJPEG, jbig2dec, lcms2, libpng, Brotli,
  extract) have their versions written there by hand: read them from the new source tree
  (`freetype.h`, `jversion.h`, `lcms2mt.h`, `opj_config_private.h`, `jbig2.h`, `png.h`,
  brotli's `version.h`) and update them.
- Check which third-party code the new version compiles in: `ls $B/<target>/build/mupdf/thirdparty`
  for MuPDF, the object files in `$B/<target>/src/ghostscript/obj` for Ghostscript. Every
  library found there needs a `components()` entry; remove the entries of the ones that are
  gone.
- License texts are read from the unpacked sources (`src:` paths). If a file moved, fix the
  path; never copy upstream license texts into this repository when the build has the source.
- Keep `deps/patches/` applying cleanly, and say in the notices header what they change.
- Update the README table when a major component's version changes.

### When you change the Rust crates of the desktop app (`desktop/Cargo.toml`)

- `collect_licenses.py` lists the crates from `cargo metadata` and stops the build when a crate
  is under a license outside `ALLOWED_LICENSES`. Only add a license to that set after checking
  that it allows combining with the AGPL-3.0. Never add proprietary, non-commercial,
  "no derivatives" or GPL-2.0-only licenses. If a license is unclear, stop and ask the user.
  Do not guess.
- Commit the updated `desktop/Cargo.lock`.

### When you change the Android libraries (`desktop/gen/android`)

- Gradle refuses to build with libraries other than those in `app/gradle.lockfile`. After
  changing a dependency, run `./gradlew :app:dependencies --write-locks` in the staged project
  (`out/android-arm64-v8a/stage/desktop/gen/android`) and commit the new lockfile.
- `collect_licenses.py` stops the build when a library comes from a Maven group outside
  `ANDROID_GROUPS`. Only add a group after checking the license of every library in it, by the
  same rules as for the crates.

### When you bundle anything new

This covers any new file in the packages (`mk/desktop.mk` and `mk/apk.mk` stage, `mk/web.mk`
site, Tauri `resources` and `externalBin`, the APK's `jniLibs` and `assets`), fonts, icons,
images and models.

- Give it a `components()` entry with its license and the targets it ships in.
- If its license is (A)GPL or LGPL, add its exact source tarball to `deps/versions.mk` and
  `SOURCE_PACKAGES`.
- Assets this project creates itself (such as `tools/make_assets.py` output) are covered by
  `LICENSE` and need no entry.
- Do not bundle libraries of the operating system (GTK, WebKitGTK, the Visual C++ runtime
  DLLs). That is why there is no AppImage: it would have to carry GTK and WebKitGTK and their
  LGPL sources. The MSVC runtime is linked statically; mention any other Microsoft component
  in the notices header.

### Things that must not be removed or weakened

- `LICENSE`, the About dialog (`showAbout` in `web/js/dialogs.js`, opened with F1 and the link
  at the bottom of the window) and its no-warranty text. The AGPL requires interactive programs
  to show these notices.
- Putting `LICENSE` and `THIRD-PARTY-NOTICES.txt` into the desktop packages and the web site,
  and attaching them and the source tarballs to releases in the workflow.
- The README sentence saying the project is not affiliated with OCRmyPDF, Tesseract,
  MuPDF or Ghostscript. Do not use those projects' names or logos as this product's name or
  icon.

### Keep these consistent

- `SOURCE_URL` in `web/js/config.js` must point at this repository. If the repository moves or
  is renamed, update it; `tools/collect_licenses.py` reads it.
- The copyright holder and year in `ABOUT` (`web/js/dialogs.js`), in `desktop/tauri.conf.json`
  and the license named there, in `LICENSE`, in the notices header and in the README "License"
  section must agree.
- Keep the files in `licenses/` exactly as upstream ships them. Do not edit their text.

### Before finishing a change that touches any of the above

1. Build the targets the change affects, for example `tools/docker-make.sh linux`; each
   regenerates `out/<target>/THIRD-PARTY-NOTICES.txt` and fails on a missing license file or a
   refused crate. `tools/docker-make.sh <target> notices` does only that step.
2. Read the "Components" list at the top of the notices and confirm that it matches what the
   programs contain.
3. If `deps/versions.mk` changed, run `make TARGET=wasm SOURCES_DIR=<scratch dir> sources` to
   confirm every URL downloads and its hash matches.
4. In the final message to the user, list what changed in the legal files.

## Code style

The code must stay easy to read, edit and extend by people. Read it first and match what
is already there.

- Code, scripts and config files keep lines at most 80 columns.
- A function fits in 40 lines. A longer one (up to 120-150 lines, rarely more) is allowed
  only when splitting it would make it harder to follow, and then a comment above it says why.
- Separate the logical blocks of a function with one empty line, for example: connect to
  the database, do the work, commit, disconnect.
- A block that more than one file needs goes into its own module, which they import.
- Code explains itself through names and structure. Comments say why the code is written
  this way, and only where it does something unusual. Never write a comment that repeats
  what the code does.
- Do not repeat yourself (DRY): one constant, helper or table per fact.
- Constants and shared variables go at the top of the file, under the imports, where
  possible.
- The OCR pipeline is one C/C++ code base (`core/src`) for every target. Code that calls
  MuPDF lives in C files (`pdf.c`): MuPDF reports errors with longjmp, which must never cross
  C++ frames. Platform code stays in `cli.cpp`/`process.cpp` (native) and `wasm.cpp` (web).
  C++ headers end in `.hpp`; `.h` is only for C headers such as `pdf.h`.
- The window is one page (`web/`) for every target; the engines (`engine-desktop.js`,
  `engine-web.js`) are the only place where the desktop and the web differ.
- Python tools (`tools/`) are formatted and linted with Ruff, configured in `ruff.toml`
  (80 columns, single quotes). Install it with
  `.venv\Scripts\python -m pip install -r requirements-dev.txt`, then run
  `.venv\Scripts\python -m ruff format .` and `.venv\Scripts\python -m ruff check .` before
  finishing a change. Both must pass.
- Tests live in `tests/`: `tests/tools` (unittest), `tests/web` (`node:test`) and
  `tests/core` (a C/C++ program, run with `tools/docker-make.sh linux test`). Add or update the
  tests of the part a change touches, and run that part's tests before finishing it (see the
  README, "Tests"). They must pass.
