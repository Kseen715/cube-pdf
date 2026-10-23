// core/src/cli.cpp: ocr-pdf-core as the desktop and Android apps run it

#include <string>
#include <vector>

#include "check.hpp"
#include "support.hpp"

using test::TempDir;

namespace {

// The exit code of a usage error, as opposed to a failed run
constexpr int USAGE_CODE = 2;

test::Output run(const std::string &input, const std::string &output,
                 std::vector<std::string> extra = {})
{
    std::vector<std::string> args = {"run", "--input", input, "--output",
                                     output, "--languages", "eng"};
    args.insert(args.end(), extra.begin(), extra.end());
    return test::run_core(args);
}

bool says(const test::Output &output, const std::string &fields)
{
    return output.stdout_text.find(fields) != std::string::npos;
}

} // namespace

TEST(run_makes_a_searchable_pdfa)
{
    ocr::Context ctx;
    TempDir dir;
    std::string out = dir.file("scan_ocr.pdf");
    test::Output output = run(test::scan_png(ctx, dir), out, {"--jobs", "2"});
    CHECK_EQ(output.code, 0);
    CHECK(says(output, R"("event":"progress","stage":"ocr","done":1)"));
    CHECK(says(output, R"("event":"done","output":")" + out + "\""));
    CHECK(!says(output, R"("level":"warning")"));
    REQUIRE(test::exists(out));
    CHECK(!test::exists(out + ".part"));
    CHECK(test::has_words(test::page_text(ctx, out)));
    CHECK(test::has_output_intent(ctx, out));
}

TEST(run_without_ghostscript_still_delivers)
{
    ocr::Context ctx;
    TempDir dir;
    std::string out = dir.file("out.pdf");
    test::Output output = run(test::scan_png(ctx, dir), out,
                              {"--gs", dir.file("no-such-gs")});
    CHECK_EQ(output.code, 0);
    CHECK(says(output, R"("level":"warning")"));
    REQUIRE(test::exists(out));
    CHECK(test::has_words(test::page_text(ctx, out)));
    CHECK(!test::has_output_intent(ctx, out));
}

TEST(run_reports_each_kind_of_failure)
{
    ocr::Context ctx;
    TempDir dir;
    std::string out = dir.file("out.pdf");
    struct Case {
        std::string input, kind;
    } cases[] = {
        {test::text_pdf(ctx, dir), "has_text"},
        {test::encrypted_pdf(ctx, dir), "encrypted"},
        {dir.file("missing.pdf"), "bad_input"},
    };
    for (const Case &c : cases) {
        test::Output output = run(c.input, out);
        CHECK_EQ(output.code, 1);
        CHECK(says(output, R"("event":"error","kind":")" + c.kind + "\""));
    }
    CHECK(!test::exists(out));
}

TEST(run_reports_an_unwritable_output)
{
    ocr::Context ctx;
    TempDir dir;
    test::Output output =
        run(test::scan_png(ctx, dir), dir.file("no/such/folder/out.pdf"));
    CHECK_EQ(output.code, 1);
    CHECK(says(output, R"("kind":"output_access")"));
}

TEST(bad_arguments)
{
    test::Output output = test::run_core({"run", "--input", "a.pdf"});
    CHECK_EQ(output.code, 1);
    CHECK(says(output, R"("event":"error","kind":"other")"));
    CHECK_EQ(test::run_core({}).code, USAGE_CODE);
    CHECK_EQ(test::run_core({"convert"}).code, USAGE_CODE);
}

TEST(expand_lists_what_the_app_can_take)
{
    TempDir dir;
    std::string folder = dir.file("in");
    for (const char *name : {"a.PDF", "sub/b.png", "sub/b_ocr.pdf",
                             "c.txt", "z\"q.jpg"})
        test::write_file(folder + "/" + name, "");
    std::string named = dir.file("notes.txt");
    test::write_file(named, "");

    test::Output output = test::run_core(
        {"expand", "--extensions", ".PDF,.png,.jpg", "--skip-suffix", "_ocr",
         folder, named, dir.file("missing")});
    CHECK_EQ(output.code, 0);
    CHECK_EQ(output.stdout_text,
             "[\"" + folder + "/a.PDF\",\"" + folder + "/sub/b.png\",\"" +
                 folder + "/z\\\"q.jpg\",\"" + named + "\"]\n");
}
