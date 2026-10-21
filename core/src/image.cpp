#include "image.hpp"

#include <algorithm>
#include <cstdlib>
#include <new>

namespace ocr {

namespace {

// Scanners add a little color noise to gray pages
constexpr int GRAY_TOLERANCE = 16;

// Leptonica keeps 8-bit pixels in big-endian 32-bit words
inline l_uint8 &byte_at(l_uint32 *line, int x)
{
    return reinterpret_cast<l_uint8 *>(line)[x ^ 3];
}

PixPtr new_pix(int w, int h, int depth)
{
    PixPtr pix(pixCreate(w, h, depth));
    if (!pix)
        throw std::bad_alloc();
    return pix;
}

bool has_color(PIX *pix)
{
    const int w = pixGetWidth(pix), h = pixGetHeight(pix);
    for (int y = 0; y < h; y++) {
        const l_uint32 *line = pixGetData(pix) + y * pixGetWpl(pix);
        for (int x = 0; x < w; x++) {
            l_int32 r, g, b;
            extractRGBValues(line[x], &r, &g, &b);
            if (std::max({r, g, b}) - std::min({r, g, b}) > GRAY_TOLERANCE)
                return true;
        }
    }
    return false;
}

Samples gray_samples(PIX *pix)
{
    Samples out{pixGetWidth(pix), pixGetHeight(pix), 1, {}};
    out.bytes.resize(std::size_t(out.w) * out.h);
    for (int y = 0; y < out.h; y++) {
        l_uint32 *line = pixGetData(pix) + y * pixGetWpl(pix);
        unsigned char *row = out.bytes.data() + y * out.stride();
        for (int x = 0; x < out.w; x++)
            row[x] = byte_at(line, x);
    }
    return out;
}

Samples rgb_samples(PIX *pix)
{
    Samples out{pixGetWidth(pix), pixGetHeight(pix), 3, {}};
    out.bytes.resize(std::size_t(out.w) * out.h * 3);
    for (int y = 0; y < out.h; y++) {
        const l_uint32 *line = pixGetData(pix) + y * pixGetWpl(pix);
        unsigned char *row = out.bytes.data() + y * out.stride();
        for (int x = 0; x < out.w; x++) {
            l_int32 r, g, b;
            extractRGBValues(line[x], &r, &g, &b);
            row[3 * x] = r;
            row[3 * x + 1] = g;
            row[3 * x + 2] = b;
        }
    }
    return out;
}

} // namespace

PixPtr to_pix(int w, int h, int n, const unsigned char *rows,
              std::ptrdiff_t stride)
{
    PixPtr pix = new_pix(w, h, n == 1 ? 8 : 32);
    for (int y = 0; y < h; y++) {
        const unsigned char *row = rows + y * stride;
        l_uint32 *line = pixGetData(pix.get()) + y * pixGetWpl(pix.get());
        for (int x = 0; x < w; x++) {
            if (n == 1)
                byte_at(line, x) = row[x];
            else
                composeRGBPixel(row[n * x], row[n * x + 1], row[n * x + 2],
                                &line[x]);
        }
    }
    return pix;
}

Samples to_samples(PIX *pix)
{
    if (pixGetDepth(pix) == 8)
        return gray_samples(pix);
    if (has_color(pix))
        return rgb_samples(pix);

    PixPtr gray(pixConvertRGBToLuminance(pix));
    if (!gray)
        throw std::bad_alloc();
    return gray_samples(gray.get());
}

} // namespace ocr
