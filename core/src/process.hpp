// Starting Ghostscript from the native program
#pragma once

#include <string>
#include <vector>

namespace ocr {

// Run program with args and wait for it. Its output goes to our stderr,
// since stdout carries the JSON messages, and it is killed when this
// process dies. Returns its exit code, or -1 if it could not start.
int run_program(const std::string &program,
                const std::vector<std::string> &args);

// The folder of the running executable, in UTF-8
std::string program_dir();

} // namespace ocr
