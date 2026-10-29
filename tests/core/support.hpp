// What the core's tests share: where the built programs are, a scratch
// folder per test, the fixture files and running ocr-pdf-core
#pragma once

#include <filesystem>
#include <string>
#include <vector>

#include "ocr.hpp"

namespace test {

// The text on every fixture page, and words OCR has to find in it
extern const std::string TEXT;
extern const std::vector<std::string> WORDS;
constexpr int SCAN_DPI = 300;

// The folder with ocr-pdf-core, ocr-pdf-gs and tessdata (main.cpp)
void set_bin_dir(const std::string &dir);
std::string bin_dir();
std::string tessdata();

class TempDir {
public:
    TempDir();
    ~TempDir();
    TempDir(const TempDir &) = delete;
    TempDir &operator=(const TempDir &) = delete;

    std::string file(const std::string &name) const;
    std::string path() const { return path_.string(); }

private:
    std::filesystem::path path_;
};

void write_file(const std::string &path, const std::string &content);
bool exists(const std::string &path);

// Fixtures, made with the context of the test; failing to make one stops
// the test
std::string text_pdf(const ocr::Context &ctx, const TempDir &dir,
                     int rotate = 0);
// skew: degrees the paper lay turned on the scanner
std::string scan_png(const ocr::Context &ctx, const TempDir &dir,
                     int rotate = 0, int skew = 0);
// A camera's photo of the page turned by rotate, with an EXIF orientation
std::string photo_jpeg(const ocr::Context &ctx, const TempDir &dir,
                       int rotate, int orientation);
std::string scan_tiff(const ocr::Context &ctx, const TempDir &dir, int pages);
std::string encrypted_pdf(const ocr::Context &ctx, const TempDir &dir);

std::string page_text(const ocr::Context &ctx, const std::string &pdf,
                      int page = 0);
int page_rotation(const ocr::Context &ctx, const std::string &pdf);
bool has_output_intent(const ocr::Context &ctx, const std::string &pdf);
bool has_words(const std::string &text);

struct Output {
    int code;
    std::string stdout_text;
};

// ocr-pdf-core with args, its stdout and exit code
Output run_core(const std::vector<std::string> &args);

} // namespace test
