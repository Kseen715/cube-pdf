#include "check.hpp"

#include <cstdio>
#include <vector>

namespace check {

namespace {

struct Test {
    const char *name;
    void (*run)();
};

std::vector<Test> &tests()
{
    static std::vector<Test> all;
    return all;
}

int failures = 0;

} // namespace

void add(const char *name, void (*run)()) { tests().push_back({name, run}); }

void fail(const char *file, int line, const std::string &what)
{
    std::fprintf(stderr, "  %s:%d: %s\n", file, line, what.c_str());
    failures++;
}

int run_all()
{
    int failed_tests = 0;
    for (const Test &test : tests()) {
        std::fprintf(stderr, "%s\n", test.name);
        int before = failures;
        try {
            test.run();
        } catch (const std::exception &e) {
            fail("exception", 0, e.what());
        }
        if (failures > before)
            failed_tests++;
    }
    std::fprintf(stderr, "%zu tests, %d failed\n", tests().size(),
                 failed_tests);
    return failed_tests ? 1 : 0;
}

} // namespace check
