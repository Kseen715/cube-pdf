# PyInstaller spec: one self-contained OCR-PDF.exe with Python, Qt, OCRmyPDF,
# Tesseract (eng/rus/deu/osd) and Ghostscript inside.
# Build with build.ps1, which fetches vendor/ first.
# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['app.py'],
    pathex=['src'],
    # progress_plugin is loaded by name through OCRmyPDF's plugin manager;
    # worker and gui are imported inside functions
    hiddenimports=['ocr_app.progress_plugin', 'ocr_app.worker', 'ocr_app.gui'],
    datas=[('assets/app.ico', 'assets')],
    excludes=['PySide6.QtNetwork', 'PySide6.QtQml', 'PySide6.QtQuick'],
    noarchive=False,
)
# Copied verbatim: the programs and their DLLs must stay side by side
a.datas += Tree('vendor/tesseract', prefix='vendor/tesseract')
a.datas += Tree('vendor/ghostscript', prefix='vendor/ghostscript')

pyz = PYZ(a.pure)

splash = Splash(
    'assets/splash.png',
    binaries=a.binaries,
    datas=a.datas,
    text_pos=None,
    always_on_top=False,
)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    splash,
    splash.binaries,
    [],
    name='OCR-PDF',
    icon='assets/app.ico',
    console=False,
    upx=False,
    runtime_tmpdir=None,
)
