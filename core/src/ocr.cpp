#include "ocr.hpp"

#include <algorithm>
#include <cmath>
#include <mutex>
#include <new>

#include <tesseract/renderer.h>

namespace ocr {

namespace {

// OCRmyPDF's default for --rotate-pages-threshold
constexpr float ROTATE_THRESHOLD = 14.0f;

// Pages are rendered at the resolution of their sharpest image, within
// these limits; pages without images at VECTOR_DPI
constexpr float MIN_DPI = 300, MAX_DPI = 600, VECTOR_DPI = 400;
constexpr double MAX_PIXELS = 64e6;

std::mutex mupdf_locks[FZ_LOCK_MAX];

void lock(void *, int n) { mupdf_locks[n].lock(); }
void unlock(void *, int n) { mupdf_locks[n].unlock(); }

const char *kind_of(ocr_status status)
{
    switch (status) {
    case OCR_ENCRYPTED:
        return "encrypted";
    case OCR_BAD_INPUT:
        return "bad_input";
    case OCR_OUTPUT_ACCESS:
        return "output_access";
    case OCR_TOO_BIG:
        return "too_big";
    default:
        return "other";
    }
}

void check(ocr_status status, const ocr_error &err)
{
    if (status != OCR_OK)
        throw Error(kind_of(status), err.message);
}

float render_dpi(const ocr_page_info &info)
{
    float dpi = info.image_dpi > 0 ? info.image_dpi : VECTOR_DPI;
    dpi = std::clamp(dpi, MIN_DPI, MAX_DPI);

    double square_inches = info.width * info.height / (72.0 * 72.0);
    if (square_inches > 0)
        dpi = std::min(dpi, float(std::sqrt(MAX_PIXELS / square_inches)));
    return dpi;
}

// Returns whether the page was straightened
bool deskew(PixPtr &image)
{
    l_float32 angle = 0, confidence = 0;
    PIX *straight =
        pixDeskewGeneral(image.get(), 0, 0, 0, 0, 0, &angle, &confidence);

    if (!straight)
        return false;
    // Leptonica returns a clone when the skew is too small to correct
    if (straight == image.get()) {
        pixDestroy(&straight);
        return false;
    }
    image.reset(straight);
    return true;
}

void write_layer(const Context &ctx, const std::string &text_pdf, PIX *image,
                 const std::string &out)
{
    Samples samples = to_samples(image);
    ocr_error err;
    check(ocr_write_layer(ctx.get(), text_pdf.c_str(), samples.w, samples.h,
                          samples.n, samples.bytes.data(), samples.stride(),
                          out.c_str(), &err),
          err);
}

} // namespace

Error::Error(const std::string &kind, const std::string &detail)
    : std::runtime_error(detail), kind_(kind)
{
}

// --- Context ---------------------------------------------------------------

Context::Context()
{
    static const fz_locks_context locks = {nullptr, lock, unlock};
    ctx_ = fz_new_context(nullptr, &locks, FZ_STORE_DEFAULT);
    if (!ctx_)
        throw std::bad_alloc();
}

Context::~Context() { fz_drop_context(ctx_); }

std::unique_ptr<Context> Context::clone() const
{
    fz_context *copy = fz_clone_context(ctx_);
    if (!copy)
        throw std::bad_alloc();
    return std::unique_ptr<Context>(new Context(copy));
}

// --- the pipeline ------------------------------------------------------------

Input prepare(const Context &ctx, const std::string &input,
              const std::string &workdir)
{
    std::string image_pdf = workdir + "/image.pdf";
    const char *pdf = nullptr;
    Input result;
    ocr_error err;

    check(ocr_prepare(ctx.get(), input.c_str(), image_pdf.c_str(), &pdf,
                      &result.pages, &err),
          err);
    result.pdf = pdf;
    return result;
}

void assemble(const Context &ctx, const std::string &pdf,
              const std::vector<PageResult> &pages, const std::string &out)
{
    std::vector<ocr_page_result> results;
    for (const PageResult &page : pages)
        results.push_back({page.action, page.rotate, page.layer.c_str()});

    ocr_error err;
    check(ocr_assemble(ctx.get(), pdf.c_str(), int(results.size()),
                       results.data(), out.c_str(), &err),
          err);
}

// --- PageOcr -----------------------------------------------------------------

PageOcr::PageOcr(const Context &ctx, const std::string &pdf,
                 const std::string &tessdata, const Options &options)
    : ctx_(ctx.clone()), tessdata_(tessdata), options_(options)
{
    // Leptonica reports the image formats it is built without whenever
    // Tesseract asks for its debugging fonts; none of it concerns the user
    setMsgSeverity(L_SEVERITY_NONE);

    if (ocr_.Init(tessdata.c_str(), options.languages.c_str(),
                  tesseract::OEM_DEFAULT) != 0)
        throw Error("missing_dependency",
                    "cannot load languages " + options.languages);
    // The orientation model only exists for the legacy engine
    if (osd_.Init(tessdata.c_str(), "osd", tesseract::OEM_TESSERACT_ONLY) != 0)
        throw Error("missing_dependency", "cannot load osd");
    osd_.SetPageSegMode(tesseract::PSM_OSD_ONLY);

    ocr_error err;
    check(ocr_open(ctx_->get(), pdf.c_str(), &doc_, &err), err);
}

PageOcr::~PageOcr() { pdf_drop_document(ctx_->get(), doc_); }

PageResult PageOcr::run(int page, const std::string &workdir)
{
    ocr_page_info info;
    ocr_error err;
    check(ocr_analyze_page(ctx_->get(), doc_, page, &info, &err), err);

    PageResult result;
    if (info.has_text && !options_.force)
        return result;

    // Old text can only go together with the page's picture of it, so such
    // pages get a new image, as do straightened ones. Both need color.
    bool replace = info.has_text;
    float dpi = render_dpi(info);
    PixPtr image = render(page, dpi, replace || options_.deskew);
    result.rotate = upright(image, dpi);
    if (options_.deskew && deskew(image))
        replace = true;

    std::string base = workdir + "/page-" + std::to_string(page);
    result.layer = recognize(image.get(), dpi, base);
    result.action = replace ? OCR_REPLACE : OCR_OVERLAY;
    if (replace) {
        std::string layer = base + "-layer.pdf";
        write_layer(*ctx_, result.layer, image.get(), layer);
        result.layer = layer;
    }
    return result;
}

PixPtr PageOcr::render(int page, float dpi, bool color)
{
    fz_context *ctx = ctx_->get();
    fz_pixmap *pixmap = nullptr;
    ocr_error err;
    check(ocr_render_page(ctx, doc_, page, dpi, color, &pixmap, &err), err);

    PixPtr pix;
    try {
        pix = to_pix(fz_pixmap_width(ctx, pixmap),
                     fz_pixmap_height(ctx, pixmap),
                     fz_pixmap_components(ctx, pixmap),
                     fz_pixmap_samples(ctx, pixmap),
                     fz_pixmap_stride(ctx, pixmap));
    } catch (...) {
        fz_drop_pixmap(ctx, pixmap);
        throw;
    }
    fz_drop_pixmap(ctx, pixmap);
    pixSetResolution(pix.get(), int(dpi), int(dpi));
    return pix;
}

// Turn the page upright when Tesseract is sure enough which way is up;
// returns the clockwise rotation it needed
int PageOcr::upright(PixPtr &image, float dpi)
{
    int orientation = 0;
    float confidence = 0, script_confidence = 0;
    const char *script = nullptr;

    osd_.SetImage(image.get());
    osd_.SetSourceResolution(int(dpi));
    if (!osd_.DetectOrientationScript(&orientation, &confidence, &script,
                                      &script_confidence) ||
        confidence < ROTATE_THRESHOLD || orientation == 0)
        return 0;

    // Tesseract reports how far the text is turned counterclockwise
    int rotate = 360 - orientation;
    PixPtr turned(pixRotateOrth(image.get(), rotate / 90));
    if (!turned)
        throw std::bad_alloc();
    image = std::move(turned);
    return rotate;
}

// Tesseract's own text-only PDF page, as OCRmyPDF uses it
std::string PageOcr::recognize(PIX *image, float dpi, const std::string &base)
{
    ocr_.SetImage(image);
    ocr_.SetSourceResolution(int(dpi));

    tesseract::TessPDFRenderer renderer(base.c_str(), tessdata_.c_str(), true);
    bool ok = renderer.BeginDocument("") && ocr_.Recognize(nullptr) == 0 &&
              renderer.AddImage(&ocr_) && renderer.EndDocument();
    if (!ok)
        throw Error("other", "Tesseract could not write " + base + ".pdf");
    return base + ".pdf";
}

} // namespace ocr
