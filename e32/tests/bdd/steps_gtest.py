"""
Host unit scenarios (firmware C units compiled for the host).  These are
NOT re-implemented here: the "compiled for the host" step runs the
GoogleTest binary built from tests/gtest with a filter naming the scenario
ID (e.g. --gtest_filter=*CMP_21_S01*) and requires it to pass with at least
one test.  The remaining steps of the scenario are covered by that run.
"""
import re
import subprocess

import pytest
from pytest_bdd import parsers, step

from support import ENV, GTEST_BIN, Result, World

R = parsers.re
_cache = {}


def gtest_filter(sid):
    return f"*{sid.replace('-', '_')}*"


def run_gtest(world: World):
    assert world.sid, "scenario has no ID"
    if not GTEST_BIN.exists() and not ENV.force:
        pytest.skip("GoogleTest suite not built (see tests/README.md)")
    filt = gtest_filter(world.sid)
    if filt not in _cache:
        cmd = [str(GTEST_BIN), f"--gtest_filter={filt}"]
        try:
            p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=300)
            _cache[filt] = Result(" ".join(cmd), p.returncode, p.stdout.decode("utf-8", "replace"))
        except FileNotFoundError as exc:
            _cache[filt] = Result(" ".join(cmd), 127, str(exc))
    res = world.gtest = _cache[filt]
    assert res.rc == 0, f"{res.cmd} exited {res.rc}:\n{res.out[-4000:]}"
    m = re.search(r"\[  PASSED  \] (\d+) tests?", res.out)
    assert m and int(m.group(1)) > 0, f"no GoogleTest test matched {filt}:\n{res.out[-2000:]}"


def covered(world: World):
    """A step whose check lives in the GoogleTest run of this scenario."""
    assert world.gtest is not None and world.gtest.rc == 0, \
        "the GoogleTest run for this scenario did not pass"


@step("pp_printf.c compiled for the host")
@step("lib.c compiled for the host with its functions renamed")
@step("gpio.c compiled for the host with readl and writel recording into an array")
def compiled_for_host(world):
    run_gtest(world)


@step(R(r'I format (?P<fmt>".*") with (?P<args>.+)'))
@step("pp_sprintf produces the same string as snprintf")
@step("it returns the same length")
@step(R(r'the result is (?P<result>".*")'))
@step(R(r"I compare memset for lengths 0 to 64, memcpy for lengths 0 to 32 at an offset, "
        r"and strlen for 4 strings with the C library"))
@step(R(r"there are (?P<n>\d+) failures"))
@step(R(r"I call gpio_dir_af\((?P<args>[^)]*)\)"))
@step("no register was written")
@step(R(r"the writes are, in order: (?P<writes>.+)"))
def covered_by_gtest(world):
    covered(world)


@step(R(r"it returns (?P<value>-?\d+)"))
def it_returns(world, value):
    if world.gtest is not None:
        covered(world)
    else:                                   # a target routine printing its result
        from steps_console import shows
        shows(world, value)
