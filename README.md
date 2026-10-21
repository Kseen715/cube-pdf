# OCR-PDF

Turns scans and photos of documents into searchable PDF/A files. You pick files, press one
button, and get `<name>_ocr.pdf`. The interface is in Russian.

One code base, three builds:

| Build | Where the OCR runs | Result |
| --- | --- | --- |
| Windows app (installer or portable zip) | natively, one Tesseract per CPU core | next to the original |
| Linux app (`.deb`, `.rpm`) | natively, one Tesseract per CPU core | next to the original |
| Web version (GitHub Pages) | in the browser: WebAssembly in Web Workers, on the visitor's CPU | downloaded; files never leave the computer |

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
| [Tauri](https://tauri.app) | 2.12 | the desktop window (WebView2 on Windows, WebKitGTK on Linux) |

`deps/versions.mk` pins every source tarball by SHA-256. The full list, with the libraries
MuPDF and Ghostscript bundle, is in each build's `THIRD-PARTY-NOTICES.txt`.

## How it works

```text
web/            the window: HTML/CSS/JS, the same page everywhere
  js/app.js        file list, options, progress, dialogs
  js/engine-desktop.js   runs ocr-pdf-core through Tauri (desktop)
  js/engine-web.js       runs the WebAssembly core in Web Workers (browser)
core/src/       the OCR pipeline, C/C++, compiled natively and to WebAssembly
  pdf.c            MuPDF: images to PDF, page analysis, rendering, text layers
  ocr.cpp          Tesseract and Leptonica: orientation, deskew, OCR per page
  pdfa.cpp         Ghostscript's PDF/A arguments
  cli.cpp          ocr-pdf-core: pages in parallel threads, JSON progress
  wasm.cpp         the same steps for the Web Workers
desktop/        the Tauri shell: plugins only, no OCR logic
deps/           pinned sources and our patches
mk/, Makefile   the build, one fragment per step and per target
docker/         the three toolchains (Linux, Windows cross-compile, Emscripten)
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

## Building

Everything is built from source inside Docker, the same way locally and in CI. You need
Docker and `make`; nothing else is installed on the machine.

```sh
tools/docker-make.sh linux     # dist/linux: .deb, .rpm
tools/docker-make.sh windows   # dist/windows: installer, portable zip
tools/docker-make.sh wasm      # dist/wasm: the static web site
```

The first build of a target takes 15–30 minutes (Docker image, libraries, Rust crates); later
ones only rebuild what changed. The build directory is `out/`. Under WSL, a named Docker volume
is much faster: `OCR_BUILD=ocr-build tools/docker-make.sh linux`.

Other goals, passed after the target:

- `core`: only `ocr-pdf-core`, `ocr-pdf-gs` and the models, in `out/<target>/bin`
- `notices`: only `THIRD-PARTY-NOTICES.txt`
- `sources`: the source tarballs that every release attaches

`ocr-pdf-core` can be used on its own:

```sh
ocr-pdf-core run --input scan.pdf --output scan_ocr.pdf --languages rus+eng [--deskew] [--force]
```

To try the web version locally, serve `dist/wasm` with any static server, for example
`python -m http.server -d dist/wasm`.

### GitHub Actions

`.github/workflows/build.yml` builds all three targets for every push and pull request.
Pushes to `main` also publish the web version on GitHub Pages; this needs **Settings → Pages →
Source: GitHub Actions** once. Pushing a tag that starts with `v` creates a GitHub release with:

- the Windows installer and portable zip, the Linux `.deb` and `.rpm`, the web site as a zip
- `LICENSE` and the `THIRD-PARTY-NOTICES-<target>.txt` files
- the source tarballs of everything compiled into the programs

```sh
git tag v2.0.0
git push origin v2.0.0
```

### Tools

`tools/` holds Python scripts: `collect_licenses.py` (run by the build) and `make_assets.py`,
which draws `assets/icon.png`. They are formatted and linted with
[Ruff](https://docs.astral.sh/ruff/) (settings in `ruff.toml`):

```sh
python -m pip install -r requirements-dev.txt
python -m ruff format .
python -m ruff check .
```

## License

OCR-PDF is licensed under the GNU Affero General Public License v3.0 or later (see `LICENSE`).
It is built from third-party software under its own licenses: MuPDF and Ghostscript
(AGPL-3.0), Tesseract (Apache-2.0), Leptonica (BSD-2-Clause), Tauri (MIT/Apache-2.0) and
others. `THIRD-PARTY-NOTICES.txt` lists every component of a build with its full license text;
the app shows it under **О программе и лицензиях** (F1). Releases attach the exact source code
of every library in the programs.

There is no AppImage: it would have to carry GTK, WebKitGTK and their dependencies. The `.deb`
and `.rpm` packages use the distribution's own copies instead.

OCR-PDF is not affiliated with or endorsed by the OCRmyPDF, Tesseract, MuPDF or Ghostscript
projects.

## Как пользоваться

1. Установите программу (Windows: `OCR-PDF_…_x64-setup.exe` или распакуйте zip; Linux: `.deb`
   или `.rpm`), либо откройте веб-версию в браузере. Можно сразу перетащить PDF или папку на
   значок программы.
2. Нажмите на большую рамку и выберите файлы, или перетащите их (или папку) в окно. Подходят
   PDF, JPG, PNG и TIFF.
3. Отметьте языки текста.
4. Нажмите зелёную кнопку **НАЧАТЬ РАСПОЗНАВАНИЕ**.
5. Готовый файл `имя_ocr.pdf` появится рядом с исходным (в веб-версии — скачается). Исходный
   файл не меняется.
