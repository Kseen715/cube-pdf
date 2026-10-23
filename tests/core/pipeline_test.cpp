// core/src/ocr.cpp: the pipeline the native program and the web share

#include <string>
#include <vector>

#include "check.hpp"
#include "support.hpp"

using test::TempDir;

namespace {

ocr::Options english(bool force = false)
{
    ocr::Options options;
    options.languages = "eng";
    options.force = force;
    return options;
}

// Every page of input through PageOcr, then assembled into out
std::vector<ocr::PageResult> recognize(const ocr::Context &ctx,
                                       const std::string &input,
                                       const ocr::Options &options,
                                       const TempDir &dir,
                                       const std::string &out)
{
    ocr::Input prepared = ocr::prepare(ctx, input, dir.path());
    ocr::PageOcr ocr(ctx, prepared.pdf, test::tessdata(), options);
    std::vector<ocr::PageResult> pages;
    for (int page = 0; page < prepared.pages; page++)
        pages.push_back(ocr.run(page, dir.path()));
    ocr::assemble(ctx, prepared.pdf, pages, out);
    return pages;
}

} // namespace

TEST(a_scan_gets_a_text_layer)
{
    ocr::Context ctx;
    TempDir dir;
    std::string out = dir.file("out.pdf");
    auto pages = recognize(ctx, test::scan_png(ctx, dir), english(), dir, out);
    REQUIRE(pages.size() == 1);
    CHECK_EQ(pages[0].action, OCR_OVERLAY);
    CHECK_EQ(pages[0].rotate, 0);
    CHECK(test::has_words(test::page_text(ctx, out)));
}

TEST(a_turned_scan_is_turned_upright)
{
    ocr::Context ctx;
    TempDir dir;
    std::string out = dir.file("out.pdf");
    auto pages =
        recognize(ctx, test::scan_png(ctx, dir, 270), english(), dir, out);
    REQUIRE(pages.size() == 1);
    CHECK_EQ(pages[0].rotate, 90);
    CHECK_EQ(test::page_rotation(ctx, out), 90);
    CHECK(test::has_words(test::page_text(ctx, out)));
}

TEST(pages_with_text_are_skipped)
{
    ocr::Context ctx;
    TempDir dir;
    std::string input = test::text_pdf(ctx, dir);
    ocr::PageOcr ocr(ctx, input, test::tessdata(), english());
    CHECK_EQ(ocr.run(0, dir.path()).action, OCR_SKIP);
}

TEST(force_replaces_old_text)
{
    ocr::Context ctx;
    TempDir dir;
    std::string out = dir.file("out.pdf");
    auto pages =
        recognize(ctx, test::text_pdf(ctx, dir), english(true), dir, out);
    REQUIRE(pages.size() == 1);
    CHECK_EQ(pages[0].action, OCR_REPLACE);
    CHECK(test::has_words(test::page_text(ctx, out)));
}

TEST(a_missing_language_is_a_missing_dependency)
{
    ocr::Context ctx;
    TempDir dir;
    ocr::Options options = english();
    options.languages = "xyz";
    try {
        ocr::PageOcr ocr(ctx, test::text_pdf(ctx, dir), test::tessdata(),
                         options);
        CHECK(!"PageOcr loaded a language that does not exist");
    } catch (const ocr::Error &e) {
        CHECK_EQ(e.kind(), "missing_dependency");
    }
}
