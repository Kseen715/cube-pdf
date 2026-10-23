// test-core: the tests of the OCR core (core/src), run by "make test".
//
//   test-core BIN_DIR
//
// BIN_DIR holds the built ocr-pdf-core, ocr-pdf-gs and tessdata.

#include <cstdio>

#include "check.hpp"
#include "support.hpp"

int main(int argc, char **argv)
{
    if (argc != 2) {
        std::fputs("usage: test-core BIN_DIR\n", stderr);
        return 2;
    }
    test::set_bin_dir(argv[1]);
    return check::run_all();
}
