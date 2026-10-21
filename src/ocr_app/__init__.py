"""Windows GUI wrapper around OCRmyPDF with all dependencies bundled."""

APP_NAME = 'Распознавание PDF'
SOURCE_URL = 'https://github.com/Kseen715/ocrmypdf-app'
OUTPUT_SUFFIX = '_ocr'

# Tesseract code -> label shown in the UI, in display order
LANGUAGES = {
    'rus': 'Русский',
    'eng': 'Английский',
    'deu': 'Немецкий',
}

PDF_EXTENSIONS = {'.pdf'}
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.tif', '.tiff'}
INPUT_EXTENSIONS = PDF_EXTENSIONS | IMAGE_EXTENSIONS
