# OCR-PDF

A single-file Windows app (`OCR-PDF.exe`) that wraps [OCRmyPDF](https://github.com/ocrmypdf/OCRmyPDF).
The interface is in Russian. You pick scans, press one button, and get a searchable PDF next to
each original, named `<name>_ocr.pdf`. Nothing needs to be installed on the target PC.

## What is inside the exe

| Component | Version | Notes |
| --- | --- | --- |
| Python | 3.14 (the build machine's; CI uses 3.14) | embedded by PyInstaller |
| OCRmyPDF | 17.13.0 | plus pikepdf, pypdfium2, fpdf2, Pillow |
| Qt (PySide6-Essentials) | 6.12.0 | GUI |
| Tesseract | 5.5.3 (official Windows build) | `tessdata` 4.1.0: `rus`, `eng`, `deu`, `osd`; only the DLLs `tesseract.exe` loads |
| Ghostscript | 10.08.0 | fallback for PDF/A; MSVC runtime DLLs copied next to it |

`unpaper`, `jbig2enc` and `pngquant` are left out. They are optional in OCRmyPDF and only
matter for `--clean` and `--optimize 2/3`, which this app does not use.

## Building

You need Python 3.11+ and 7-Zip (`7z.exe` on PATH or in Program Files).

```powershell
powershell -ExecutionPolicy Bypass -File build.ps1
```

The script:

1. creates `.venv` and installs `requirements.txt`
2. runs `tools/fetch_vendor.py`, which downloads the Tesseract/Ghostscript installers and language
   files, checks them against pinned SHA-256 hashes, and unpacks them with 7-Zip into `vendor/`
   (no admin rights, nothing installed system-wide). Tesseract's training tools are dropped,
   together with the DLLs only they need (GLib, Pango, Cairo, ICU and so on).
3. runs `tools/collect_licenses.py`, which writes `build/THIRD-PARTY-NOTICES.txt`
4. runs `tools/make_assets.py`, which draws the icon and the splash image
5. runs PyInstaller with `ocr_app.spec`, producing `dist\OCR-PDF.exe`, and copies `LICENSE` and
   `THIRD-PARTY-NOTICES.txt` next to it

After pulling changes to `tools/fetch_vendor.py`, run `.venv\Scripts\python tools\fetch_vendor.py
--force` once, so `vendor/` is unpacked again.

### GitHub Actions

`.github/workflows/build.yml` runs `build.ps1` on `windows-latest` for every push and pull
request and uploads the exe as a workflow artifact. Pushing a tag that starts with `v` also
creates a GitHub release with:

- `OCR-PDF.exe`
- `LICENSE` and `THIRD-PARTY-NOTICES.txt`
- the exact source tarballs of the bundled copyleft code: Ghostscript (AGPL), GNU libiconv,
  gettext's libintl, libunistring, libidn2 (LGPL) and JBIG-KIT (GPL), all downloaded by
  `tools/fetch_vendor.py --sources`

```powershell
git tag v1.0.0
git push origin v1.0.0
```

When you update Tesseract or Ghostscript, update `SOURCES` in `tools/fetch_vendor.py` and the
versions in `NATIVE` in `tools/collect_licenses.py` too. The DLL versions can be read with
`tesseract --version` and from the DLLs' exported version symbols.

To work on the code without building, run `.venv\Scripts\python app.py` after the first build
(it reuses `vendor/`).

## How it works

- `src/ocr_app/gui.py` is the window. Each file is processed by starting the same exe again as
  `OCR-PDF.exe --worker <json>`, so the UI never freezes and **Stop** can kill a job.
- `src/ocr_app/worker.py` puts the bundled `tesseract` and `gswin64c` first on `PATH`, sets
  `TESSDATA_PREFIX`, and calls `ocrmypdf.ocr()`. It reports progress, log lines and errors as
  JSON lines on stdout (`ipc.py`, `progress_plugin.py`).
- Worker processes get the `CREATE_NO_WINDOW` flag, so Tesseract never flashes a console window.
  Each worker runs in a Windows job object (`winjob.py`), so Stop, or closing the app, also kills
  its Tesseract processes. Each worker also gets its own temp folder, which is deleted afterwards.
- A onefile child started this way reuses the parent's unpacked `_MEI*` folder. Only the first
  launch pays the unpacking cost, about 3–4 s.

OCRmyPDF settings used:

- the languages ticked in the UI (default: Russian + English)
- `mode=skip`: pages that already contain text are copied unchanged. The **Распознать заново**
  checkbox switches to `mode=force`.
- `rotate_pages=True`, plus optional `deskew`
- `output_type=auto`: PDF/A when that is possible without loss, otherwise a regular PDF
- `invalidate_digital_signatures=True`, because the original file keeps its signature
- `image_dpi=300` for images that have no usable DPI information

## GPU

GPU acceleration is not included. Tesseract runs only on the CPU, and OCRmyPDF already runs one
Tesseract per core. On a 16-thread CPU that came to about 4 pages/s on test scans. The only GPU options are
third-party engine plugins built on PyTorch (for example `ocrmypdf-easyocr`). They would add
3–4 GB to the exe and make every launch slower (the onefile has to unpack all of it each time),
and their text layer is less accurate than Tesseract's for Russian and German documents.

## License

OCR-PDF is licensed under the GNU Affero General Public License v3.0 or later (see `LICENSE`).
It bundles third-party software under its own licenses: OCRmyPDF (MPL-2.0), Tesseract
(Apache-2.0), Ghostscript (AGPL-3.0), Qt/PySide6 (LGPL-3.0) and others.
`THIRD-PARTY-NOTICES.txt` lists every component with its full license text; the app shows it under
**О программе и лицензиях** (F1). The license files of Tesseract's DLLs are kept in `licenses/`.

OCR-PDF is not affiliated with or endorsed by the OCRmyPDF, Tesseract or Ghostscript projects.

## Как пользоваться

1. Запустите `OCR-PDF.exe`. Можно сразу перетащить PDF на значок программы.
2. Нажмите на большую рамку и выберите файлы, или перетащите их в окно. Подходят PDF, JPG, PNG и TIFF.
3. Отметьте языки текста.
4. Нажмите зелёную кнопку **НАЧАТЬ РАСПОЗНАВАНИЕ**.
5. Готовый файл `имя_ocr.pdf` появится рядом с исходным. Исходный файл не меняется.
