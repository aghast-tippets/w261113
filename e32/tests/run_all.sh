#!/bin/sh
# run_all.sh -- build and run both test suites, keep JUnit XML results in
# tests/results/, then regenerate docs/traceability.md from them.
#
#   tests/run_all.sh            from the e32 directory
#
# Exit status: 0 if neither suite had a failure.  Skips (no QEMU, board
# or cross compiler) are not failures; @pending scenarios are.
set -u
cd "$(dirname "$0")/.."
mkdir -p tests/results
status=0

cmake -S tests/gtest -B tests/gtest/build >/dev/null &&
	cmake --build tests/gtest/build >/dev/null || exit 2
tests/gtest/build/e32_tests --gtest_brief=1 \
	--gtest_output=xml:tests/results/gtest.xml || status=1

python3 -m pytest tests/bdd -q -p no:cacheprovider \
	--junitxml=tests/results/bdd.xml || status=1

python3 tools/tracecheck.py || status=1
exit $status
