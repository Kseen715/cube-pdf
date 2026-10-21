// Ghostscript turns the OCR result into PDF/A-2b, as OCRmyPDF does
#pragma once

#include <string>
#include <vector>

namespace ocr {

// PostScript that adds the sRGB output intent PDF/A requires. Ghostscript
// reads it from a file named before the input; see pdfa_args().
extern const char PDFA_DEFINITIONS[];

// Ghostscript's arguments, without the program name
std::vector<std::string> pdfa_args(const std::string &definitions,
                                   const std::string &in,
                                   const std::string &out);

} // namespace ocr
