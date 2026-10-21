// Moving pixels between MuPDF (rows of bytes) and Leptonica (PIX)
#pragma once

#include <cstddef>
#include <memory>
#include <vector>

#include <leptonica/allheaders.h>

namespace ocr {

struct PixDeleter {
    void operator()(PIX *pix) const { pixDestroy(&pix); }
};
using PixPtr = std::unique_ptr<PIX, PixDeleter>;

// Rows of w pixels of n bytes each: 1 for gray, 3 for RGB
struct Samples {
    int w = 0, h = 0, n = 1;
    std::vector<unsigned char> bytes;

    std::ptrdiff_t stride() const { return std::ptrdiff_t(w) * n; }
};

PixPtr to_pix(int w, int h, int n, const unsigned char *rows,
              std::ptrdiff_t stride);

// An RGB image without any color comes back as gray, a third of the size
Samples to_samples(PIX *pix);

} // namespace ocr
