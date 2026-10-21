#include "pdfa.hpp"

namespace ocr {

// The ICC profile is the one compiled into Ghostscript itself
const char PDFA_DEFINITIONS[] = R"(%!
[/_objdef {icc_PDFA} /type /stream /OBJ pdfmark
[{icc_PDFA} << /N 3 >> /PUT pdfmark
[{icc_PDFA} (%rom%iccprofiles/srgb.icc) (r) file /PUT pdfmark
[/_objdef {OutputIntent_PDFA} /type /dict /OBJ pdfmark
[{OutputIntent_PDFA} <<
  /Type /OutputIntent
  /S /GTS_PDFA1
  /DestOutputProfile {icc_PDFA}
  /OutputConditionIdentifier (sRGB)
>> /PUT pdfmark
[{Catalog} << /OutputIntents [ {OutputIntent_PDFA} ] >> /PUT pdfmark
)";

// Images keep their compression and resolution: JPEGs pass through, the
// rest is compressed losslessly
std::vector<std::string> pdfa_args(const std::string &definitions,
                                   const std::string &in,
                                   const std::string &out)
{
    return {
        "-dQUIET",
        "-dBATCH",
        "-dNOPAUSE",
        "-dSAFER",
        "-sDEVICE=pdfwrite",
        "-dPDFA=2",
        "-dPDFACompatibilityPolicy=1",
        "-dCompatibilityLevel=1.7",
        "-sColorConversionStrategy=LeaveColorUnchanged",
        "-dAutoRotatePages=/None",
        "-dDownsampleColorImages=false",
        "-dDownsampleGrayImages=false",
        "-dDownsampleMonoImages=false",
        "-dAutoFilterColorImages=false",
        "-dAutoFilterGrayImages=false",
        "-dColorImageFilter=/FlateEncode",
        "-dGrayImageFilter=/FlateEncode",
        "-dPassThroughJPEGImages=true",
        "-dPassThroughJPXImages=true",
        "-sOutputFile=" + out,
        definitions,
        in,
    };
}

} // namespace ocr
