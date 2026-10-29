/*
 * Test files made and read with MuPDF. C for the reason pdf.c is: MuPDF's
 * errors longjmp, which must never cross C++ frames. Each function returns
 * 0, or -1 after printing MuPDF's message to stderr.
 */
#ifndef OCR_TEST_FIXTURES_H
#define OCR_TEST_FIXTURES_H

#include <stddef.h>

#include <mupdf/fitz.h>

#ifdef __cplusplus
extern "C" {
#endif

/*
 * One small page with the lines of text (separated by '\n') in Helvetica,
 * shown turned clockwise by rotate degrees
 */
int fixture_text_pdf(fz_context *ctx, const char *path, const char *text,
                     int rotate);

/*
 * Page 0 of pdf as a gray PNG scanned at dpi, which the PNG records, with
 * the paper turned clockwise by skew degrees
 */
int fixture_page_png(fz_context *ctx, const char *pdf, int dpi, float skew,
                     const char *png);

/*
 * Page 0 of pdf as a camera's JPEG: taken at dpi but recording 72 dpi, as
 * cameras do, and the EXIF orientation (1 to 8) it is to be shown with
 */
int fixture_photo_jpeg(fz_context *ctx, const char *pdf, int dpi,
                       int orientation, const char *jpeg);

/* Page 0 of pdf scanned at dpi as an uncompressed gray TIFF, once on each
   of its pages */
int fixture_page_tiff(fz_context *ctx, const char *pdf, int dpi, int pages,
                      const char *tiff);

/* A copy of pdf that needs no password to open but is encrypted */
int fixture_encrypt(fz_context *ctx, const char *pdf, const char *out);

/* The text of a page, as a reader would copy it */
int fixture_page_text(fz_context *ctx, const char *pdf, int page,
                      char *text, size_t size);

int fixture_page_rotation(fz_context *ctx, const char *pdf, int page,
                          int *degrees);

int fixture_has_output_intent(fz_context *ctx, const char *pdf, int *yes);

#ifdef __cplusplus
}
#endif

#endif
