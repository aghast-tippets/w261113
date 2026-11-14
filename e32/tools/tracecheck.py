#!/usr/bin/env python3
"""
tracecheck.py -- check e32's requirement traceability and write the matrix.

    python3 tools/tracecheck.py              check, then write docs/traceability.md
    python3 tools/tracecheck.py --check      check only
    python3 tools/tracecheck.py --self-test  prove every error class is detected

Inputs:  docs/requirements/*.md   ("### ID — title" + "- **Field:** value")
         docs/features/**/*.feature  (Gherkin tags; "Scenario: <REQ>-Snn: title")
         tests/gtest/**/*.cpp     (test names <REQ>_Snn_Tnn_..., e.g. CMP_21_S01_T02_x)
         tests/bdd/               (if present: pytest-bdd binds every scenario in
                                   docs/features/*.feature as its test T01)
         docs/epics.md, docs/features.md, docs/stories.md
Exit status is 1 if any error is found.  Python 3 standard library only.
"""
import glob
import os
import re
import sys
import tempfile

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

TYPES = {  # prefix: (level name, allowed parent prefixes)
    "BR": ("Business", ()),
    "STK": ("Stakeholder", ("BR",)),
    "SYS": ("System", ("STK",)),
    "SUB": ("Subsystem", ("SYS",)),
    "HW": ("Hardware", ("SUB",)),
    "SW": ("Software", ("SUB",)),
    "IF": ("Interface", ("SYS", "SUB")),
    "CMP": ("Component", ("HW", "SW")),
    "VER": ("Verification", ()),
}
ORDER = ["BR", "STK", "SYS", "SUB", "HW", "SW", "IF", "CMP", "VER"]
NEEDS_CHILDREN = ("BR", "STK", "SYS", "SUB", "SW")  # HW, IF, CMP may be leaves
METHODS = ("Test", "Analysis", "Inspection", "Demonstration")
ENV_TAGS = {"host", "qemu", "hardware", "pending"}
ID_RE = re.compile(r"\b(?:BR|STK|SYS|SUB|HW|SW|IF|CMP|VER)(?:-[A-Z]+)?-\d+\b")
HEAD_RE = re.compile(r"^### ((?:BR|STK|SYS|SUB|HW|SW|IF|CMP|VER)(?:-[A-Z]+)?-\d+) — (.+)$")
FIELD_RE = re.compile(r"^- \*\*([A-Za-z ]+):\*\* ?(.*)$")
# "Scenario: CMP-21-S01: title" -> scenario ID, title
SCN_RE = re.compile(r"^((?:BR|STK|SYS|SUB|HW|SW|IF|CMP)(?:-[A-Z]+)?-\d+-S\d\d): (.+)$")
# GoogleTest: TEST(Suite, CMP_21_S01_T02_what) / TEST_F / TEST_P
TEST_DEF_RE = re.compile(r"\bTEST(?:_F|_P)?\(\s*\w+\s*,\s*("
                         r"(?:BR|STK|SYS|SUB|HW|SW|IF|CMP)(?:_[A-Z]+)?_\d+_S\d\d_T\d\d)")
SOURCES = ["*.c", "*.S", "*.lds", "include/*.h", "tools/mkimage.c",
           "tools/build-toolchain.sh", "Makefile"]


def prefix(rid):
    return rid.split("-")[0]


def ids_in(text):
    return ID_RE.findall(text or "")


def parse_requirements(req_dir):
    reqs, errors = {}, []
    for path in sorted(glob.glob(os.path.join(req_dir, "*.md"))):
        cur = None
        for n, line in enumerate(open(path, encoding="utf-8"), 1):
            line = line.rstrip("\n")
            m = HEAD_RE.match(line)
            if m:
                rid, title = m.groups()
                if rid in reqs:
                    errors.append(f"{os.path.basename(path)}:{n}: duplicate ID {rid}")
                cur = {"id": rid, "title": title, "file": os.path.basename(path),
                       "line": n, "fields": {}}
                reqs[rid] = cur
                continue
            if line.startswith("## ") or line.startswith("# "):
                cur = None
                continue
            m = FIELD_RE.match(line)
            if m and cur is not None:
                cur["fields"][m.group(1).strip()] = m.group(2).strip()
    return reqs, errors


def parse_features(feat_dir):
    """Return {tag: [(file, scenario title)]}, a list of (file, line, tag)
    and the scenarios, as dicts: id, title, file, line, tags, top (True for
    files directly in docs/features, which pytest-bdd binds)."""
    by_tag, all_tags, scenarios = {}, [], []
    paths = glob.glob(os.path.join(feat_dir, "**", "*.feature"), recursive=True)
    for path in sorted(paths):
        fname = os.path.relpath(path, feat_dir).replace(os.sep, "/")
        feature_tags, pending = [], []
        for n, raw in enumerate(open(path, encoding="utf-8"), 1):
            line = raw.strip()
            if line.startswith("@"):
                tags = [t[1:] for t in line.split() if t.startswith("@")]
                pending += tags
                all_tags += [(fname, n, t) for t in tags]
                continue
            m = re.match(r"^(Feature|Scenario Outline|Scenario):\s*(.*)$", line)
            if m:
                if m.group(1) == "Feature":
                    feature_tags = pending
                else:
                    for t in set(pending + feature_tags):
                        by_tag.setdefault(t, []).append((fname, m.group(2)))
                    sm = SCN_RE.match(m.group(2))
                    scenarios.append({
                        "id": sm.group(1) if sm else None,
                        "title": sm.group(2) if sm else m.group(2),
                        "file": fname, "line": n, "tags": pending + feature_tags,
                        "top": "/" not in fname})
                pending = []
    return by_tag, all_tags, scenarios


def scenario_owner(sid):
    return sid.rsplit("-S", 1)[0]


RESULT_ID_RE = re.compile(r"((?:BR|STK|SYS|SUB|HW|SW|IF|CMP)(?:_[A-Z]+)?_\d+_S\d\d_T\d\d)")


def parse_results(root):
    """Read JUnit XML from tests/results/ (tests/run_all.sh writes it).
    Return {test id: {"pass": n, "fail": n, "skip": n}}; empty if none."""
    import xml.etree.ElementTree as ET
    out = {}
    for path in sorted(glob.glob(os.path.join(root, "tests", "results", "*.xml"))):
        for case in ET.parse(path).getroot().iter("testcase"):
            m = RESULT_ID_RE.search(case.get("name", ""))
            if not m:
                continue
            tid = m.group(1).replace("_", "-")
            if case.find("failure") is not None or case.find("error") is not None:
                kind = "fail"
            elif case.find("skipped") is not None or case.get("result") == "skipped":
                kind = "skip"
            else:
                kind = "pass"
            out.setdefault(tid, {"pass": 0, "fail": 0, "skip": 0})[kind] += 1
    return out


def outcome(counts):
    """One word for a set of results: failing, passing, skipped or not run."""
    if not counts or not sum(counts.values()):
        return "not run"
    if counts["fail"]:
        return "failing"
    if counts["pass"]:
        return "passing" + (" (some rows skipped)" if counts["skip"] else "")
    return "skipped"


def parse_tests(root):
    """Return {test id: [where]} from tests/gtest sources (names such as
    CMP_21_S01_T02_...) plus whether tests/bdd (pytest-bdd) exists."""
    tests = {}
    for path in sorted(glob.glob(os.path.join(root, "tests", "gtest", "**", "*.cpp"),
                                 recursive=True)):
        rel = os.path.relpath(path, root)
        for n, line in enumerate(open(path, encoding="utf-8"), 1):
            m = TEST_DEF_RE.search(line)
            if m:
                tid = m.group(1).replace("_", "-")
                tests.setdefault(tid, []).append(f"{rel}:{n}")
    return tests, os.path.isdir(os.path.join(root, "tests", "bdd"))


def check(root):
    req_dir = os.path.join(root, "docs", "requirements")
    feat_dir = os.path.join(root, "docs", "features")
    reqs, errors = parse_requirements(req_dir)
    warnings = []
    by_tag, all_tags, scenarios = parse_features(feat_dir)
    tests, has_bdd = parse_tests(root)

    children = {rid: [] for rid in reqs}
    verifiers = {rid: [] for rid in reqs}

    for rid, r in reqs.items():
        p = prefix(rid)
        f = r["fields"]
        where = f"{r['file']}:{r['line']}"
        if p == "VER":
            method = f.get("Method", "")
            if method not in METHODS:
                errors.append(f"{where}: {rid} has no single TAID method (got '{method}')")
            if not f.get("Status"):
                errors.append(f"{where}: {rid} has no status")
            targets = ids_in(f.get("Verifies"))
            if not targets:
                errors.append(f"{where}: {rid} verifies nothing")
            for t in targets:
                if t not in reqs:
                    errors.append(f"{where}: {rid} verifies unknown {t}")
                elif prefix(t) == "VER":
                    errors.append(f"{where}: {rid} verifies another VER {t}")
                else:
                    verifiers[t].append(rid)
            for t in re.findall(r"@(VER-[A-Z]+-\d+)", f.get("Evidence", "")):
                if t not in by_tag:
                    warnings.append(f"{where}: {rid} cites @{t} but no scenario carries it")
            continue
        # ordinary requirement
        expect = TYPES[p][0]
        if f.get("Type") != expect:
            errors.append(f"{where}: {rid} type is '{f.get('Type')}', expected '{expect}'")
        if not f.get("EARS"):
            errors.append(f"{where}: {rid} has no EARS pattern")
        if not f.get("Statement"):
            errors.append(f"{where}: {rid} has no statement")
        parents = ids_in(f.get("Derives from"))
        allowed = TYPES[p][1]
        if allowed and not parents:
            errors.append(f"{where}: {rid} derives from nothing")
        for par in parents:
            if par not in reqs:
                errors.append(f"{where}: {rid} derives from unknown {par}")
            elif prefix(par) not in allowed:
                errors.append(f"{where}: {rid} ({p}) may not derive from {par} "
                              f"({prefix(par)}); allowed: {', '.join(allowed)}")
            else:
                children[par].append(rid)

    for rid, r in reqs.items():
        if prefix(rid) == "VER":
            continue
        where = f"{r['file']}:{r['line']}"
        listed = ids_in(r["fields"].get("Verified by"))
        if not listed and not verifiers[rid]:
            errors.append(f"{where}: {rid} is not verified")
        for v in listed:
            if v not in reqs:
                errors.append(f"{where}: {rid} names unknown verifier {v}")
            elif rid not in ids_in(reqs[v]["fields"].get("Verifies")):
                errors.append(f"{where}: {rid} names {v}, but {v} does not list {rid}")
        for v in verifiers[rid]:
            if v not in listed:
                errors.append(f"{where}: {v} verifies {rid}, but {rid} does not name {v}")
        if prefix(rid) in NEEDS_CHILDREN and not children[rid]:
            warnings.append(f"{where}: {rid} has no derived requirement")

    # epics, features, stories
    epics_txt = open(os.path.join(root, "docs", "epics.md"), encoding="utf-8").read()
    feats_txt = open(os.path.join(root, "docs", "features.md"), encoding="utf-8").read()
    stories_txt = open(os.path.join(root, "docs", "stories.md"), encoding="utf-8").read()
    epics = set(re.findall(r"^## (EP-\d+)", epics_txt, re.M))
    feats = set(re.findall(r"^\| (F-\d+) \|", feats_txt, re.M))
    for fname, n, tag in all_tags:
        where = f"{fname}:{n}"
        if tag in ENV_TAGS:
            continue
        if re.fullmatch(r"EP-\d+", tag):
            if tag not in epics:
                errors.append(f"{where}: unknown epic tag @{tag}")
        elif re.fullmatch(r"F-\d+", tag):
            if tag not in feats:
                errors.append(f"{where}: unknown feature tag @{tag}")
        elif ID_RE.fullmatch(tag):
            if tag not in reqs:
                errors.append(f"{where}: unknown requirement tag @{tag}")
        else:
            errors.append(f"{where}: unrecognised tag @{tag}")
    for doc, txt in (("epics.md", epics_txt), ("stories.md", stories_txt)):
        for rid in sorted(set(ids_in(txt))):
            if rid not in reqs:
                errors.append(f"{doc}: refers to unknown {rid}")
    stk = {r for r in reqs if prefix(r) == "STK"}
    traced = set(re.findall(r"STK-\d+", stories_txt))
    for s in sorted(stk - traced):
        warnings.append(f"stories.md: no story traces to {s}")

    # scenarios: ID, owner tag, uniqueness; tests: every scenario has one,
    # every test names a scenario.  Top-level feature files are bound by
    # pytest-bdd, which is test T01 of each of their scenarios.
    seen = {}
    for s in scenarios:
        where = f"{s['file']}:{s['line']}"
        sid = s["id"]
        s["tests"] = []
        if not sid:
            errors.append(f"{where}: scenario has no ID ('<REQ>-Snn: title')")
            continue
        if sid in seen:
            errors.append(f"{where}: duplicate scenario ID {sid} (also {seen[sid]})")
        seen[sid] = where
        owner = scenario_owner(sid)
        if owner not in reqs:
            errors.append(f"{where}: scenario {sid} names unknown requirement {owner}")
        elif owner not in s["tags"]:
            errors.append(f"{where}: scenario {sid} is not tagged @{owner}")
        if s["top"] and has_bdd:
            s["tests"].append(f"{sid}-T01")
    by_sid = {s["id"]: s for s in scenarios if s["id"]}
    for tid, wheres in sorted(tests.items(), key=lambda kv: natkey(kv[0])):
        sid = tid.rsplit("-T", 1)[0]
        if len(wheres) > 1:
            errors.append(f"{wheres[1]}: duplicate test ID {tid} (also {wheres[0]})")
        if sid not in by_sid:
            errors.append(f"{wheres[0]}: test {tid} names unknown scenario {sid}")
            continue
        if tid.endswith("-T01") and by_sid[sid]["top"] and has_bdd:
            errors.append(f"{wheres[0]}: {tid} is reserved for the pytest-bdd binding; "
                          f"number GoogleTest tests of {sid} from T02")
            continue
        by_sid[sid]["tests"].append(tid)
    for s in scenarios:
        if s["id"] and not s["tests"]:
            errors.append(f"{s['file']}:{s['line']}: scenario {s['id']} has no test")

    return reqs, children, verifiers, by_tag, scenarios, errors, warnings


def status_word(s):
    s = (s or "").lower()
    for w in ("passed", "partial", "pending"):
        if s.startswith(w):
            return w.capitalize()
    return "?"


def source_lines(root):
    files = set()
    for pat in SOURCES:
        files.update(glob.glob(os.path.join(root, pat)))
    return sum(sum(1 for _ in open(f, encoding="utf-8", errors="replace")) for f in files), len(files)


def write_matrix(root, reqs, children, verifiers, by_tag, scenarios, errors, warnings):
    out = []
    w = out.append
    w("# Traceability matrix\n")
    w("Generated by `tools/tracecheck.py`; do not edit by hand.\n")
    w("## Summary\n")
    w("| Type | Count |")
    w("|---|---|")
    for p in ORDER:
        w(f"| {TYPES[p][0]} (`{p}`) | {sum(1 for r in reqs if prefix(r) == p)} |")
    vers = [r for r in reqs.values() if prefix(r["id"]) == "VER"]
    w("")
    w("| Verification method | Count |")
    w("|---|---|")
    for m in METHODS:
        w(f"| {m} | {sum(1 for v in vers if v['fields'].get('Method') == m)} |")
    w("")
    w("| Verification status | Count |")
    w("|---|---|")
    for s in ("Passed", "Partial", "Pending"):
        w(f"| {s} | {sum(1 for v in vers if status_word(v['fields'].get('Status')) == s)} |")
    sys_ids = [r for r in reqs if prefix(r) == "SYS"]
    covered = [r for r in sys_ids if any(
        re.search(r"QEMU|Host", reqs[v]["fields"].get("Environment", "")) for v in verifiers[r])]
    pct = 100.0 * len(covered) / len(sys_ids) if sys_ids else 0
    lines, nfiles = source_lines(root)
    w("")
    w(f"* **Emulator/host coverage (BR-05 KPI):** {len(covered)} of {len(sys_ids)} system "
      f"requirements ({pct:.0f} %) have a verification runnable in QEMU or on the host "
      f"(target ≥ 80 %).")
    w(f"* **Source size (BR-01 KPI):** {lines} lines in {nfiles} firmware, tool and build "
      f"files (target ≤ 2,500).")
    ntests = sum(len(s["tests"]) for s in scenarios)
    w(f"* **Scenarios and tests:** {len(scenarios)} scenarios "
      f"({sum(1 for s in scenarios if s['top'])} bound by pytest-bdd, "
      f"{sum(1 for s in scenarios if not s['top'])} unit-level), {ntests} test IDs "
      f"(T01 of a top-level scenario is its pytest-bdd binding; the rest are GoogleTest).")
    w("* **Test results:** see [`test-results.md`](test-results.md), written from "
      "the last `tests/run_all.sh`.")
    w(f"* **Check result:** {len(errors)} errors, {len(warnings)} warnings.\n")

    w("## Derivation tree (BR → STK → SYS)\n")
    for br in sorted((r for r in reqs if prefix(r) == "BR"), key=natkey):
        w(f"* **{br}** {reqs[br]['title']}")
        for stk in sorted(children[br], key=natkey):
            w(f"  * {stk} {reqs[stk]['title']}")
            for s in sorted(children[stk], key=natkey):
                w(f"    * {s} {reqs[s]['title']}")
    w("")

    for p in ORDER:
        ids = sorted((r for r in reqs if prefix(r) == p), key=natkey)
        if not ids:
            continue
        w(f"## {TYPES[p][0]} (`{p}`)\n")
        if p == "VER":
            w("| ID | Verifies | Method | Environment | Status | Scenarios |")
            w("|---|---|---|---|---|---|")
            for v in ids:
                f = reqs[v]["fields"]
                n = len(by_tag.get(v, []))
                w(f"| {v} | {', '.join(ids_in(f.get('Verifies')))} | {f.get('Method')} | "
                  f"{f.get('Environment', '')} | {status_word(f.get('Status'))} | {n or ''} |")
        else:
            w("| ID | Title | EARS | Derives from | Children | Verified by | Status | Scenarios |")
            w("|---|---|---|---|---|---|---|---|")
            for r in ids:
                f = reqs[r]["fields"]
                vs = sorted(set(ids_in(f.get("Verified by"))) | set(verifiers[r]), key=natkey)
                st = "/".join(sorted({status_word(reqs[v]["fields"].get("Status"))
                                      for v in vs if v in reqs}))
                feats = sorted({fn for fn, _ in by_tag.get(r, [])})
                w(f"| {r} | {reqs[r]['title']} | {f.get('EARS', '')} | "
                  f"{', '.join(ids_in(f.get('Derives from'))) or '—'} | "
                  f"{', '.join(sorted(children[r], key=natkey)) or '—'} | "
                  f"{', '.join(vs)} | {st} | {', '.join(feats)} |")
        w("")
    w("## Scenarios and tests\n")
    w("The scenario ID's prefix is the requirement it is filed under, and so its level.\n")
    w("| Scenario | Level | File | Environment | Tests |")
    w("|---|---|---|---|---|")
    for s in sorted(scenarios, key=lambda s: natkey(s["id"] or "")):
        sid = s["id"] or "(no ID)"
        lvl = TYPES.get(prefix(sid), ("?",))[0]
        env = " ".join(t for t in ("host", "qemu", "hardware", "pending") if t in s["tags"])
        w(f"| {sid} | {lvl} | {s['file']}:{s['line']} | {env} | "
          f"{', '.join(sorted(s['tests'], key=natkey)) or '—'} |")
    w("")
    if warnings:
        w("## Warnings\n")
        for x in warnings:
            w(f"* {x}")
        w("")
    path = os.path.join(root, "docs", "traceability.md")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(out))
    return path


def write_results(root, reqs, scenarios):
    """docs/test-results.md: the outcome of every scenario and requirement
    in the last run (tests/results/*.xml).  Kept apart from the matrix so
    that the matrix depends only on the documents and the test names."""
    results = parse_results(root)
    if not results:
        return None
    for sc in scenarios:
        tot = {"pass": 0, "fail": 0, "skip": 0}
        for t in sc["tests"]:
            for k, v in results.get(t, {}).items():
                tot[k] += v
        sc["counts"], sc["outcome"] = tot, outcome(tot)
    out = []
    w = out.append
    w("# Test results\n")
    w("Generated by `tools/tracecheck.py` from `tests/results/*.xml`, which "
      "`tests/run_all.sh` writes. Skipped means the environment lacked QEMU, a board "
      "or the cross compiler.\n")
    tally = {}
    for sc in scenarios:
        word = sc["outcome"].split(" (")[0]
        tally[word] = tally.get(word, 0) + 1
    w("| Scenarios | Count |")
    w("|---|---|")
    for k in ("passing", "failing", "skipped", "not run"):
        w(f"| {k} | {tally.get(k, 0)} |")
    w("")
    w("## Requirements by scenario outcome\n")
    w("A requirement is listed under the outcomes of the scenarios tagged with it.\n")
    w("| Requirement | Passing | Failing | Skipped |")
    w("|---|---|---|---|")
    for r in sorted((r for r in reqs if prefix(r) != "VER"), key=natkey):
        tagged = [sc for sc in scenarios if r in sc["tags"]]
        if not tagged:
            continue
        cell = lambda word: ", ".join(sc["id"] for sc in tagged
                                      if sc["outcome"].startswith(word)) or "—"
        w(f"| {r} | {cell('passing')} | {cell('failing')} | {cell('skipped')} |")
    w("")
    w("## Scenarios\n")
    w("| Scenario | Environment | Tests | Passed | Failed | Skipped | Outcome |")
    w("|---|---|---|---|---|---|---|")
    for sc in sorted(scenarios, key=lambda s: natkey(s["id"] or "")):
        env = " ".join(t for t in ("host", "qemu", "hardware", "pending") if t in sc["tags"])
        c = sc["counts"]
        w(f"| {sc['id']} | {env} | {', '.join(sorted(sc['tests'], key=natkey))} | "
          f"{c['pass']} | {c['fail']} | {c['skip']} | {sc['outcome']} |")
    w("")
    path = os.path.join(root, "docs", "test-results.md")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(out))
    return path


def natkey(rid):
    return [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", rid)]


def self_test():
    """Build small fixture trees, one per error class, and expect detection."""
    base_reqs = {
        "BR.md": "### BR-01 — b\n- **Type:** Business\n- **EARS:** Ubiquitous\n"
                 "- **Statement:** s\n- **Derives from:** —\n- **Verified by:** VER-BR-01\n",
        "STK.md": "### STK-01 — k\n- **Type:** Stakeholder\n- **EARS:** Ubiquitous\n"
                  "- **Statement:** s\n- **Derives from:** BR-01\n- **Verified by:** VER-STK-01\n",
        "VER.md": "### VER-BR-01 — v\n- **Type:** Verification\n- **Verifies:** BR-01\n"
                  "- **Method:** Analysis\n- **Environment:** Host\n- **Status:** Passed\n\n"
                  "### VER-STK-01 — v\n- **Type:** Verification\n- **Verifies:** STK-01\n"
                  "- **Method:** Test\n- **Environment:** Host\n- **Status:** Passed\n",
    }
    base_feat = ("@EP-01 @F-01\nFeature: f\n  @host @STK-01 @VER-STK-01\n"
                 "  Scenario: STK-01-S01: s\n")
    unit_feat = "Feature: u\n  @host @STK-01 @VER-STK-01\n  Scenario: STK-01-S02: u\n"
    unit_test = "TEST(U, STK_01_S02_T01_u) {}\n"
    cases = {
        "clean": ({}, None, None),
        "duplicate ID": ({"BR.md": base_reqs["BR.md"] * 2}, None, "duplicate ID"),
        "unknown parent": ({"STK.md": base_reqs["STK.md"].replace("BR-01\n-", "BR-09\n-")},
                           None, "derives from unknown"),
        "wrong level": ({"STK.md": base_reqs["STK.md"].replace("Derives from:** BR-01",
                                                               "Derives from:** STK-01")},
                        None, "may not derive"),
        "unverified": ({"STK.md": base_reqs["STK.md"].replace("- **Verified by:** VER-STK-01\n", ""),
                        "VER.md": base_reqs["VER.md"].split("\n\n")[0] + "\n"},
                       None, "is not verified"),
        "no method": ({"VER.md": base_reqs["VER.md"].replace("Method:** Test", "Method:** Guess")},
                      None, "no single TAID method"),
        "unknown tag": ({}, base_feat.replace("@STK-01", "@SYS-77"), "unknown requirement tag"),
        "scenario without ID": ({}, base_feat.replace("STK-01-S01: ", ""), "scenario has no ID"),
        "scenario not tagged with its owner": ({}, base_feat.replace("STK-01-S01", "BR-01-S01"),
                                               "is not tagged"),
        "unit scenario without test": ({}, None, "has no test", {"unit_test": ""}),
        "test for unknown scenario": ({}, None, "names unknown scenario",
                                      {"unit_test": unit_test + "TEST(U, STK_01_S09_T01_x) {}\n"}),
        "T01 reused by GoogleTest": ({}, None, "reserved for the pytest-bdd binding",
                                     {"unit_test": unit_test + "TEST(U, STK_01_S01_T01_x) {}\n"}),
    }
    ok = True
    for name, case in cases.items():
        override, feat, expect = case[:3]
        extra = dict({"unit_test": unit_test}, **(case[3] if len(case) > 3 else {}))
        with tempfile.TemporaryDirectory() as d:
            os.makedirs(os.path.join(d, "docs", "requirements"))
            os.makedirs(os.path.join(d, "docs", "features", "unit"))
            os.makedirs(os.path.join(d, "tests", "bdd"))
            os.makedirs(os.path.join(d, "tests", "gtest"))
            files = dict(base_reqs, **override)
            for fn, txt in files.items():
                open(os.path.join(d, "docs", "requirements", fn), "w").write(txt)
            open(os.path.join(d, "docs", "features", "f.feature"), "w").write(feat or base_feat)
            open(os.path.join(d, "docs", "features", "unit", "u.feature"), "w").write(unit_feat)
            open(os.path.join(d, "tests", "gtest", "t.cpp"), "w").write(extra["unit_test"])
            open(os.path.join(d, "docs", "epics.md"), "w").write("## EP-01 — e\n")
            open(os.path.join(d, "docs", "features.md"), "w").write("| F-01 | f |\n")
            open(os.path.join(d, "docs", "stories.md"), "w").write("Traces to: STK-01\n")
            errs = check(d)[5]
            if expect is None:
                good = not errs
            else:
                good = any(expect in e for e in errs)
            print(f"  {'ok ' if good else 'BAD'} {name}" + ("" if good else f": {errs}"))
            ok &= good
    print("self-test: all error classes detected" if ok else "self-test: FAILED")
    return 0 if ok else 1


def main(argv):
    if "--self-test" in argv:
        return self_test()
    reqs, children, verifiers, by_tag, scenarios, errors, warnings = check(ROOT)
    for e in errors:
        print("error:", e)
    for x in warnings:
        print("warning:", x)
    if "--check" not in argv:
        print("wrote", os.path.relpath(write_matrix(ROOT, reqs, children, verifiers, by_tag,
                                                    scenarios, errors, warnings), ROOT))
        res = write_results(ROOT, reqs, scenarios)
        if res:
            print("wrote", os.path.relpath(res, ROOT))
    print(f"{len(reqs)} entries, {len(errors)} errors, {len(warnings)} warnings")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
