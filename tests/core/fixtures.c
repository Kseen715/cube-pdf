#include "fixtures.h"

#include <mupdf/pdf.h>
#include <stdio.h>
#include <string.h>

/* A short page of plain print: enough text for Tesseract to tell which
   way is up, small enough to OCR in a second */
#define PAGE_WIDTH 468
#define PAGE_HEIGHT 432
#define FONT_SIZE 12
#define LINE_PITCH 15
#define MARGIN 24

static const char OWNER_PASSWORD[] = "owner";

/* Cameras record this resolution, whatever the picture shows */
#define CAMERA_DPI 72
#define JPEG_QUALITY 90
#define SOI_SIZE 2

/* The smallest APP1 block MuPDF reads: one IFD entry, Orientation */
static const unsigned char EXIF[] = {
    0xFF, 0xE1, 0, 34,                      /* APP1, length */
    'E', 'x', 'i', 'f', 0, 0,               /* its name */
    'M', 'M', 0, 42, 0, 0, 0, 8,            /* TIFF header, IFD at 8 */
    0, 1,                                   /* one entry */
    0x01, 0x12, 0, 3, 0, 0, 0, 1, 0, 1, 0, 0, /* SHORT 0x112 */
    0, 0, 0, 0,                             /* no next IFD */
};
#define EXIF_ORIENTATION_AT 29

#define TIFF_SHORT 3
#define TIFF_LONG 4
#define TIFF_RATIONAL 5
#define TIFF_HEADER 8
#define TIFF_ENTRIES 11
#define TIFF_IFD_SIZE (2 + 12 * TIFF_ENTRIES + 4)

static int failed(fz_context *ctx)
{
    fprintf(stderr, "fixture: %s\n", fz_caught_message(ctx));
    fz_ignore_error(ctx);
    return -1;
}

static fz_buffer *text_contents(fz_context *ctx, const char *text)
{
    fz_buffer *contents = fz_new_buffer(ctx, 256);
    float y = PAGE_HEIGHT - MARGIN - FONT_SIZE;
    const char *line = text;

    fz_try(ctx) {
        while (*line) {
            const char *end = strchr(line, '\n');
            int length = end ? (int)(end - line) : (int)strlen(line);

            fz_append_printf(ctx, contents,
                             "BT /F1 %d Tf %d %g Td (%.*s) Tj ET\n",
                             FONT_SIZE, MARGIN, y, length, line);
            y -= LINE_PITCH;
            line += length + (end != NULL);
        }
    }
    fz_catch(ctx) {
        fz_drop_buffer(ctx, contents);
        fz_rethrow(ctx);
    }
    return contents;
}

int fixture_text_pdf(fz_context *ctx, const char *path, const char *text,
                     int rotate)
{
    pdf_document *doc = NULL;
    fz_font *font = NULL;
    fz_buffer *contents = NULL;
    pdf_obj *res = NULL, *page = NULL;

    fz_var(doc);
    fz_var(font);
    fz_var(contents);
    fz_var(res);
    fz_var(page);
    fz_try(ctx) {
        pdf_obj *fonts;

        doc = pdf_create_document(ctx);
        font = fz_new_base14_font(ctx, "Helvetica");
        res = pdf_new_dict(ctx, doc, 1);
        fonts = pdf_dict_put_dict(ctx, res, PDF_NAME(Font), 1);
        pdf_dict_puts_drop(ctx, fonts, "F1",
                           pdf_add_simple_font(ctx, doc, font,
                                               PDF_SIMPLE_ENCODING_LATIN));
        contents = text_contents(ctx, text);
        page = pdf_add_page(ctx, doc,
                            fz_make_rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT),
                            rotate, res, contents);
        pdf_insert_page(ctx, doc, -1, page);
        pdf_save_document(ctx, doc, path, NULL);
    }
    fz_always(ctx) {
        pdf_drop_obj(ctx, page);
        pdf_drop_obj(ctx, res);
        fz_drop_buffer(ctx, contents);
        fz_drop_font(ctx, font);
        pdf_drop_document(ctx, doc);
    }
    fz_catch(ctx)
        return failed(ctx);
    return 0;
}

/* Page 0 of pdf rendered gray at dpi, the paper turned by skew degrees */
static fz_pixmap *scan_page(fz_context *ctx, const char *pdf, int dpi,
                            float skew)
{
    pdf_document *doc = pdf_open_document(ctx, pdf);
    fz_matrix ctm = fz_concat(fz_scale(dpi / 72.0f, dpi / 72.0f),
                              fz_rotate(skew));
    fz_pixmap *pixmap = NULL;

    fz_try(ctx) {
        pixmap = fz_new_pixmap_from_page_number(
            ctx, (fz_document *)doc, 0, ctm, fz_device_gray(ctx), 0);
        fz_set_pixmap_resolution(ctx, pixmap, dpi, dpi);
    }
    fz_always(ctx)
        pdf_drop_document(ctx, doc);
    fz_catch(ctx)
        fz_rethrow(ctx);
    return pixmap;
}

int fixture_page_png(fz_context *ctx, const char *pdf, int dpi, float skew,
                     const char *png)
{
    fz_pixmap *pixmap = NULL;

    fz_var(pixmap);
    fz_try(ctx) {
        pixmap = scan_page(ctx, pdf, dpi, skew);
        fz_save_pixmap_as_png(ctx, pixmap, png);
    }
    fz_always(ctx)
        fz_drop_pixmap(ctx, pixmap);
    fz_catch(ctx)
        return failed(ctx);
    return 0;
}

/* The JPEG, with the EXIF block put right after its first marker (SOI) */
static void save_with_exif(fz_context *ctx, fz_buffer *jpeg, int orientation,
                           const char *path)
{
    unsigned char exif[sizeof EXIF];
    unsigned char *data;
    size_t len = fz_buffer_storage(ctx, jpeg, &data);
    fz_output *out = fz_new_output_with_path(ctx, path, 0);

    memcpy(exif, EXIF, sizeof exif);
    exif[EXIF_ORIENTATION_AT] = (unsigned char)orientation;
    fz_try(ctx) {
        fz_write_data(ctx, out, data, SOI_SIZE);
        fz_write_data(ctx, out, exif, sizeof exif);
        fz_write_data(ctx, out, data + SOI_SIZE, len - SOI_SIZE);
        fz_close_output(ctx, out);
    }
    fz_always(ctx)
        fz_drop_output(ctx, out);
    fz_catch(ctx)
        fz_rethrow(ctx);
}

int fixture_photo_jpeg(fz_context *ctx, const char *pdf, int dpi,
                       int orientation, const char *jpeg)
{
    fz_pixmap *pixmap = NULL;
    fz_buffer *buf = NULL;
    fz_output *out = NULL;

    fz_var(pixmap);
    fz_var(buf);
    fz_var(out);
    fz_try(ctx) {
        pixmap = scan_page(ctx, pdf, dpi, 0);
        fz_set_pixmap_resolution(ctx, pixmap, CAMERA_DPI, CAMERA_DPI);
        buf = fz_new_buffer(ctx, 0);
        out = fz_new_output_with_buffer(ctx, buf);
        fz_write_pixmap_as_jpeg(ctx, out, pixmap, JPEG_QUALITY, 0);
        fz_close_output(ctx, out);
        save_with_exif(ctx, buf, orientation, jpeg);
    }
    fz_always(ctx) {
        fz_drop_output(ctx, out);
        fz_drop_buffer(ctx, buf);
        fz_drop_pixmap(ctx, pixmap);
    }
    fz_catch(ctx)
        return failed(ctx);
    return 0;
}

static void tiff_entry(fz_context *ctx, fz_output *out,
                       const unsigned entry[3])
{
    fz_write_uint16_le(ctx, out, entry[0]);
    fz_write_uint16_le(ctx, out, entry[1]);
    fz_write_uint32_le(ctx, out, 1);
    if (entry[1] == TIFF_SHORT) {
        fz_write_uint16_le(ctx, out, entry[2]);
        fz_write_uint16_le(ctx, out, 0);
    } else {
        fz_write_uint32_le(ctx, out, entry[2]);
    }
}

/*
 * Little-endian: the header, the pixels as one strip, the resolution, then
 * one IFD per page, every one pointing at the same strip
 */
static void write_tiff(fz_context *ctx, fz_output *out, fz_pixmap *pixmap,
                       int pages)
{
    unsigned w = fz_pixmap_width(ctx, pixmap);
    unsigned h = fz_pixmap_height(ctx, pixmap);
    unsigned char *samples = fz_pixmap_samples(ctx, pixmap);
    unsigned size = w * h, padded = size + (size & 1);
    unsigned resolution = TIFF_HEADER + padded, ifd = resolution + 8;
    const unsigned entries[TIFF_ENTRIES][3] = {
        {256, TIFF_LONG, w},         {257, TIFF_LONG, h},
        {258, TIFF_SHORT, 8},        {259, TIFF_SHORT, 1},
        {262, TIFF_SHORT, 1},        {273, TIFF_LONG, TIFF_HEADER},
        {278, TIFF_LONG, h},         {279, TIFF_LONG, size},
        {282, TIFF_RATIONAL, resolution},
        {283, TIFF_RATIONAL, resolution},
        {296, TIFF_SHORT, 2},
    };
    unsigned y, page, i;

    fz_write_data(ctx, out, "II*\0", 4);
    fz_write_uint32_le(ctx, out, ifd);
    for (y = 0; y < h; y++)
        fz_write_data(ctx, out, samples + y * fz_pixmap_stride(ctx, pixmap),
                      w);
    if (padded > size)
        fz_write_byte(ctx, out, 0);
    fz_write_uint32_le(ctx, out, pixmap->xres);
    fz_write_uint32_le(ctx, out, 1);
    for (page = 0; page < (unsigned)pages; page++) {
        fz_write_uint16_le(ctx, out, TIFF_ENTRIES);
        for (i = 0; i < TIFF_ENTRIES; i++)
            tiff_entry(ctx, out, entries[i]);
        fz_write_uint32_le(ctx, out,
                           page + 1 < (unsigned)pages
                               ? ifd + (page + 1) * TIFF_IFD_SIZE
                               : 0);
    }
}

int fixture_page_tiff(fz_context *ctx, const char *pdf, int dpi, int pages,
                      const char *tiff)
{
    fz_pixmap *pixmap = NULL;
    fz_output *out = NULL;

    fz_var(pixmap);
    fz_var(out);
    fz_try(ctx) {
        pixmap = scan_page(ctx, pdf, dpi, 0);
        out = fz_new_output_with_path(ctx, tiff, 0);
        write_tiff(ctx, out, pixmap, pages);
        fz_close_output(ctx, out);
    }
    fz_always(ctx) {
        fz_drop_output(ctx, out);
        fz_drop_pixmap(ctx, pixmap);
    }
    fz_catch(ctx)
        return failed(ctx);
    return 0;
}

int fixture_encrypt(fz_context *ctx, const char *pdf, const char *out)
{
    pdf_document *doc = NULL;
    pdf_write_options opts = pdf_default_write_options;

    opts.do_encrypt = PDF_ENCRYPT_AES_128;
    opts.permissions = -1;
    fz_strlcpy(opts.opwd_utf8, OWNER_PASSWORD, sizeof opts.opwd_utf8);

    fz_var(doc);
    fz_try(ctx) {
        doc = pdf_open_document(ctx, pdf);
        pdf_save_document(ctx, doc, out, &opts);
    }
    fz_always(ctx)
        pdf_drop_document(ctx, doc);
    fz_catch(ctx)
        return failed(ctx);
    return 0;
}

int fixture_page_text(fz_context *ctx, const char *pdf, int page,
                      char *text, size_t size)
{
    pdf_document *doc = NULL;
    fz_buffer *buf = NULL;

    fz_var(doc);
    fz_var(buf);
    fz_try(ctx) {
        doc = pdf_open_document(ctx, pdf);
        buf = fz_new_buffer_from_page_number(ctx, (fz_document *)doc, page,
                                             NULL);
        fz_strlcpy(text, fz_string_from_buffer(ctx, buf), size);
    }
    fz_always(ctx) {
        fz_drop_buffer(ctx, buf);
        pdf_drop_document(ctx, doc);
    }
    fz_catch(ctx)
        return failed(ctx);
    return 0;
}

int fixture_page_rotation(fz_context *ctx, const char *pdf, int page,
                          int *degrees)
{
    pdf_document *doc = NULL;

    fz_var(doc);
    fz_try(ctx) {
        doc = pdf_open_document(ctx, pdf);
        *degrees = pdf_to_int(
            ctx, pdf_dict_get_inheritable(ctx,
                                          pdf_lookup_page_obj(ctx, doc, page),
                                          PDF_NAME(Rotate)));
    }
    fz_always(ctx)
        pdf_drop_document(ctx, doc);
    fz_catch(ctx)
        return failed(ctx);
    return 0;
}

int fixture_has_output_intent(fz_context *ctx, const char *pdf, int *yes)
{
    pdf_document *doc = NULL;

    fz_var(doc);
    fz_try(ctx) {
        pdf_obj *intents;

        doc = pdf_open_document(ctx, pdf);
        intents = pdf_dict_get(ctx, pdf_trailer(ctx, doc), PDF_NAME(Root));
        intents = pdf_dict_get(ctx, intents, PDF_NAME(OutputIntents));
        *yes = pdf_array_len(ctx, intents) > 0;
    }
    fz_always(ctx)
        pdf_drop_document(ctx, doc);
    fz_catch(ctx)
        return failed(ctx);
    return 0;
}
