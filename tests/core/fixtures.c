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

int fixture_page_png(fz_context *ctx, const char *pdf, int dpi,
                     const char *png)
{
    pdf_document *doc = NULL;
    fz_pixmap *pixmap = NULL;

    fz_var(doc);
    fz_var(pixmap);
    fz_try(ctx) {
        doc = pdf_open_document(ctx, pdf);
        pixmap = fz_new_pixmap_from_page_number(
            ctx, (fz_document *)doc, 0, fz_scale(dpi / 72.0f, dpi / 72.0f),
            fz_device_gray(ctx), 0);
        fz_set_pixmap_resolution(ctx, pixmap, dpi, dpi);
        fz_save_pixmap_as_png(ctx, pixmap, png);
    }
    fz_always(ctx) {
        fz_drop_pixmap(ctx, pixmap);
        pdf_drop_document(ctx, doc);
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
