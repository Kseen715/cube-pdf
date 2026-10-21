#include "pdf.h"

#include <math.h>
#include <string.h>

/*
 * Images without a believable resolution are taken as scans at this DPI.
 * MuPDF reports 96 for a file that has none, and cameras write 72.
 */
#define FALLBACK_IMAGE_DPI 300
#define MIN_BELIEVABLE_DPI 100

#define NAME_SIZE 32
#define DRAW_SIZE 256

static const char LAYER_NAME[] = "OCRLayer";
static const char IMAGE_NAME[] = "OCRImage";

typedef struct analyze_device {
    fz_device super;
    int has_text;
    float image_dpi;
} analyze_device;

/* Record the caught MuPDF error; running out of memory has its own kind */
static ocr_status caught(fz_context *ctx, ocr_status status, ocr_error *err)
{
    fz_snprintf(err->message, sizeof err->message, "%s",
                fz_caught_message(ctx));
    if (fz_caught(ctx) == FZ_ERROR_LIMIT ||
        strstr(err->message, "alloc ("))
        status = OCR_TOO_BIG;
    fz_ignore_error(ctx);
    return status;
}

static void save(fz_context *ctx, pdf_document *doc, const char *path)
{
    pdf_write_options opts = pdf_default_write_options;

    opts.do_garbage = 1;
    opts.do_compress = 1;
    opts.do_compress_images = 1;
    opts.do_compress_fonts = 1;
    pdf_save_document(ctx, doc, path, &opts);
}

ocr_status ocr_open(fz_context *ctx, const char *path, pdf_document **doc,
                    ocr_error *err)
{
    *doc = NULL;
    fz_try(ctx)
        *doc = pdf_open_document(ctx, path);
    fz_catch(ctx)
        return caught(ctx, OCR_BAD_INPUT, err);

    /* Like OCRmyPDF: any encryption, even without a password to open */
    if (pdf_needs_password(ctx, *doc) || (*doc)->crypt) {
        pdf_drop_document(ctx, *doc);
        *doc = NULL;
        fz_snprintf(err->message, sizeof err->message, "encrypted PDF");
        return OCR_ENCRYPTED;
    }
    return OCR_OK;
}

/* --- images to PDF ------------------------------------------------------ */

static pdf_obj *image_resources(fz_context *ctx, pdf_document *doc,
                                pdf_obj *image)
{
    pdf_obj *res = pdf_new_dict(ctx, doc, 1);

    fz_try(ctx) {
        pdf_obj *xobjects = pdf_dict_put_dict(ctx, res, PDF_NAME(XObject), 1);
        pdf_dict_puts(ctx, xobjects, IMAGE_NAME, image);
    }
    fz_catch(ctx) {
        pdf_drop_obj(ctx, res);
        fz_rethrow(ctx);
    }
    return res;
}

/* One page as large as the image is at its resolution, turned upright */
static void add_image_page(fz_context *ctx, pdf_document *doc,
                           fz_image *image)
{
    int xres, yres;
    float w, h, swap;
    fz_matrix place;
    pdf_obj *ref = NULL, *res = NULL, *page = NULL;
    fz_buffer *contents = NULL;

    fz_image_resolution(image, &xres, &yres);
    if (xres < MIN_BELIEVABLE_DPI || yres < MIN_BELIEVABLE_DPI)
        xres = yres = FALLBACK_IMAGE_DPI;
    w = image->w * 72.0f / xres;
    h = image->h * 72.0f / yres;
    /* EXIF orientations 5 to 8 turn the image by 90 degrees */
    if (fz_image_orientation(ctx, image) >= 5) {
        swap = w;
        w = h;
        h = swap;
    }
    place = fz_concat(fz_image_orientation_matrix(ctx, image),
                      fz_scale(w, h));

    fz_var(ref);
    fz_var(res);
    fz_var(page);
    fz_var(contents);
    fz_try(ctx) {
        ref = pdf_add_image(ctx, doc, image);
        res = image_resources(ctx, doc, ref);
        contents = fz_new_buffer(ctx, DRAW_SIZE);
        fz_append_printf(ctx, contents, "q %g %g %g %g %g %g cm /%s Do Q",
                         place.a, place.b, place.c, place.d, place.e,
                         place.f, IMAGE_NAME);
        page = pdf_add_page(ctx, doc, fz_make_rect(0, 0, w, h), 0, res,
                            contents);
        pdf_insert_page(ctx, doc, -1, page);
    }
    fz_always(ctx) {
        fz_drop_buffer(ctx, contents);
        pdf_drop_obj(ctx, page);
        pdf_drop_obj(ctx, res);
        pdf_drop_obj(ctx, ref);
    }
    fz_catch(ctx)
        fz_rethrow(ctx);
}

static void add_image_pages(fz_context *ctx, pdf_document *doc,
                            fz_buffer *buf)
{
    unsigned char *data;
    size_t len = fz_buffer_storage(ctx, buf, &data);
    int count = 1, i;
    fz_image *image = NULL;
    fz_pixmap *pixmap = NULL;
    int tiff = len >= 8 &&
               fz_recognize_image_format(ctx, data) == FZ_IMAGE_TIFF;

    if (tiff)
        count = fz_load_tiff_subimage_count(ctx, data, len);

    fz_var(image);
    fz_var(pixmap);
    for (i = 0; i < count; i++) {
        fz_try(ctx) {
            if (tiff) {
                pixmap = fz_load_tiff_subimage(ctx, data, len, i);
                image = fz_new_image_from_pixmap(ctx, pixmap, NULL);
            } else {
                image = fz_new_image_from_buffer(ctx, buf);
            }
            add_image_page(ctx, doc, image);
        }
        fz_always(ctx) {
            fz_drop_image(ctx, image);
            fz_drop_pixmap(ctx, pixmap);
            image = NULL;
            pixmap = NULL;
        }
        fz_catch(ctx)
            fz_rethrow(ctx);
    }
}

static int is_image(fz_context *ctx, const char *path)
{
    unsigned char header[8] = {0};
    fz_stream *file = fz_open_file(ctx, path);
    size_t got = 0;

    fz_try(ctx)
        got = fz_read(ctx, file, header, sizeof header);
    fz_always(ctx)
        fz_drop_stream(ctx, file);
    fz_catch(ctx)
        fz_rethrow(ctx);
    return got == sizeof header &&
           fz_recognize_image_format(ctx, header) != FZ_IMAGE_UNKNOWN;
}

static void image_to_pdf(fz_context *ctx, const char *input, const char *out)
{
    fz_buffer *buf = NULL;
    pdf_document *doc = NULL;

    fz_var(buf);
    fz_var(doc);
    fz_try(ctx) {
        buf = fz_read_file(ctx, input);
        doc = pdf_create_document(ctx);
        add_image_pages(ctx, doc, buf);
        save(ctx, doc, out);
    }
    fz_always(ctx) {
        pdf_drop_document(ctx, doc);
        fz_drop_buffer(ctx, buf);
    }
    fz_catch(ctx)
        fz_rethrow(ctx);
}

ocr_status ocr_prepare(fz_context *ctx, const char *input,
                       const char *image_pdf, const char **pdf, int *pages,
                       ocr_error *err)
{
    pdf_document *doc;
    ocr_status status;

    *pdf = input;
    fz_try(ctx) {
        if (is_image(ctx, input)) {
            image_to_pdf(ctx, input, image_pdf);
            *pdf = image_pdf;
        }
    }
    fz_catch(ctx)
        return caught(ctx, OCR_BAD_INPUT, err);

    status = ocr_open(ctx, *pdf, &doc, err);
    if (status != OCR_OK)
        return status;
    fz_try(ctx)
        *pages = pdf_count_pages(ctx, doc);
    fz_always(ctx)
        pdf_drop_document(ctx, doc);
    fz_catch(ctx)
        return caught(ctx, OCR_BAD_INPUT, err);

    if (*pages < 1) {
        fz_snprintf(err->message, sizeof err->message, "no pages");
        return OCR_BAD_INPUT;
    }
    return OCR_OK;
}

/* --- looking at a page -------------------------------------------------- */

static void note_text(fz_device *dev, const fz_text *text)
{
    if (text->head)
        ((analyze_device *)dev)->has_text = 1;
}

static void fill_text(fz_context *ctx, fz_device *dev, const fz_text *text,
                      fz_matrix ctm, fz_colorspace *cs, const float *color,
                      float alpha, fz_color_params params)
{
    note_text(dev, text);
}

static void stroke_text(fz_context *ctx, fz_device *dev, const fz_text *text,
                        const fz_stroke_state *stroke, fz_matrix ctm,
                        fz_colorspace *cs, const float *color, float alpha,
                        fz_color_params params)
{
    note_text(dev, text);
}

static void clip_text(fz_context *ctx, fz_device *dev, const fz_text *text,
                      fz_matrix ctm, fz_rect scissor)
{
    note_text(dev, text);
}

static void clip_stroke_text(fz_context *ctx, fz_device *dev,
                             const fz_text *text,
                             const fz_stroke_state *stroke, fz_matrix ctm,
                             fz_rect scissor)
{
    note_text(dev, text);
}

/* Invisible text, such as an earlier OCR layer, is text too */
static void ignore_text(fz_context *ctx, fz_device *dev, const fz_text *text,
                        fz_matrix ctm)
{
    note_text(dev, text);
}

static void note_image(fz_device *dev, fz_image *image, fz_matrix ctm)
{
    analyze_device *analyze = (analyze_device *)dev;
    float width = hypotf(ctm.a, ctm.b), height = hypotf(ctm.c, ctm.d);

    if (width > 0 && height > 0) {
        float dpi = fmaxf(image->w * 72 / width, image->h * 72 / height);
        analyze->image_dpi = fmaxf(analyze->image_dpi, dpi);
    }
}

static void fill_image(fz_context *ctx, fz_device *dev, fz_image *image,
                       fz_matrix ctm, float alpha, fz_color_params params)
{
    note_image(dev, image, ctm);
}

static void fill_image_mask(fz_context *ctx, fz_device *dev,
                            fz_image *image, fz_matrix ctm,
                            fz_colorspace *cs, const float *color,
                            float alpha, fz_color_params params)
{
    note_image(dev, image, ctm);
}

static void clip_image_mask(fz_context *ctx, fz_device *dev,
                            fz_image *image, fz_matrix ctm, fz_rect scissor)
{
    note_image(dev, image, ctm);
}

static analyze_device *new_analyze_device(fz_context *ctx)
{
    analyze_device *dev = fz_new_derived_device(ctx, analyze_device);

    dev->super.fill_text = fill_text;
    dev->super.stroke_text = stroke_text;
    dev->super.clip_text = clip_text;
    dev->super.clip_stroke_text = clip_stroke_text;
    dev->super.ignore_text = ignore_text;
    dev->super.fill_image = fill_image;
    dev->super.fill_image_mask = fill_image_mask;
    dev->super.clip_image_mask = clip_image_mask;
    return dev;
}

ocr_status ocr_analyze_page(fz_context *ctx, pdf_document *doc, int number,
                            ocr_page_info *info, ocr_error *err)
{
    pdf_page *page = NULL;
    analyze_device *dev = NULL;
    fz_rect shown;

    fz_var(page);
    fz_var(dev);
    fz_try(ctx) {
        page = pdf_load_page(ctx, doc, number);
        dev = new_analyze_device(ctx);
        fz_run_page_contents(ctx, (fz_page *)page, &dev->super, fz_identity,
                             NULL);
        fz_close_device(ctx, &dev->super);
        shown = fz_bound_page(ctx, (fz_page *)page);
        info->has_text = dev->has_text;
        info->image_dpi = dev->image_dpi;
        info->width = shown.x1 - shown.x0;
        info->height = shown.y1 - shown.y0;
    }
    fz_always(ctx) {
        fz_drop_device(ctx, (fz_device *)dev);
        fz_drop_page(ctx, (fz_page *)page);
    }
    fz_catch(ctx)
        return caught(ctx, OCR_BAD_INPUT, err);
    return OCR_OK;
}

/* Only the page's own content: annotations stay live above the result */
ocr_status ocr_render_page(fz_context *ctx, pdf_document *doc, int number,
                           float dpi, int color, fz_pixmap **pixmap,
                           ocr_error *err)
{
    pdf_page *page = NULL;
    fz_device *dev = NULL;
    fz_pixmap *pix = NULL;
    fz_matrix ctm = fz_scale(dpi / 72, dpi / 72);

    fz_var(page);
    fz_var(dev);
    fz_var(pix);
    fz_try(ctx) {
        fz_colorspace *cs = color ? fz_device_rgb(ctx) : fz_device_gray(ctx);
        fz_rect shown;

        page = pdf_load_page(ctx, doc, number);
        shown = fz_transform_rect(fz_bound_page(ctx, (fz_page *)page), ctm);
        pix = fz_new_pixmap_with_bbox(ctx, cs, fz_round_rect(shown), NULL, 0);
        fz_clear_pixmap_with_value(ctx, pix, 0xff);
        dev = fz_new_draw_device(ctx, fz_identity, pix);
        fz_run_page_contents(ctx, (fz_page *)page, dev, ctm, NULL);
        fz_close_device(ctx, dev);
    }
    fz_always(ctx) {
        fz_drop_device(ctx, dev);
        fz_drop_page(ctx, (fz_page *)page);
    }
    fz_catch(ctx) {
        fz_drop_pixmap(ctx, pix);
        return caught(ctx, OCR_BAD_INPUT, err);
    }
    *pixmap = pix;
    return OCR_OK;
}

/* --- changing pages ----------------------------------------------------- */

/*
 * Give dict a shallow copy of original under key, so changing it cannot
 * affect other pages that share the original; return the copy
 */
static pdf_obj *own_dict(fz_context *ctx, pdf_document *doc, pdf_obj *dict,
                         pdf_obj *key, pdf_obj *original)
{
    pdf_obj *copy = pdf_is_dict(ctx, original) ? pdf_copy_dict(ctx, original)
                                               : pdf_new_dict(ctx, doc, 4);

    pdf_dict_put_drop(ctx, dict, key, copy);
    return copy;
}

/* Put xobject into the page's resources under a free name, written to name.
   With fresh_resources the page's old resources are dropped. */
static void add_xobject(fz_context *ctx, pdf_document *doc, pdf_obj *page,
                        const char *base, pdf_obj *xobject,
                        int fresh_resources, char name[NAME_SIZE])
{
    pdf_obj *old = fresh_resources
                       ? NULL
                       : pdf_dict_get_inheritable(ctx, page,
                                                  PDF_NAME(Resources));
    pdf_obj *res = own_dict(ctx, doc, page, PDF_NAME(Resources), old);
    pdf_obj *xobjects = own_dict(ctx, doc, res, PDF_NAME(XObject),
                                 pdf_dict_get(ctx, res, PDF_NAME(XObject)));
    int i;

    fz_snprintf(name, NAME_SIZE, "%s", base);
    for (i = 1; pdf_dict_gets(ctx, xobjects, name); i++)
        fz_snprintf(name, NAME_SIZE, "%s%d", base, i);
    pdf_dict_puts(ctx, xobjects, name, xobject);
}

static pdf_obj *new_stream(fz_context *ctx, pdf_document *doc,
                           const char *text)
{
    fz_buffer *buf = fz_new_buffer_from_copied_data(
        ctx, (const unsigned char *)text, strlen(text));
    pdf_obj *ref = NULL;

    fz_try(ctx)
        ref = pdf_add_stream(ctx, doc, buf, NULL, 0);
    fz_always(ctx)
        fz_drop_buffer(ctx, buf);
    fz_catch(ctx)
        fz_rethrow(ctx);
    return ref;
}

/* Set the page's content streams to: before, the old ones if keep, after */
static void set_contents(fz_context *ctx, pdf_document *doc, pdf_obj *page,
                         const char *before, int keep, const char *after)
{
    pdf_obj *old = pdf_dict_get(ctx, page, PDF_NAME(Contents));
    pdf_obj *list = pdf_new_array(ctx, doc, 4);
    int i;

    fz_try(ctx) {
        if (before)
            pdf_array_push_drop(ctx, list, new_stream(ctx, doc, before));
        if (keep && pdf_is_array(ctx, old)) {
            for (i = 0; i < pdf_array_len(ctx, old); i++)
                pdf_array_push(ctx, list, pdf_array_get(ctx, old, i));
        } else if (keep && old) {
            pdf_array_push(ctx, list, old);
        }
        if (after)
            pdf_array_push_drop(ctx, list, new_stream(ctx, doc, after));
        pdf_dict_put(ctx, page, PDF_NAME(Contents), list);
    }
    fz_always(ctx)
        pdf_drop_obj(ctx, list);
    fz_catch(ctx)
        fz_rethrow(ctx);
}

ocr_status ocr_write_layer(fz_context *ctx, const char *text_pdf, int w,
                           int h, int n, const unsigned char *samples,
                           ptrdiff_t stride, const char *out, ocr_error *err)
{
    pdf_document *doc = NULL;
    fz_pixmap *pixmap = NULL;
    fz_image *image = NULL;
    pdf_obj *ref = NULL;
    char name[NAME_SIZE], draw[DRAW_SIZE];

    fz_var(doc);
    fz_var(pixmap);
    fz_var(image);
    fz_var(ref);
    fz_try(ctx) {
        pdf_obj *page;
        fz_rect box;
        fz_colorspace *cs = n == 1 ? fz_device_gray(ctx) : fz_device_rgb(ctx);

        doc = pdf_open_document(ctx, text_pdf);
        page = pdf_lookup_page_obj(ctx, doc, 0);
        box = pdf_dict_get_rect(ctx, page, PDF_NAME(MediaBox));
        pixmap = fz_new_pixmap_with_data(ctx, cs, w, h, NULL, 0, (int)stride,
                                         (unsigned char *)samples);
        image = fz_new_image_from_pixmap(ctx, pixmap, NULL);
        ref = pdf_add_image(ctx, doc, image);
        add_xobject(ctx, doc, page, IMAGE_NAME, ref, 0, name);
        fz_snprintf(draw, sizeof draw, "q %g 0 0 %g %g %g cm /%s Do Q\n",
                    box.x1 - box.x0, box.y1 - box.y0, box.x0, box.y0, name);
        set_contents(ctx, doc, page, draw, 1, NULL);
        save(ctx, doc, out);
    }
    fz_always(ctx) {
        pdf_drop_obj(ctx, ref);
        fz_drop_image(ctx, image);
        fz_drop_pixmap(ctx, pixmap);
        pdf_drop_document(ctx, doc);
    }
    fz_catch(ctx)
        return caught(ctx, OCR_FAILED, err);
    return OCR_OK;
}

/* --- assembling the result ---------------------------------------------- */

static fz_buffer *page_contents(fz_context *ctx, pdf_obj *page)
{
    pdf_obj *contents = pdf_dict_get(ctx, page, PDF_NAME(Contents));
    fz_buffer *all, *part = NULL;
    int i;

    if (!pdf_is_array(ctx, contents))
        return pdf_load_stream(ctx, contents);

    all = fz_new_buffer(ctx, 1024);
    fz_var(part);
    fz_try(ctx) {
        for (i = 0; i < pdf_array_len(ctx, contents); i++) {
            part = pdf_load_stream(ctx, pdf_array_get(ctx, contents, i));
            fz_append_buffer(ctx, all, part);
            fz_append_byte(ctx, all, '\n');
            fz_drop_buffer(ctx, part);
            part = NULL;
        }
    }
    fz_catch(ctx) {
        fz_drop_buffer(ctx, part);
        fz_drop_buffer(ctx, all);
        fz_rethrow(ctx);
    }
    return all;
}

/* The layer's page as a form XObject in doc; box is its media box */
static pdf_obj *layer_xobject(fz_context *ctx, pdf_document *doc,
                              pdf_document *layer, fz_rect *box)
{
    pdf_obj *page = pdf_lookup_page_obj(ctx, layer, 0);
    pdf_graft_map *map = NULL;
    pdf_obj *res = NULL, *xobject = NULL;
    fz_buffer *contents = NULL;

    fz_var(map);
    fz_var(res);
    fz_var(contents);
    fz_try(ctx) {
        *box = pdf_dict_get_rect(ctx, page, PDF_NAME(MediaBox));
        map = pdf_new_graft_map(ctx, doc);
        res = pdf_graft_mapped_object(
            ctx, map, pdf_dict_get(ctx, page, PDF_NAME(Resources)));
        contents = page_contents(ctx, page);
        xobject = pdf_new_xobject(ctx, doc, *box, fz_identity, res, contents);
    }
    fz_always(ctx) {
        fz_drop_buffer(ctx, contents);
        pdf_drop_obj(ctx, res);
        pdf_drop_graft_map(ctx, map);
    }
    fz_catch(ctx)
        fz_rethrow(ctx);
    return xobject;
}

/*
 * Map the layer (Tesseract's page for the image as it is shown, y going
 * up) onto the page's own coordinates, through the way the page is shown
 */
static fz_matrix layer_matrix(fz_context *ctx, pdf_obj *page, fz_rect box)
{
    fz_rect crop, shown;
    fz_matrix page_ctm, to_shown;
    float sx, sy;

    pdf_page_obj_transform(ctx, page, &crop, &page_ctm);
    shown = fz_transform_rect(crop, page_ctm);
    sx = (shown.x1 - shown.x0) / (box.x1 - box.x0);
    sy = (shown.y1 - shown.y0) / (box.y1 - box.y0);
    to_shown = fz_make_matrix(sx, 0, 0, -sy, shown.x0 - box.x0 * sx,
                              shown.y0 + box.y1 * sy);
    return fz_concat(to_shown, fz_invert_matrix(page_ctm));
}

static void add_rotation(fz_context *ctx, pdf_obj *page, int degrees)
{
    pdf_obj *old = pdf_dict_get_inheritable(ctx, page, PDF_NAME(Rotate));
    int rotate = (pdf_to_int(ctx, old) + degrees) % 360;

    pdf_dict_put_int(ctx, page, PDF_NAME(Rotate), (rotate + 360) % 360);
}

/*
 * Draw the layer over the page. The old content is wrapped in q/Q first,
 * so whatever graphics state it leaves behind cannot move the text. With
 * replace, the layer (image and text) becomes the whole content.
 */
static void draw_layer(fz_context *ctx, pdf_document *doc, pdf_obj *page,
                       pdf_obj *xobject, fz_rect box, int replace)
{
    fz_matrix m = layer_matrix(ctx, page, box);
    char name[NAME_SIZE], draw[DRAW_SIZE];

    add_xobject(ctx, doc, page, LAYER_NAME, xobject, replace, name);
    fz_snprintf(draw, sizeof draw, "%sq %g %g %g %g %g %g cm /%s Do Q\n",
                replace ? "" : "\nQ\n", m.a, m.b, m.c, m.d, m.e, m.f, name);
    if (replace)
        set_contents(ctx, doc, page, NULL, 0, draw);
    else
        set_contents(ctx, doc, page, "q\n", 1, draw);
}

static void apply_layer(fz_context *ctx, pdf_document *doc, int number,
                        const ocr_page_result *result)
{
    pdf_obj *page = pdf_lookup_page_obj(ctx, doc, number);
    pdf_document *layer = NULL;
    pdf_obj *xobject = NULL;
    fz_rect box;

    fz_var(layer);
    fz_var(xobject);
    fz_try(ctx) {
        if (result->rotate)
            add_rotation(ctx, page, result->rotate);
        layer = pdf_open_document(ctx, result->layer);
        xobject = layer_xobject(ctx, doc, layer, &box);
        draw_layer(ctx, doc, page, xobject, box,
                   result->action == OCR_REPLACE);
    }
    fz_always(ctx) {
        pdf_drop_obj(ctx, xobject);
        pdf_drop_document(ctx, layer);
    }
    fz_catch(ctx)
        fz_rethrow(ctx);
}

ocr_status ocr_assemble(fz_context *ctx, const char *input, int count,
                        const ocr_page_result *pages, const char *out,
                        ocr_error *err)
{
    pdf_document *doc;
    ocr_status status = ocr_open(ctx, input, &doc, err);
    int i;

    if (status != OCR_OK)
        return status;
    fz_try(ctx) {
        for (i = 0; i < count; i++)
            if (pages[i].action != OCR_SKIP)
                apply_layer(ctx, doc, i, &pages[i]);
        save(ctx, doc, out);
    }
    fz_always(ctx)
        pdf_drop_document(ctx, doc);
    fz_catch(ctx)
        return caught(ctx, OCR_FAILED, err);
    return OCR_OK;
}
