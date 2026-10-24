# CUBE-PDF

[![Coverage](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/Kseen715/cube-pdf/badges/coverage.json)](#tests)

Turns scans and photos of documents into searchable PDF/A files. You pick files, press one
button, and get `<name>_ocr.pdf`. The interface is in Russian.

One code base, four builds:

| Build | Where the OCR runs | Result |
| --- | --- | --- |
| Windows app (installer or portable zip) | natively, one Tesseract per CPU core | next to the original |
| Linux app (`.deb`, `.rpm`) | natively, one Tesseract per CPU core | next to the original |
| Android app (`.apk`, Android 10 and newer) | natively, one Tesseract per CPU core as memory allows | in Downloads |
| Web version (GitHub Pages) | in the browser: WebAssembly in Web Workers, on the visitor's CPU | downloaded with the file's button; files never leave the computer |

The web version gives the same text as the apps (same engine, same models). It is slower: a
24-page scan took 4.6 s in the Windows app and 7–12 s in Chromium on a 16-thread CPU. On the
first visit it also downloads about 70 MB of language models, which the browser then keeps.

## What is inside

| Component | Version | Used for |
| --- | --- | --- |
| [Tesseract](https://github.com/tesseract-ocr/tesseract) | 5.5.3 | OCR and page orientation |
| [tessdata](https://github.com/tesseract-ocr/tessdata) | 4.1.0 | `rus`, `eng`, `deu`, `osd` models |
| [Leptonica](https://github.com/DanBloomberg/leptonica) | 1.87.0 | deskewing, image handling for Tesseract |
| [MuPDF](https://mupdf.com) | 1.28.5 | reading PDFs and images, rendering pages, writing the text layer |
| [Ghostscript](https://ghostscript.com) | 10.08.0 | PDF/A-2b |
| [zlib](https://zlib.net) | 1.3.2 | compression |
| [Tauri](https://tauri.app) | 2.12 | the app window (WebView2 on Windows, WebKitGTK on Linux, Android System WebView) |
| [IBM Plex](https://github.com/IBM/plex) Sans and Serif | 0.2.0, 2.0.0 | the typefaces of the window |

`deps/versions.mk` pins every source tarball by SHA-256. The full list, with the libraries
MuPDF and Ghostscript bundle, is in each build's `THIRD-PARTY-NOTICES.txt`.

## How it works

```text
web/            the window: HTML/CSS/JS, the same page everywhere
  js/app.js        file list, options, progress, dialogs
  js/theme.js      light, dark or the system's theme
  js/engine-desktop.js   runs ocr-pdf-core through Tauri (desktop)
  js/engine-android.js   runs ocr-pdf-core through the app's commands (Android)
  js/engine-web.js       runs the WebAssembly core in Web Workers (browser)
  js/update.js           finds a newer release on GitHub, for both apps
  js/core.js             ocr-pdf-core's options and messages, for both apps
core/src/       the OCR pipeline, C/C++, compiled natively and to WebAssembly
  pdf.c            MuPDF: images to PDF, page analysis, rendering, text layers
  ocr.cpp          Tesseract and Leptonica: orientation, deskew, OCR per page
  pdfa.cpp         Ghostscript's PDF/A arguments
  cli.cpp          ocr-pdf-core: pages in parallel threads, JSON progress
  wasm.cpp         the same steps for the Web Workers
desktop/        the Tauri shell, no OCR logic
  src/android.rs   starts ocr-pdf-core on Android, which has no shell plugin
  src/update.rs    downloads and installs an update
  gen/android/     the Android project; AndroidPlugin.kt: file picker, Downloads
deps/           pinned sources and our patches
mk/, Makefile   the build, one fragment per step and per target
docker/         the four toolchains (Linux, Windows cross-compile, Emscripten,
                Android NDK and SDK)
```

For each file:

1. **Prepare.** A PDF is used as it is; a JPEG, PNG or TIFF becomes a PDF page as large as the
   image is at its resolution (300 dpi when the file has none). JPEGs are kept as they are.
2. **OCR each page**, in parallel:
   - pages that already have text are skipped, unless "Распознать заново" is ticked;
   - the page is rendered at the resolution of its sharpest image (300–600 dpi);
   - Tesseract's orientation detection turns it upright when it is sure (threshold 14, as in
     OCRmyPDF);
   - with "Выпрямлять", Leptonica straightens it;
   - Tesseract writes an invisible text layer (its own text-only PDF renderer, as OCRmyPDF
     uses).
3. **Assemble.** Each text layer is placed over its page in a copy of the PDF, so the
   original images stay untouched. Pages that were straightened, or whose old text was
   replaced, get the new image.
4. **PDF/A.** Ghostscript converts the result to PDF/A-2b, keeping JPEGs as they are and
   compressing everything else losslessly. If that fails, the result is a regular PDF.

The desktop app starts `ocr-pdf-core` once per file, so **Stop** simply ends that process (on
Windows a job object takes Ghostscript with it). The result is written next to the original
only when it is complete. On Windows, a manifest switches the programs to UTF-8, so paths
with Cyrillic letters work.

The Android app runs the same `ocr-pdf-core` and Ghostscript, built with the NDK for
`arm64-v8a` and `x86_64`. Android only lets an app run programs from its native library
folder, so the APK carries them as `libocr_pdf_core.so` and `libocr_pdf_gs.so`. The app copies
the picked file into its cache, runs the core there and saves the result to Downloads. OCR
runs while the app is open: Android pauses apps in the background.

### Updates

At start the apps ask GitHub for the latest release of this repository; that and the download
of an update are all they do over the network, and files never leave the device. When it is
newer than the app, an arrow appears next to the version at the bottom of the window. Pressing
it shows both versions and asks whether to update. On yes the app downloads the release's file
for the way it was installed and installs it:

| Installed from | Downloads | Installs |
| --- | --- | --- |
| Windows installer | `-windows-x86_64.exe` | runs it in passive mode, which closes the app and starts the new version |
| `.deb` / `.rpm` | the same kind of package | `pkexec dpkg -i` / `pkexec rpm -U` (asks for the password), then restarts the app |
| Android APK | `-android-universal.apk` | the system's package installer, which asks first (and, the first time, for the right to install apps from CUBE-PDF) |

The portable zip, and a copy not installed from a package, cannot replace itself: the arrow
opens the release's page instead. The web version is always the latest and does not check.

## Building

Everything is built from source inside Docker, the same way locally and in CI. You need
Docker and `make`; nothing else is installed on the machine.

```sh
tools/docker-make.sh linux     # dist/linux: .deb, .rpm
tools/docker-make.sh windows   # dist/windows: installer, portable zip
tools/docker-make.sh wasm      # dist/wasm: the static web site
tools/docker-make.sh android   # dist/android: the APK
```

The Android build compiles the libraries once per ABI, in `out/android-<abi>`. Its APK is
signed when `ANDROID_KEYSTORE` names a keystore in the build directory (as
`/build/release.jks`), with `ANDROID_KEYSTORE_PASSWORD`, `ANDROID_KEY_ALIAS` and
`ANDROID_KEY_PASSWORD`; otherwise it is unsigned. The libraries the APK takes from Maven are
pinned in `desktop/gen/android/app/gradle.lockfile`; after changing them, run
`./gradlew :app:dependencies --write-locks` in the staged project and commit the file.

The first build of a target takes 15–30 minutes (Docker image, libraries, Rust crates); later
ones only rebuild what changed. The build directory is `out/`. Under WSL, a named Docker volume
is much faster: `OCR_BUILD=ocr-build tools/docker-make.sh linux`.

Other goals, passed after the target:

- `core`: only `ocr-pdf-core`, `ocr-pdf-gs` and the models, in `out/<target>/bin`
- `notices`: only `THIRD-PARTY-NOTICES.txt`
- `test` (Linux only): the core's tests, see [Tests](#tests)
- `sources`: the source tarballs that every release attaches

`ocr-pdf-core` can be used on its own:

```sh
ocr-pdf-core run --input scan.pdf --output scan_ocr.pdf --languages rus+eng [--deskew] [--force]
```

To try the web version locally, serve `dist/wasm` with any static server, for example
`python -m http.server -d dist/wasm`.

### GitHub Actions

`.github/workflows/check.yml` runs Ruff and the tests of `tools/` and `web/` on every push to
`main` and every pull request; `core.yml` runs the core's tests when the core or what it is built
from changes. On `main` both measure the tests' coverage and commit it to the `badges` branch,
which the coverage badge above reads through shields.io. `.github/workflows/build.yml` builds all
four targets for tags that start with `v`, when started by hand from the Actions tab, and on
`main` when what its caches come from changes (`deps/`, `docker/`, `mk/`, the `Makefile`,
`desktop/Cargo.lock`, `desktop/gen/android/`), so the next tag starts from warm caches. A tag also publishes the web version on GitHub Pages; this needs
**Settings → Pages → Source: GitHub Actions** once, and the tag rule `v*` in **Settings →
Environments → github-pages → Deployment branches and tags**. A tag also creates a GitHub release
with:

- the apps, named `CUBE-PDF-<version>-<platform>[-<libc>]-<arch>.<extension>`: the Windows
  installer (`-windows-x86_64.exe`) and portable zip (`-windows-x86_64.zip`), the Linux
  `-linux-glibc-x86_64.deb` and `.rpm`, the Android `-android-universal.apk`, the web site as
  `-web-wasm32.zip`
- `LICENSE` and the `THIRD-PARTY-NOTICES-<target>.txt` files
- the source tarballs of everything compiled into the programs

The apps take their version from the latest tag `v<x.y.z>`, so a release needs no version bump in
the code; builds after the tag show it with the commit, such as `v2.2.1+b4c2406`.

```sh
git tag v2.2.1
git push origin v2.2.1
```

The APK is signed when the repository has the secrets `ANDROID_KEYSTORE_BASE64` (the keystore,
base64-encoded), `ANDROID_KEYSTORE_PASSWORD`, `ANDROID_KEY_ALIAS` and `ANDROID_KEY_PASSWORD`.

### Tools

`tools/` holds Python scripts: `collect_licenses.py` (run by the build) and `make_assets.py`,
which draws `assets/icon.png`. They are formatted and linted with
[Ruff](https://docs.astral.sh/ruff/) (settings in `ruff.toml`):

```sh
python -m pip install -r requirements-dev.txt
python -m ruff format .
python -m ruff check .
```

### Tests

`tests/` holds the tests of each part, with no test framework to install:

```sh
python -m unittest discover -s tests/tools   # tools/ and the legal files
node --test tests/web/*.test.js              # the page's logic (web/js)
tools/docker-make.sh linux test              # the OCR core, end to end
```

The core's tests (`tests/core`) are a C/C++ program, `out/linux/test-core`, linked with the
core and run against the built `ocr-pdf-core`, Ghostscript and language models: they make PDFs
and scans of a page of text with MuPDF and check what comes out, including Tesseract's
recognition and PDF/A. The window's DOM, the engines and the Rust shell are not tested; the
builds cover them.

The coverage badge counts the lines of `tools/`, of the files in `web/js` that the tests import
and of `core/src` that the tests run, all suites together. To measure it locally:

```sh
python -m coverage run --source=tools -m unittest discover -s tests/tools
python -m coverage report
node --test --experimental-test-coverage --test-coverage-include='web/js/**' tests/web/*.test.js
tools/docker-make.sh linux coverage          # writes out/linux/coverage/core.lcov
```

## License

CUBE-PDF is licensed under the GNU Affero General Public License v3.0 or later (see `LICENSE`).
It is built from third-party software under its own licenses: MuPDF and Ghostscript
(AGPL-3.0), Tesseract (Apache-2.0), Leptonica (BSD-2-Clause), Tauri (MIT/Apache-2.0), in the
Android app also AndroidX and Kotlin (Apache-2.0), and others. `THIRD-PARTY-NOTICES.txt` lists every component of a build with its full license text;
the app shows it under **О программе и лицензиях** (F1). Releases attach the exact source code
of every library in the programs.

There is no AppImage: it would have to carry GTK, WebKitGTK and their dependencies. The `.deb`
and `.rpm` packages use the distribution's own copies instead.

CUBE-PDF is not affiliated with or endorsed by the OCRmyPDF, Tesseract, MuPDF or Ghostscript
projects.

## Как пользоваться

1. Установите программу (Windows: `CUBE-PDF-…-windows-x86_64.exe` или распакуйте
   `CUBE-PDF-…-windows-x86_64.zip`; Linux: `.deb` или `.rpm`; Android:
   `CUBE-PDF-…-android-universal.apk`), либо откройте веб-версию в браузере. Можно сразу
   перетащить PDF или папку на значок программы.
2. Нажмите на рамку «Перетащите сюда файлы или папку» (на телефоне — «Выберите файлы») и
   выберите файлы, или перетащите их (или папку) в окно. Подходят PDF, JPG, PNG и TIFF.
3. Отметьте языки текста.
4. Нажмите кнопку **Начать распознавание**.
5. Готовый файл `имя_ocr.pdf` появится рядом с исходным (в веб-версии — скачивается кнопкой
   **Скачать** в строке файла, на Android — сохраняется в папку «Загрузки»). Исходный файл не
   меняется.

Когда выходит новая версия, внизу окна рядом с номером версии появляется стрелка. Нажмите её,
чтобы скачать и установить обновление.
