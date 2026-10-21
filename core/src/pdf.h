/*
 * The PDF side of the OCR pipeline, built on MuPDF.
 *
 * This part is C on purpose: MuPDF reports errors with longjmp (fz_try,
 * fz_catch), which must never jump across C++ frames. Every function here
 * catches MuPDF's errors itself and returns an ocr_status instead.
 */
#ifndef OCR_PDF_H
#define OCR_PDF_H

#include <mupdf/fitz.h>
#include <mupdf/pdf.h>

#ifdef __cplusplus
extern "C" {
#endif

/* The failures the user gets a separate explanation for */
typedef enum ocr_status {
    OCR_OK,
    OCR_ENCRYPTED,
    OCR_BAD_INPUT,
    OCR_OUTPUT_ACCESS,
    OCR_TOO_BIG,
    OCR_FAILED,
} ocr_status;

typedef struct ocr_error {
    char message[512];
} ocr_error;

/* What happens to a page when the result is assembled */
typedef enum ocr_action {
    OCR_SKIP,    /* left as it is */
    OCR_OVERLAY, /* invisible text is added over the page */
    OCR_REPLACE, /* the page becomes the layer: a new image plus text */
} ocr_action;

typedef struct ocr_page_result {
    ocr_action action;
    int rotate;        /* degrees clockwise, added to the page's /Rotate */
    const char *layer; /* one-page PDF made by ocr_write_layer or Tesseract */
} ocr_page_result;

typedef struct ocr_page_info {
    int has_text;
    float image_dpi;     /* of the sharpest image on the page; 0 if none */
    float width, height; /* as shown, in points */
} ocr_page_info;

/*
 * Check the input and count its pages. A PDF is used as it is; an image
 * (JPEG, PNG, TIFF) is first converted into a PDF at image_pdf. *pdf then
 * points at input or image_pdf.
 */
ocr_status ocr_prepare(fz_context *ctx, const char *input,
                       const char *image_pdf, const char **pdf, int *pages,
                       ocr_error *err);

ocr_status ocr_open(fz_context *ctx, const char *path, pdf_document **doc,
                    ocr_error *err);

ocr_status ocr_analyze_page(fz_context *ctx, pdf_document *doc, int page,
                            ocr_page_info *info, ocr_error *err);

/* Gray (n = 1) or RGB (n = 3), as shown on screen, at dpi */
ocr_status ocr_render_page(fz_context *ctx, pdf_document *doc, int page,
                           float dpi, int color, fz_pixmap **pixmap,
                           ocr_error *err);

/*
 * Write to out a copy of Tesseract's text-only PDF page with an image
 * underneath: samples are rows of w pixels of n bytes (1 gray, 3 RGB).
 */
ocr_status ocr_write_layer(fz_context *ctx, const char *text_pdf, int w,
                           int h, int n, const unsigned char *samples,
                           ptrdiff_t stride, const char *out, ocr_error *err);

/* Apply the page results to a copy of input and save it to out */
ocr_status ocr_assemble(fz_context *ctx, const char *input, int count,
                        const ocr_page_result *pages, const char *out,
                        ocr_error *err);

#ifdef __cplusplus
}
#endif

#endif
