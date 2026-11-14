#!/usr/bin/env python3
"""
tracecheck.py -- check e32's requirement traceability and write the matrix.

    python3 tools/tracecheck.py              check, then write docs/traceability.md
    python3 tools/tracecheck.py --check      check only
    python3 tools/tracecheck.py --self-test  prove every error class is detected

Inputs:  docs/requirements/*.md   ("### ID — title" + "- **Field:** value")
         docs/features/*.feature  (Gherkin tags)
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
    """Return {tag: [(file, scenario title)]} and a list of (file, line, tag)."""
    by_tag, all_tags = {}, []
    for path in sorted(glob.glob(os.path.join(feat_dir, "*.feature"))):
        fname = os.path.basename(path)
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
                pending = []
    return by_tag, all_tags


def check(root):
    req_dir = os.path.join(root, "docs", "requirements")
    feat_dir = os.path.join(root, "docs", "features")
    reqs, errors = parse_requirements(req_dir)
    warnings = []
    by_tag, all_tags = parse_features(feat_dir)

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

    return reqs, children, verifiers, by_tag, errors, warnings


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


def write_matrix(root, reqs, children, verifiers, by_tag, errors, warnings):
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
    if warnings:
        w("## Warnings\n")
        for x in warnings:
            w(f"* {x}")
        w("")
    path = os.path.join(root, "docs", "traceability.md")
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
    base_feat = "@EP-01 @F-01\nFeature: f\n  @host @STK-01 @VER-STK-01\n  Scenario: s\n"
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
    }
    ok = True
    for name, (override, feat, expect) in cases.items():
        with tempfile.TemporaryDirectory() as d:
            os.makedirs(os.path.join(d, "docs", "requirements"))
            os.makedirs(os.path.join(d, "docs", "features"))
            files = dict(base_reqs, **override)
            for fn, txt in files.items():
                open(os.path.join(d, "docs", "requirements", fn), "w").write(txt)
            open(os.path.join(d, "docs", "features", "f.feature"), "w").write(feat or base_feat)
            open(os.path.join(d, "docs", "epics.md"), "w").write("## EP-01 — e\n")
            open(os.path.join(d, "docs", "features.md"), "w").write("| F-01 | f |\n")
            open(os.path.join(d, "docs", "stories.md"), "w").write("Traces to: STK-01\n")
            errs = check(d)[4]
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
    reqs, children, verifiers, by_tag, errors, warnings = check(ROOT)
    for e in errors:
        print("error:", e)
    for x in warnings:
        print("warning:", x)
    if "--check" not in argv:
        print("wrote", os.path.relpath(write_matrix(ROOT, reqs, children, verifiers,
                                                    by_tag, errors, warnings), ROOT))
    print(f"{len(reqs)} entries, {len(errors)} errors, {len(warnings)} warnings")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
