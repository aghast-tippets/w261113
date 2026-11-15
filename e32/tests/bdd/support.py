"""
Shared helpers for the e32 pytest-bdd layer: paths, environment detection,
command execution and the per-scenario World object the steps share.
"""
import os
import re
import shlex
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
E32 = HERE.parent.parent                       # the e32 project directory
FEATURES = E32 / "docs" / "features"           # docs/features/<level>/*.feature


def feature_files():
    """Every feature file, in its level folder (framework v2.0)."""
    return sorted(FEATURES.glob("*/*.feature"))


def feature_name(path):
    """The path pytest-bdd's FeatureParser takes: relative to FEATURES."""
    return str(path.relative_to(FEATURES))
GTEST_BIN = Path(os.environ.get("E32_GTEST_BIN", E32 / "tests" / "gtest" / "build" / "e32_tests"))

ID_RE = re.compile(r"^([A-Z]+(?:-[A-Z]+)*-\d+-S\d+):")    # "CMP-21-S01: ..." -> "CMP-21-S01"

# Files copied into each scenario's private tree: never build outputs,
# never the test suites or VCS data.
_COPY_IGNORE = shutil.ignore_patterns(
    ".git", "build", ".pytest_cache", "__pycache__", "*.o", "e32.elf", "e32.bin", "e32.map",
    "e32.dis", "flash.img", "empty.img")


def scenario_id(name):
    m = ID_RE.match(name)
    return m.group(1) if m else None


def norm_tag(tag):
    """SYS-12 -> SYS_12: the marker name used for a Gherkin tag."""
    return re.sub(r"\W", "_", tag)


# --------------------------------------------------------------------------
# Environment
# --------------------------------------------------------------------------

@dataclass
class Env:
    cross_prefix: str
    cross_gcc: str | None
    qemu: str | None
    esptool: str | None
    port: str | None
    force: bool
    hostcc: str | None

    @classmethod
    def detect(cls):
        prefix = os.environ.get("CROSS_COMPILE", "xtensa-esp32-elf-")
        qemu_env = os.environ.get("QEMU")
        qemu = shutil.which(qemu_env) if qemu_env else None
        qemu = qemu or shutil.which("qemu-system-xtensa")
        return cls(
            cross_prefix=prefix,
            cross_gcc=shutil.which(prefix + "gcc"),
            qemu=qemu,
            esptool=shutil.which("esptool") or shutil.which("esptool.py"),
            port=os.environ.get("E32_PORT") or None,
            force=os.environ.get("E32_BDD_FORCE_ALL") == "1",
            hostcc=shutil.which(os.environ.get("HOSTCC", "cc")),
        )

    # Names used in skip reasons
    @property
    def cross_name(self):
        return self.cross_prefix + "gcc"

    def summary(self):
        def s(v):
            return v if v else "absent"
        return (f"cross={s(self.cross_gcc)} qemu={s(self.qemu)} esptool={s(self.esptool)} "
                f"E32_PORT={s(self.port)} gtest={'built' if GTEST_BIN.exists() else 'absent'} "
                f"force_all={self.force}")

    def environment_skip_reason(self, tags):
        """Reason to skip a scenario with these tags, or None to run it."""
        if self.force:
            return None
        qemu_ok = bool(self.qemu and self.cross_gcc)
        board_ok = bool(self.port)
        if "qemu" in tags and "hardware" in tags:
            if qemu_ok or board_ok:
                return None
            return ("@qemu @hardware: needs QEMU (+ cross compiler) or a board; "
                    f"{self._qemu_missing()}, and E32_PORT is not set")
        if "hardware" in tags and not board_ok:
            return "@hardware: needs a physical board; set E32_PORT (e.g. /dev/ttyUSB0)"
        if "qemu" in tags and not qemu_ok:
            return f"@qemu: {self._qemu_missing()}"
        return None

    def _qemu_missing(self):
        missing = []
        if not self.qemu:
            missing.append("qemu-system-xtensa not found ($QEMU or PATH)")
        if not self.cross_gcc:
            missing.append(f"{self.cross_name} not on PATH ($CROSS_COMPILE)")
        return "; ".join(missing) or "ok"

    # Per-step requirements -------------------------------------------------

    def need_cross(self):
        if not self.cross_gcc and not self.force:
            pytest.skip(f"cross toolchain absent: {self.cross_name} not on PATH "
                        "(set CROSS_COMPILE or install xtensa-esp32-elf-gcc)")

    def need_qemu(self):
        if not self.qemu and not self.force:
            pytest.skip("qemu-system-xtensa not found (set $QEMU or add it to PATH)")

    def need_esptool(self):
        if not self.esptool and not self.force:
            pytest.skip("esptool not found (pip install esptool)")

    def need_board(self):
        if not self.port and not self.force:
            pytest.skip("no board: set E32_PORT")

    def need_hostcc(self):
        if not self.hostcc and not self.force:
            pytest.skip("host C compiler (cc) not found")


ENV = Env.detect()


# --------------------------------------------------------------------------
# Command results
# --------------------------------------------------------------------------

@dataclass
class Result:
    cmd: str
    rc: int
    out: str          # stdout and stderr, interleaved


def run(cmd, cwd, env=None, timeout=600, input=None):
    """Run a shell command, capturing stdout+stderr together."""
    e = os.environ.copy()
    if env:
        e.update(env)
    try:
        p = subprocess.run(cmd, shell=True, cwd=str(cwd), env=e, input=input,
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                           timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        out = (exc.stdout or b"").decode("utf-8", "replace")
        return Result(cmd, -1, out + f"\n[timeout after {timeout}s]")
    return Result(cmd, p.returncode, p.stdout.decode("utf-8", "replace"))


# --------------------------------------------------------------------------
# World: everything one scenario accumulates
# --------------------------------------------------------------------------

@dataclass
class World:
    request: object
    tmp: Path
    sid: str | None
    example: dict
    tags: set = field(default_factory=set)
    tree_: Path | None = None
    result: Result | None = None
    runs: list = field(default_factory=list)          # every Result, in order
    console: object = None                             # qemu_console.Console
    qemu: object = None                                # qemu_console.QemuTarget
    vars: dict = field(default_factory=dict)           # <that address>, <pc>, ...
    gtest: Result | None = None
    data: dict = field(default_factory=dict)           # step-to-step scratch

    # The private copy of the e32 tree all builds run in -------------------
    @property
    def tree(self):
        if self.tree_ is None:
            self.tree_ = self.tmp / "e32"
            shutil.copytree(E32, self.tree_, ignore=_COPY_IGNORE)
        return self.tree_

    def path(self, name):
        """A file named in a step: absolute (after /tmp mapping) or in the tree."""
        name = self.map_tmp(name)
        p = Path(name)
        return p if p.is_absolute() else self.tree / p

    def map_tmp(self, text):
        """Steps write to /tmp/...: keep that inside the scenario's temp dir."""
        return re.sub(r"(?<![\w/])/tmp/", str(self.tmp) + "/", text)

    def make_env(self):
        env = {"CROSS_COMPILE": ENV.cross_prefix}
        if ENV.esptool:
            env["ESPTOOL"] = ENV.esptool
        if ENV.qemu:
            env["QEMU"] = ENV.qemu
        return env

    def expand(self, text):
        """Fill in <placeholders> a step text still carries."""
        def sub(m):
            key = m.group(1)
            if key in self.example:
                return str(self.example[key])
            if key in self.vars:
                return str(self.vars[key])
            if key == "path to qemu-system-xtensa":
                return ENV.qemu or "qemu-system-xtensa"
            if key == "size of e32.bin":
                return str((self.tree / "e32.bin").stat().st_size)
            if key == "pc":
                return self.console_pc()
            if key == "gpio_init":
                return self.symbol("gpio_init")
            return m.group(0)
        return re.sub(r"<([^<>]+)>", sub, text)

    def console_pc(self):
        from steps_console import get_console   # local import: avoid a cycle
        line = get_console(self).wait_for_line(r"^pc  ([0-9a-f]{8})", since=self.data.get("mark", 0))
        return re.match(r"^pc  ([0-9a-f]{8})", line).group(1)

    # Commands ---------------------------------------------------------------
    def shell(self, cmd, timeout=600, record=True):
        """Run a command from a feature step in the private tree."""
        cmd = self.map_tmp(cmd)
        if ENV.port:
            cmd = cmd.replace("/dev/ttyUSB0", ENV.port)
        cmd = rewrite_tools(cmd)
        res = run(cmd, self.tree, env=self.make_env(), timeout=timeout)
        if record:
            self.result = res
            self.runs.append(res)
        return res

    def build(self, target="all"):
        ENV.need_cross()
        res = run(f"make {target}", self.tree, env=self.make_env())
        self.runs.append(res)
        assert res.rc == 0, f"make {target} failed (rc={res.rc}):\n{res.out[-3000:]}"
        return res

    def build_mkimage(self):
        ENV.need_hostcc()
        res = run(f"{ENV.hostcc or 'cc'} -O2 -Wall tools/mkimage.c -o tools/mkimage", self.tree)
        assert res.rc == 0, f"building tools/mkimage with the host cc failed:\n{res.out}"

    def symbol(self, name):
        if name in self.vars:
            return self.vars[name]
        ENV.need_cross()
        if not (self.tree / "e32.elf").exists():
            self.build()
        res = run(f"{ENV.cross_prefix}nm e32.elf", self.tree)
        assert res.rc == 0, res.out
        m = re.search(rf"^([0-9a-f]{{8}}) \w {re.escape(name)}$", res.out, re.M)
        assert m, f"symbol {name} not in nm output"
        self.vars[name] = m.group(1)
        return m.group(1)

    def close(self):
        for obj in (self.console, self.qemu):
            try:
                if obj is not None:
                    obj.close()
            except Exception:
                pass


def rewrite_tools(cmd):
    """Point tool names in a step's command at the detected executables."""
    words = cmd.split(None, 1)
    if not words:
        return cmd
    first, rest = words[0], (words[1] if len(words) > 1 else "")
    if first.startswith("xtensa-esp32-elf-"):
        first = ENV.cross_prefix + first[len("xtensa-esp32-elf-"):]
    elif first in ("esptool", "esptool.py") and ENV.esptool:
        first = shlex.quote(ENV.esptool)
    return f"{first} {rest}".rstrip()


def needs_for_command(cmd):
    """Skip a step whose command needs an absent tool (unless forced)."""
    words = cmd.split()
    if not words:
        return
    first = words[0]
    if first.startswith("xtensa-esp32-elf-"):
        ENV.need_cross()
    elif first in ("esptool", "esptool.py"):
        ENV.need_esptool()
        if "image-info" in cmd or "image_info" in cmd:
            ENV.need_cross()            # the image must be built first
        if "-p socket://" not in cmd:
            ENV.need_board()
    elif first == "make":
        targets = [w for w in words[1:] if "=" not in w and not w.startswith("-")
                   and w not in ("2>&1",)]
        if targets != ["clean"] and "CROSS_COMPILE=" not in cmd:
            ENV.need_cross()
        if any(t in ("ram", "flash") for t in targets):
            ENV.need_esptool()
            ENV.need_board()
        if "qemu" in targets:
            ENV.need_qemu()


def bind_scenario_ids(namespace):
    """Rename the test functions pytest-bdd generated from scenario names
    ("test_cmp21s01_gpio_unit_...") to carry the scenario's test ID:
    test_CMP_21_S01_T01_gpio_unit_...  (the binding is test T01)."""
    for name, fn in list(namespace.items()):
        if not name.startswith("test_") or not callable(fn):
            continue
        doc = getattr(fn, "__doc__", "") or ""
        scen = doc.split(": ", 1)[-1]          # "<feature>: <scenario name>"
        sid = scenario_id(scen)
        if not sid:
            continue
        rest = re.sub(r"\W+", "_", scen.split(":", 1)[1]).strip("_").lower()
        new = f"test_{sid.replace('-', '_')}_T01_{rest}"
        del namespace[name]
        fn.__name__ = new
        namespace[new] = fn
