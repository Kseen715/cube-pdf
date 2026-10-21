// The OCR pipeline, shared by the native program (cli.cpp) and the
// WebAssembly module (wasm.cpp):
//
//   prepare()   check the input, turn an image into a PDF
//   PageOcr     OCR single pages; the caller runs one per thread or worker
//   assemble()  put the text layers into a copy of the PDF
//
// Ghostscript then makes PDF/A of the result, see pdfa.hpp.
#pragma once

#include <memory>
#include <stdexcept>
#include <string>
#include <vector>

#include <tesseract/baseapi.h>

#include "image.hpp"
#include "pdf.h"

namespace ocr {

// A failure, with the kind of explanation the user gets for it
class Error : public std::runtime_error {
public:
    Error(const std::string &kind, const std::string &detail);
    const std::string &kind() const { return kind_; }

private:
    std::string kind_;
};

struct Options {
    std::string languages; // Tesseract codes joined with '+'
    bool force = false;    // also OCR pages that already have text
    bool deskew = false;   // straighten pages scanned at an angle
};

struct PageResult {
    ocr_action action = OCR_SKIP;
    int rotate = 0;
    std::string layer;
};

// A MuPDF context. Each thread needs its own: clone() makes one.
class Context {
public:
    Context();
    ~Context();
    Context(const Context &) = delete;
    Context &operator=(const Context &) = delete;

    std::unique_ptr<Context> clone() const;
    fz_context *get() const { return ctx_; }

private:
    explicit Context(fz_context *ctx) : ctx_(ctx) {}
    fz_context *ctx_;
};

struct Input {
    std::string pdf; // the input itself, or a PDF made from the image
    int pages = 0;
};

Input prepare(const Context &ctx, const std::string &input,
              const std::string &workdir);

// OCRs pages of one PDF, writing their layers into workdir. It holds a
// Tesseract instance, so each thread or worker needs its own.
class PageOcr {
public:
    PageOcr(const Context &ctx, const std::string &pdf,
            const std::string &tessdata, const Options &options);
    ~PageOcr();
    PageOcr(const PageOcr &) = delete;
    PageOcr &operator=(const PageOcr &) = delete;

    PageResult run(int page, const std::string &workdir);

private:
    PixPtr render(int page, float dpi, bool color);
    int upright(PixPtr &image, float dpi);
    std::string recognize(PIX *image, float dpi, const std::string &base);

    std::unique_ptr<Context> ctx_;
    pdf_document *doc_ = nullptr;
    std::string tessdata_;
    Options options_;
    tesseract::TessBaseAPI ocr_;
    tesseract::TessBaseAPI osd_;
};

void assemble(const Context &ctx, const std::string &pdf,
              const std::vector<PageResult> &pages, const std::string &out);

} // namespace ocr
