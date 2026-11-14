// bdd.h -- Given/When/Then steps inside GoogleTest tests.
//
// Each step adds a scoped trace, so a failing assertion is reported with
// the scenario steps that led to it:
//
//   TEST_F(GpioTest, CMP_21_S01_T02_invalid_pin_writes_nothing) {
//     GIVEN("gpio.c with a recording register bus");
//     WHEN("gpio_dir_af(7, 1, 1, 0) is called");
//     int r = gpio_dir_af(7, 1, 1, 0);
//     THEN("it returns -1");
//     EXPECT_EQ(r, -1);
//   }
//
// Test names start with the scenario ID and a test number
// (<SCENARIO>_Tnn) so tools/tracecheck.py can link them back to the
// .feature files.
#ifndef E32_TESTS_BDD_H
#define E32_TESTS_BDD_H

#include <string>

#include <gtest/gtest.h>

#define E32_BDD_CAT2(a, b) a##b
#define E32_BDD_CAT(a, b) E32_BDD_CAT2(a, b)
#define E32_BDD_STEP(keyword, text)                                  \
  ::testing::ScopedTrace E32_BDD_CAT(e32_bdd_step_, __LINE__)(        \
      __FILE__, __LINE__, std::string(keyword) + " " + (text))

#define GIVEN(text) E32_BDD_STEP("Given", text)
#define WHEN(text) E32_BDD_STEP("When", text)
#define THEN(text) E32_BDD_STEP("Then", text)
#define AND(text) E32_BDD_STEP("And", text)

#endif  // E32_TESTS_BDD_H
