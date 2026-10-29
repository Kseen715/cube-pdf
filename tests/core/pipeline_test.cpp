// core/src/ocr.cpp: the pipeline the native program and the web share

#include <string>
#include <vector>

#include "check.hpp"
#include "support.hpp"

using test::TempDir;

namespace {

// Degrees the paper lay turned on the scanner, within what deskew finds
constexpr int SKEW = 3;

ocr::Options english(bool force = false)
{
    ocr::Options options;
    options.languages = "eng";
    options.force = force;
    return options;
}

ocr::Options deskewing()
{
    ocr::Options options = english();
    options.deskew = true;
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

// Tesseract's text is invisible, and still text
TEST(a_page_made_searchable_before_is_skipped)
{
    ocr::Context ctx;
    TempDir dir;
    std::string out = dir.file("out.pdf");
    recognize(ctx, test::scan_png(ctx, dir), english(), dir, out);
    ocr::PageOcr ocr(ctx, out, test::tessdata(), english());
    CHECK_EQ(ocr.run(0, dir.path()).action, OCR_SKIP);
}

// EXIF 6 turns the picture a quarter clockwise, 8 counterclockwise
TEST(a_photo_is_read_the_way_the_camera_shows_it)
{
    ocr::Context ctx;
    TempDir dir;
    std::string out = dir.file("out.pdf");
    struct Case {
        int rotate, orientation;
    } cases[] = {{270, 6}, {90, 8}};
    for (const Case &c : cases) {
        std::string photo = test::photo_jpeg(ctx, dir, c.rotate, c.orientation);
        auto pages = recognize(ctx, photo, english(), dir, out);
        REQUIRE(pages.size() == 1);
        CHECK_EQ(pages[0].rotate, 0);
        CHECK(test::has_words(test::page_text(ctx, out)));
    }
}

// A straightened page gets a new picture under its text
TEST(deskew_straightens_a_skewed_scan)
{
    ocr::Context ctx;
    TempDir dir;
    std::string out = dir.file("out.pdf");
    auto pages = recognize(ctx, test::scan_png(ctx, dir, 0, SKEW),
                           deskewing(), dir, out);
    REQUIRE(pages.size() == 1);
    CHECK_EQ(pages[0].action, OCR_REPLACE);
    CHECK(test::has_words(test::page_text(ctx, out)));
}

TEST(deskew_leaves_a_straight_scan_alone)
{
    ocr::Context ctx;
    TempDir dir;
    auto pages = recognize(ctx, test::scan_png(ctx, dir), deskewing(), dir,
                           dir.file("out.pdf"));
    REQUIRE(pages.size() == 1);
    CHECK_EQ(pages[0].action, OCR_OVERLAY);
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

TEST(a_failure_is_named_by_its_kind)
{
    ocr::Context ctx;
    TempDir dir;
    struct Case {
        std::string input, kind;
    } cases[] = {
        {test::encrypted_pdf(ctx, dir), "encrypted"},
        {dir.file("missing.pdf"), "bad_input"},
    };
    for (const Case &c : cases) {
        try {
            ocr::prepare(ctx, c.input, dir.path());
            CHECK(!"prepare took a file it cannot read");
        } catch (const ocr::Error &e) {
            CHECK_EQ(e.kind(), c.kind);
        }
    }
}
