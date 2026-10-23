// core/src/pdf.c: preparing the input, looking at pages, assembling

#include <cmath>
#include <string>

#include "check.hpp"
#include "support.hpp"

using test::TempDir;

namespace {

// The fixture page, in points (tests/core/fixtures.c)
constexpr float PAGE_WIDTH = 468, PAGE_HEIGHT = 432;

struct Prepared {
    ocr_status status;
    std::string pdf;
    int pages = 0;
};

Prepared prepare(const ocr::Context &ctx, const std::string &input,
                 const TempDir &dir)
{
    std::string image_pdf = dir.file("image.pdf");
    const char *pdf = nullptr;
    Prepared result;
    ocr_error err;
    result.status = ocr_prepare(ctx.get(), input.c_str(), image_pdf.c_str(),
                                &pdf, &result.pages, &err);
    if (pdf)
        result.pdf = pdf;
    return result;
}

ocr_page_info analyze(const ocr::Context &ctx, const std::string &path)
{
    pdf_document *doc = nullptr;
    ocr_error err;
    REQUIRE(ocr_open(ctx.get(), path.c_str(), &doc, &err) == OCR_OK);
    ocr_page_info info{};
    ocr_status status = ocr_analyze_page(ctx.get(), doc, 0, &info, &err);
    pdf_drop_document(ctx.get(), doc);
    REQUIRE(status == OCR_OK);
    return info;
}

ocr_status assemble(const ocr::Context &ctx, const std::string &input,
                    ocr_page_result page, const std::string &out)
{
    ocr_error err;
    return ocr_assemble(ctx.get(), input.c_str(), 1, &page, out.c_str(),
                        &err);
}

} // namespace

TEST(an_image_becomes_a_page_of_its_size)
{
    ocr::Context ctx;
    TempDir dir;
    Prepared prepared = prepare(ctx, test::scan_png(ctx, dir), dir);
    CHECK_EQ(prepared.status, OCR_OK);
    CHECK_EQ(prepared.pdf, dir.file("image.pdf"));
    CHECK_EQ(prepared.pages, 1);

    ocr_page_info info = analyze(ctx, prepared.pdf);
    CHECK(!info.has_text);
    CHECK(std::fabs(info.image_dpi - test::SCAN_DPI) < 1);
    CHECK(std::fabs(info.width - PAGE_WIDTH) < 1);
    CHECK(std::fabs(info.height - PAGE_HEIGHT) < 1);
}

TEST(a_pdf_is_used_as_it_is)
{
    ocr::Context ctx;
    TempDir dir;
    std::string input = test::text_pdf(ctx, dir);
    Prepared prepared = prepare(ctx, input, dir);
    CHECK_EQ(prepared.status, OCR_OK);
    CHECK_EQ(prepared.pdf, input);
    CHECK(!test::exists(dir.file("image.pdf")));

    ocr_page_info info = analyze(ctx, input);
    CHECK(info.has_text);
    CHECK_EQ(info.image_dpi, 0.0f);
}

TEST(a_turned_page_is_measured_as_shown)
{
    ocr::Context ctx;
    TempDir dir;
    ocr_page_info info = analyze(ctx, test::text_pdf(ctx, dir, 90));
    CHECK(std::fabs(info.width - PAGE_HEIGHT) < 1);
    CHECK(std::fabs(info.height - PAGE_WIDTH) < 1);
}

TEST(other_files_are_bad_input)
{
    ocr::Context ctx;
    TempDir dir;
    std::string input = dir.file("notes.pdf");
    test::write_file(input, "not a PDF at all");
    CHECK_EQ(prepare(ctx, input, dir).status, OCR_BAD_INPUT);
    CHECK_EQ(prepare(ctx, dir.file("missing.pdf"), dir).status,
             OCR_BAD_INPUT);
}

TEST(an_encrypted_pdf_is_refused)
{
    ocr::Context ctx;
    TempDir dir;
    Prepared prepared = prepare(ctx, test::encrypted_pdf(ctx, dir), dir);
    CHECK_EQ(prepared.status, OCR_ENCRYPTED);
}

TEST(assemble_draws_the_layer_and_turns_the_page)
{
    ocr::Context ctx;
    TempDir dir;
    Prepared prepared = prepare(ctx, test::scan_png(ctx, dir), dir);
    REQUIRE(prepared.status == OCR_OK);
    std::string layer = test::text_pdf(ctx, dir);
    std::string out = dir.file("out.pdf");

    std::string text = test::page_text(ctx, prepared.pdf);
    CHECK(!test::has_words(text));
    CHECK_EQ(assemble(ctx, prepared.pdf, {OCR_OVERLAY, 90, layer.c_str()},
                      out),
             OCR_OK);
    CHECK(test::has_words(test::page_text(ctx, out)));
    CHECK_EQ(test::page_rotation(ctx, out), 90);
}

TEST(assemble_leaves_skipped_pages_alone)
{
    ocr::Context ctx;
    TempDir dir;
    std::string input = test::text_pdf(ctx, dir, 270);
    std::string out = dir.file("out.pdf");
    CHECK_EQ(assemble(ctx, input, {OCR_SKIP, 0, nullptr}, out), OCR_OK);
    CHECK_EQ(test::page_rotation(ctx, out), 270);
    CHECK(test::has_words(test::page_text(ctx, out)));
}

TEST(write_layer_puts_the_image_under_the_text)
{
    ocr::Context ctx;
    TempDir dir;
    std::string text = test::text_pdf(ctx, dir);
    std::string out = dir.file("layer.pdf");
    unsigned char gray[4 * 2] = {0, 64, 128, 255, 255, 128, 64, 0};
    ocr_error err;
    CHECK_EQ(ocr_write_layer(ctx.get(), text.c_str(), 4, 2, 1, gray, 4,
                             out.c_str(), &err),
             OCR_OK);

    ocr_page_info info = analyze(ctx, out);
    CHECK(info.has_text);
    CHECK(info.image_dpi > 0);
}
