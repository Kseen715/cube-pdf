# Agent rules

## Keep the legal information in sync with the code

OCR-PDF.exe redistributes third-party software, so every release has to carry correct
license notices and the source code of its copyleft parts. These files hold that information:

| File | What it holds |
| --- | --- |
| `LICENSE` | AGPL-3.0 text for this project's own code |
| `tools/collect_licenses.py` | `REQUIREMENTS` (top-level runtime Python packages), `NATIVE` (every bundled non-Python component, with version, SPDX license, license files and source location), `SOURCE_URL`, the notices header |
| `licenses/` | Upstream license files of the native libraries, referenced from `NATIVE` |
| `tools/fetch_vendor.py` | Pinned installers, plus `SOURCES`: exact source tarballs of every (A)GPL/LGPL native component, attached to each release |
| `src/ocr_app/__init__.py` | `SOURCE_URL` shown in the app |
| `src/ocr_app/gui.py` | `ABOUT`: copyright line, license statement, no-warranty statement |
| `ocr_app.spec`, `build.ps1`, `.github/workflows/build.yml` | Bundle `LICENSE` and `THIRD-PARTY-NOTICES.txt` into the exe, copy them to `dist/`, attach them and the sources to releases |
| `README.md` | "What is inside the exe" table, "License" section |

Treat the legal update as part of the change itself, made in the same commit and never left
for later.

### When you change Python dependencies (`requirements.txt`)

- The notices pick up transitive dependencies automatically. If you add a new **top-level**
  runtime package, add it to `REQUIREMENTS` in `tools/collect_licenses.py`. Build-only tools
  such as PyInstaller do not belong there.
- Check the new package's license (and its dependencies' licenses). This project is AGPL-3.0,
  so do not add anything proprietary, non-commercial, "no derivatives", or GPL-2.0-only.
  If a license is unclear, stop and ask the user. Do not guess.
- If the package ships native libraries whose license files are missing from its `.dist-info`
  (as with the Qt LGPL text in PySide6), add the missing text to the notices the way
  `collect_licenses.py` already does for PySide6.
- Update the README table when a major component's version changes.

### When you change Tesseract, tessdata or Ghostscript (`tools/fetch_vendor.py`)

- Update the versions in `NATIVE` in `tools/collect_licenses.py`.
- Run `tools/fetch_vendor.py --force`, then compare the DLLs in `vendor/tesseract/` with
  `NATIVE`:
  - Each new DLL needs a `NATIVE` entry and its upstream license file in `licenses/`,
    downloaded from the release tag that matches the bundled version.
  - Remove the entries and license files of DLLs that are gone.
  - `tesseract --version` prints most library versions. For the others, read the DLL's
    exported version symbol, for example `curl_version`, `_libiconv_version`,
    `_libunistring_version`, `libintl_version` or `idn2_check_version`.
- For every (A)GPL or LGPL component whose version changed, put the matching source tarball
  in `SOURCES`, with its SHA-256 hash. Keep the tarball file names in `NATIVE`'s "source"
  field matching.
- Check that `tesseract.exe` and `gswin64c.exe` still work after the DLL pruning by OCRing a
  test image through the built exe.

### When you bundle anything new

This covers any new file in `ocr_app.spec` `datas`/`binaries`, `vendor/`, fonts, icons,
images and models.

- Give it a `NATIVE` entry with its license, plus its license file in `licenses/`.
- If its license is (A)GPL or LGPL, add its exact source to `SOURCES`.
- Assets this project creates itself (such as `tools/make_assets.py` output) are covered by
  `LICENSE` and need no entry.
- Microsoft runtime DLLs may only be ones on Microsoft's Visual C++ redistributable list.
  Mention any new one in the notices header.

### Things that must not be removed or weakened

- `LICENSE`, the About dialog (`show_about`, F1) and its no-warranty text. The AGPL requires
  interactive programs to show these notices.
- Bundling `LICENSE` and `THIRD-PARTY-NOTICES.txt` in the spec, copying them in `build.ps1`,
  and attaching them and `dist/sources/*` to releases in the workflow.
- The README sentence saying the project is not affiliated with OCRmyPDF, Tesseract or
  Ghostscript. Do not use those projects' names or logos as this product's name or icon.

### Keep these consistent

- `SOURCE_URL` in `src/ocr_app/__init__.py` and `tools/collect_licenses.py` must both point at
  this repository. If the repository moves or is renamed, update both.
- The copyright holder and year in `ABOUT` (`src/ocr_app/gui.py`) and the license named there,
  in `LICENSE`, in the notices header and in the README "License" section must agree.
- Keep the files in `licenses/` exactly as upstream ships them. Do not edit their text.

### Before finishing a change that touches any of the above

1. Run `powershell -ExecutionPolicy Bypass -File build.ps1`. It must regenerate
   `build/THIRD-PARTY-NOTICES.txt` without errors.
2. Read the "Components" list at the top of the notices and confirm that it matches what the
   exe contains.
3. If `SOURCES` changed, run `python tools/fetch_vendor.py --sources <scratch dir>` to confirm
   every URL downloads and its hash matches.
4. In the final message to the user, list what changed in the legal files.
