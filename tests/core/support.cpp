#include "support.hpp"

#include <array>
#include <cstdio>
#include <fstream>
#include <random>

#include <sys/wait.h>

#include "check.hpp"
#include "fixtures.h"

namespace fs = std::filesystem;

namespace test {

namespace {

// Mixed case: Tesseract cannot tell which way capitals alone face
const char PARAGRAPH[] =
    "The quick brown fox jumps over the lazy dog, then\n"
    "runs back into the deep woods where it lives with\n"
    "its family of five. Every morning the fox wakes up\n"
    "early, looks around the quiet valley and listens to\n"
    "the birds singing in the tall green trees nearby.\n"
    "In the afternoon it hunts for mice and berries, and\n"
    "in the evening it returns home to rest by the river.\n"
    "Some days the weather is cold and the snow is deep,\n"
    "but the fox knows every path through the forest.\n";
const int PARAGRAPHS = 3;
const size_t TEXT_SIZE = 16384;
std::string bin;

// Quoted for the shell popen() runs
std::string quote(const std::string &arg)
{
    std::string out = "'";
    for (char c : arg)
        out += c == '\'' ? std::string("'\\''") : std::string(1, c);
    return out + "'";
}

std::string repeat(const std::string &text, int times)
{
    std::string out;
    for (int i = 0; i < times; i++)
        out += text;
    return out;
}

} // namespace

const std::string TEXT = repeat(PARAGRAPH, PARAGRAPHS);
const std::vector<std::string> WORDS = {"quick", "brown", "forest"};

void set_bin_dir(const std::string &dir) { bin = dir; }

std::string bin_dir() { return bin; }

std::string tessdata() { return bin + "/tessdata"; }

TempDir::TempDir()
{
    std::random_device random;
    path_ = fs::temp_directory_path() /
            ("ocr-pdf-test-" + std::to_string(random()));
    fs::create_directories(path_);
}

TempDir::~TempDir()
{
    std::error_code ignored;
    fs::remove_all(path_, ignored);
}

std::string TempDir::file(const std::string &name) const
{
    return (path_ / name).string();
}

void write_file(const std::string &path, const std::string &content)
{
    fs::create_directories(fs::path(path).parent_path());
    std::ofstream(path, std::ios::binary) << content;
}

bool exists(const std::string &path) { return fs::exists(path); }

std::string text_pdf(const ocr::Context &ctx, const TempDir &dir, int rotate)
{
    std::string pdf = dir.file("text-" + std::to_string(rotate) + ".pdf");
    REQUIRE(fixture_text_pdf(ctx.get(), pdf.c_str(), TEXT.c_str(), rotate) ==
            0);
    return pdf;
}

std::string scan_png(const ocr::Context &ctx, const TempDir &dir, int rotate,
                     int skew)
{
    std::string pdf = text_pdf(ctx, dir, rotate);
    std::string png = dir.file("scan-" + std::to_string(rotate) + "-" +
                               std::to_string(skew) + ".png");
    REQUIRE(fixture_page_png(ctx.get(), pdf.c_str(), SCAN_DPI, skew,
                             png.c_str()) == 0);
    return png;
}

std::string photo_jpeg(const ocr::Context &ctx, const TempDir &dir,
                       int rotate, int orientation)
{
    std::string pdf = text_pdf(ctx, dir, rotate);
    std::string jpeg = dir.file("photo-" + std::to_string(rotate) + "-" +
                                std::to_string(orientation) + ".jpg");
    REQUIRE(fixture_photo_jpeg(ctx.get(), pdf.c_str(), SCAN_DPI, orientation,
                               jpeg.c_str()) == 0);
    return jpeg;
}

std::string scan_tiff(const ocr::Context &ctx, const TempDir &dir, int pages)
{
    std::string pdf = text_pdf(ctx, dir);
    std::string tiff = dir.file("scan-" + std::to_string(pages) + ".tif");
    REQUIRE(fixture_page_tiff(ctx.get(), pdf.c_str(), SCAN_DPI, pages,
                              tiff.c_str()) == 0);
    return tiff;
}

std::string encrypted_pdf(const ocr::Context &ctx, const TempDir &dir)
{
    std::string out = dir.file("encrypted.pdf");
    REQUIRE(fixture_encrypt(ctx.get(), text_pdf(ctx, dir).c_str(),
                            out.c_str()) == 0);
    return out;
}

std::string page_text(const ocr::Context &ctx, const std::string &pdf,
                      int page)
{
    std::vector<char> text(TEXT_SIZE);
    REQUIRE(fixture_page_text(ctx.get(), pdf.c_str(), page, text.data(),
                              text.size()) == 0);
    return text.data();
}

int page_rotation(const ocr::Context &ctx, const std::string &pdf)
{
    int degrees = -1;
    REQUIRE(fixture_page_rotation(ctx.get(), pdf.c_str(), 0, &degrees) == 0);
    return degrees;
}

bool has_output_intent(const ocr::Context &ctx, const std::string &pdf)
{
    int yes = 0;
    REQUIRE(fixture_has_output_intent(ctx.get(), pdf.c_str(), &yes) == 0);
    return yes;
}

bool has_words(const std::string &text)
{
    for (const std::string &word : WORDS)
        if (text.find(word) == std::string::npos)
            return false;
    return true;
}

Output run_core(const std::vector<std::string> &args)
{
    std::string command = quote(bin + "/ocr-pdf-core");
    for (const std::string &arg : args)
        command += " " + quote(arg);

    FILE *pipe = popen(command.c_str(), "r");
    REQUIRE(pipe);
    Output output{-1, ""};
    std::array<char, 4096> chunk;
    size_t got;
    while ((got = std::fread(chunk.data(), 1, chunk.size(), pipe)) > 0)
        output.stdout_text.append(chunk.data(), got);
    int status = pclose(pipe);
    if (WIFEXITED(status))
        output.code = WEXITSTATUS(status);
    return output;
}

} // namespace test
