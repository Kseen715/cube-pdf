// A small test runner, so the core's tests need no library of their own:
//
//   TEST(name) { CHECK(condition); CHECK_EQ(actual, expected); }
//
// A failed CHECK is reported and the test goes on; REQUIRE stops the test.
// Any exception a test throws fails it too.
#pragma once

#include <sstream>
#include <stdexcept>
#include <string>

namespace check {

struct Stop : std::runtime_error {
    using std::runtime_error::runtime_error;
};

void add(const char *name, void (*run)());
void fail(const char *file, int line, const std::string &what);
int run_all();

struct Register {
    Register(const char *name, void (*run)()) { add(name, run); }
};

template <class A, class B>
void equal(const A &actual, const B &expected, const char *what,
           const char *file, int line)
{
    if (actual == expected)
        return;
    std::ostringstream message;
    message << what << ": got " << actual << ", expected " << expected;
    fail(file, line, message.str());
}

} // namespace check

#define TEST(name)                                                         \
    static void test_##name();                                             \
    static check::Register register_##name(#name, test_##name);            \
    static void test_##name()

#define CHECK(condition)                                                   \
    ((condition) ? void() : check::fail(__FILE__, __LINE__, #condition))

#define CHECK_EQ(actual, expected)                                         \
    check::equal((actual), (expected), #actual, __FILE__, __LINE__)

#define REQUIRE(condition)                                                 \
    ((condition) ? void() : throw check::Stop(#condition))
