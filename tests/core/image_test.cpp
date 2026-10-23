// core/src/image.cpp: pixels between MuPDF rows and Leptonica

#include <cstdlib>
#include <vector>

#include "check.hpp"
#include "image.hpp"

using ocr::Samples;

namespace {

Samples round_trip(int w, int h, int n, const std::vector<unsigned char> &rows,
                   std::ptrdiff_t stride)
{
    ocr::PixPtr pix = ocr::to_pix(w, h, n, rows.data(), stride);
    REQUIRE(pix);
    return ocr::to_samples(pix.get());
}

// Two rows of three RGB pixels
std::vector<unsigned char> rgb(unsigned char r, unsigned char g,
                               unsigned char b)
{
    std::vector<unsigned char> rows;
    for (int i = 0; i < 6; i++)
        rows.insert(rows.end(), {r, g, b});
    return rows;
}

} // namespace

TEST(gray_round_trip)
{
    std::vector<unsigned char> rows = {0, 50, 100, 150, 200, 255};
    Samples out = round_trip(3, 2, 1, rows, 3);
    CHECK_EQ(out.n, 1);
    CHECK_EQ(out.w, 3);
    CHECK_EQ(out.h, 2);
    CHECK(out.bytes == rows);
}

TEST(gray_rows_with_padding)
{
    std::vector<unsigned char> rows = {1, 2, 3, 99, 4, 5, 6, 99};
    Samples out = round_trip(3, 2, 1, rows, 4);
    CHECK(out.bytes == std::vector<unsigned char>({1, 2, 3, 4, 5, 6}));
}

TEST(color_stays_rgb)
{
    std::vector<unsigned char> rows = rgb(200, 40, 30);
    Samples out = round_trip(3, 2, 3, rows, 9);
    CHECK_EQ(out.n, 3);
    CHECK_EQ(out.stride(), 9);
    CHECK(out.bytes == rows);
}

TEST(rgb_without_color_becomes_gray)
{
    Samples out = round_trip(3, 2, 3, rgb(120, 120, 120), 9);
    CHECK_EQ(out.n, 1);
    CHECK_EQ(out.bytes.size(), size_t(6));
    for (unsigned char value : out.bytes)
        CHECK(std::abs(value - 120) <= 1);
}

TEST(scanner_noise_is_not_color)
{
    Samples out = round_trip(3, 2, 3, rgb(100, 112, 106), 9);
    CHECK_EQ(out.n, 1);
}
