# e32 test suites

Run everything, keep the results, and update the ledger and the records:

    tests/run_all.sh          # from the e32 directory

JUnit XML goes to `tests/results/`. `tools/tracecheck.py --record-status`
then writes the ledger (`docs/traceability.md`: every rule, scenario and
test with its result, and the Phase 6 audit), records stories and epics
that became Done or were reopened in `docs/stories.md` and
`docs/epics.md`, and regenerates the work view (`docs/backlog.md`). See
[`../docs/README.md`](../docs/README.md#status-and-the-ledger).

## pytest-bdd (feature files)

`tests/bdd/` binds every scenario of the feature files,
`docs/features/<level>/*.feature`, to an executable pytest test, except the
scenarios tagged `@gtest`: the GoogleTest suite implements those, and
`conftest.py` deselects them. Gherkin `Rule:` blocks are supported (tags on
a rule reach its scenarios as markers); a file whose rules have no scenario
yet is skipped.

    cd e32 && python3 -m pytest tests/bdd           # all scenarios
    cd e32 && python3 -m pytest tests/bdd -q -rs    # with skip reasons

Requirements: Python 3, `pytest` and `pytest-bdd` (`pip install pytest pytest-bdd`).
Optional: `pyserial` for a board.

### Scenario IDs and test names

A scenario's pytest-bdd binding is its test **T01**. Each test function is
named after the scenario ID: `CMP-21-S01: GPIO unit test against a fake
register file` becomes

    tests/bdd/test_features.py::test_CMP_21_S01_T01_gpio_unit_test_against_a_fake_register_file

Scenario outlines add one parameter per Examples row, such as `[0-0xe9-magic]`.
Select by ID with `-k`. Write the hyphens as underscores; matching ignores case:

    python3 -m pytest tests/bdd -k CMP_21_S01           # one scenario
    python3 -m pytest tests/bdd -k CMP_21_S01_T01       # the same, by test ID
    python3 -m pytest tests/bdd -k "CMP_27_S01 and Double"   # one Examples row (by its text)
    python3 -m pytest tests/bdd -k "CMP_19 or CMP_21"   # several

Gherkin tags become markers, again with `-` replaced by `_`: `@SYS-12` becomes
`SYS_12`, `@VER-SYS-09` becomes `VER_SYS_09`, `@EP-01` becomes `EP_01`, and
`@FEAT-042` becomes `FEAT_042`. `@host`, `@qemu`, `@hardware`, `@pending` and `@gtest` keep their
names. Select by marker with `-m`:

    python3 -m pytest tests/bdd -m VER_SYS_09
    python3 -m pytest tests/bdd -m "host and not pending"

`conftest.py` registers every tag it finds in the feature files, so
`--strict-markers` stays on.

### Environment variables

| Variable | Meaning | Default |
|---|---|---|
| `CROSS_COMPILE` | Cross-toolchain prefix; `${CROSS_COMPILE}gcc` must be on the PATH | `xtensa-esp32-elf-` |
| `QEMU` | Espressif QEMU binary | `qemu-system-xtensa` on the PATH |
| `E32_PORT` | Serial port of a physical board; turns on `@hardware` | unset |
| `E32_GTEST_BIN` | GoogleTest binary used by the host unit scenarios | `tests/gtest/build/e32_tests` |
| `E32_TIMEOUT` / `E32_BOOT_TIMEOUT` | Console wait limits, in seconds | 15 / 30 |
| `E32_BDD_FORCE_ALL` | `1` turns off every environment skip (see below) | unset |
| `HOSTCC` | Host C compiler that builds `tools/mkimage` | `cc` |

esptool is found as `esptool` or `esptool.py` on the PATH.

### What runs, what skips, what fails

Rules are applied in this order. The first rule that applies decides.

1. **Collection-time skips.** No step runs. Each skip gives a precise reason.
   * `@hardware`: skipped unless `E32_PORT` is set.
   * `@qemu`: skipped unless QEMU **and** the cross compiler are present.
   * `@qemu @hardware`: runs if either QEMU (with the cross compiler) or a
     board is available. QEMU is preferred.
2. **Every step must have a definition.** This is checked before the first
   step. `test_step_catalogue.py` also checks it statically for every
   rendered step of every scenario, whatever the environment. Each step
   must match exactly one definition.
3. **`@pending` fails red.** A `@pending` scenario that is not skipped fails
   with `PENDING automation: ...`. This is the red state of the BDD pipeline.
   Three `@pending` scenarios are automated and run normally. They are listed
   in `AUTOMATED_PENDING` in `conftest.py`:
   * `SW-IMG-03-S01`: crafted ELF files run against the real `tools/mkimage`.
   * `CMP-21-S01` and `SW-FMT-01-S01`: delegated to GoogleTest.
4. **Per-step tool skips.**
   * Steps that need the cross toolchain skip when it is absent. These include
     building the firmware, `make` targets, objdump, nm and build variants.
   * esptool steps skip without esptool.
   * QEMU steps skip without QEMU.
   * The host unit steps skip with "GoogleTest suite not built" when the
     binary is missing.

`E32_BDD_FORCE_ALL=1` turns off rules 1 and 4. Every step of every scenario
then executes up to its first failure, so missing tools show up as failures
at the tool invocation. Use it to prove that every step resolves.

### Host unit scenarios run through GoogleTest

These steps do not compile C in Python:

* `pp_printf.c compiled for the host`
* `lib.c compiled for the host ...`
* `gpio.c compiled for the host ...`

Instead they run the GoogleTest binary with the scenario ID as the filter.
For example, `CMP-21-S01` runs:

    tests/gtest/build/e32_tests --gtest_filter=*CMP_21_S01*

The step requires exit status 0 and at least one test reported as
`[  PASSED  ] N tests`. The remaining steps of the scenario are covered by
that run. Build the binary first:

    cmake -S tests/gtest -B tests/gtest/build && cmake --build tests/gtest/build

### Isolation

* Each scenario builds in its own copy of the e32 tree, under pytest's
  `tmp_path`. Build variants patch only that copy.
* `/tmp/...` paths in steps are mapped into the scenario's temp directory.
* "The traceability matrix is up to date" regenerates the matrix in the copy
  and compares it with `docs/traceability.md`.
* The working tree is never written.

### The QEMU console harness

`tests/bdd/qemu_console.py` drives the console:

* It builds `flash.img` with `make flash.img`.
* It starts `$QEMU -nographic -machine esp32 -drive file=flash.img,if=mtd,format=raw`.
* For ROM download mode, it uses `empty.img`, `strap_mode` `0x0f`, and
  `-serial tcp::5556,server,nowait`. It runs esptool `load-ram`, then
  connects to the TCP port.

The harness keeps the full byte transcript, which the CR LF check uses. It
provides:

* `send()`
* `enter()`, which sends the line followed by CR
* `wait_for()` and `wait_for_line()`, with timeouts
* `prompt()`, which waits for `> ` at the start of a line

A literal Ctrl-A is doubled, because QEMU's `-nographic` multiplexer uses
Ctrl-A as its escape key. QEMU is killed when the scenario ends.

**The harness has not yet run against a real QEMU**, because neither QEMU nor
the cross compiler was available when it was written.

## GoogleTest + GoogleMock (unit, scenario and end-to-end)

    sudo apt-get install libgtest-dev libgmock-dev      # once
    cmake -S tests/gtest -B tests/gtest/build
    cmake --build tests/gtest/build
    tests/gtest/build/e32_tests                         # or: ctest --test-dir tests/gtest/build
    tests/gtest/build/e32_tests --gtest_filter='*CMP_21_S01*'   # one scenario

### Layout

| Path | What |
|---|---|
| `host/e32_host.h` | What the firmware calls instead of hardware when built with `-DE32_HOST` (see `include/types.h`, `include/xtensa.h`) |
| `host/sim.{h,cpp}` | The simulated SoC: `FakeSoc` (memory, UART0, interrupt matrix, RTC reset), a `Cpu` model (CCOUNT, CCOMPARE0, INTENABLE, PS.INTLEVEL, `waiti`, level-1 dispatch) and the GoogleMock `MockBus` |
| `support/fixtures.h` | `SimTest` (fresh SoC per test, `NiceMock<MockBus>` delegating to the fake), `MonitorTest` (drives `mimmo()` through the console), `E32_IN_FRESH_PROCESS` |
| `support/bdd.h` | `GIVEN` / `WHEN` / `THEN` / `AND`: each step becomes a scoped trace in failure messages |
| `support/process.h` | Running host commands; `XtensaElf` builds ELF files byte by byte |
| `unit/` | One file per firmware C file: the `@gtest` scenarios (T01 onwards), plus T02 onwards of host scenarios that pytest-bdd also binds |
| `e2e/` | `tools/mkimage` as a process on crafted ELF files; the firmware booted in QEMU (skipped without `$QEMU` and `flash.img`) |
| `stubs/` | Empty implementations, for the red check |

The firmware's libc-clashing names are renamed for the host build only
(`putc` → `e32_putc`, `printf` → `pp_printf`, `main` → `e32_main`, …), so
the test binary keeps the real C library.

### Test names

`TEST_F(Suite, <SCENARIO>_Tnn_<what>)`, e.g. `CMP_21_S01_T02_flash_pin_is_refused_with_no_register_written`.
`tools/tracecheck.py` reads these names, so a test must start with the ID
of an existing scenario. T01 of a scenario not tagged `@gtest` belongs to
its pytest-bdd binding; GoogleTest numbers those from T02. A scenario that
only GoogleTest implements is tagged `@gtest` and numbered from T01.
Scenario Outlines become `TEST_P` with one instance per Examples row.

### Mocks, fakes and isolation

* Every register access goes through `MockBus`, which forwards to the
  `FakeSoc` unless a test sets an expectation. Tests use `EXPECT_CALL` with
  `InSequence` for exact write orders (wdt, GPIO), and `.Times(0)` for
  "nothing written".
* The firmware's endless loops end by exception: `InputExhausted` when it
  waits for input that will never come, `Rebooted` when it writes the RTC
  reset bit. The C files are compiled with `-fexceptions`.
* State that only moves one way (`serial_irq_init`, `panic_handler`,
  `main`) is tested inside `E32_IN_FRESH_PROCESS`: a forked child whose
  failures are reported through the parent's `EXPECT_EXIT`.

### Red check (Phase 3)

    cmake -S tests/gtest -B tests/gtest/build-red -DE32_RED=ON
    cmake --build tests/gtest/build-red && tests/gtest/build-red/e32_tests

This links the empty stubs in place of the firmware and `mkimage`. Expected
result: every runnable test fails on an assertion (no crash, no build
error), and the 2 QEMU tests skip. On 2026-11-14 the result was 0 passed,
103 failed, 2 skipped. Against the real firmware: 103 passed, 2 skipped.
