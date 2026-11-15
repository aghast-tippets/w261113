#!/usr/bin/env python3
"""
tracecheck.py -- check e32's traceability (BDD framework v2.0, see
docs/bdd-framework.md) and write the ledger and the work view.

    python3 tools/tracecheck.py                  check, then write docs/traceability.md
                                                 (ledger) and docs/backlog.md (work view)
    python3 tools/tracecheck.py --check          check only
    python3 tools/tracecheck.py --strict         also fail on coverage gaps (a Test-verified
                                                 requirement with no Rule, a Rule with no
                                                 scenario); use for the Phase 6 sign-off
    python3 tools/tracecheck.py --record-status  write story and epic status changes (Done,
                                                 reopened) into docs/stories.md and
                                                 docs/epics.md, then regenerate
    python3 tools/tracecheck.py --self-test      prove every error class is detected

Inputs (records): docs/actors.md, docs/epics.md, docs/stories.md,
    docs/requirements/*.md ("### ID — title" + "- **Field:** value"),
    docs/features/<level>/*.feature (Feature: FEAT-nnn ⊃ Rule: <REQ> ⊃ Scenario: <REQ>-Snn)
Inputs (tests): tests/gtest/**/*.cpp (TEST names <REQ>_Snn_Tnn_...); tests/bdd/ (if present,
    pytest-bdd binds every scenario not tagged @gtest as its test T01);
    tests/results/*.xml (JUnit results, written by tests/run_all.sh)
Exit status is 1 if any error is found.  Python 3 standard library only.
"""
import datetime
import glob
import os
import re
import sys
import tempfile
import xml.etree.ElementTree as ET

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
PRIORITIES = ("Must", "Should", "Could")
ACTOR_TYPES = ("Primary", "Supporting", "Offstage")
# feature folder -> requirement prefixes whose Rules it may hold
LEVEL_DIRS = {"acceptance": ("BR", "STK"), "system": ("SYS",), "subsystem": ("SUB",),
              "hardware": ("HW",), "software": ("SW",), "interface": ("IF",),
              "unit": ("CMP",)}
NARRATIVE_LEVELS = ("acceptance", "system")
ENV_TAGS = {"host", "qemu", "hardware", "pending", "gtest"}
STATUS = {"proposed": "💡 Proposed", "open": "⏳ Open", "done": "✅ Done",
          "retired": "⛔ RETIRED"}
ID_RE = re.compile(r"\b(?:BR|STK|SYS|SUB|HW|SW|IF|CMP|VER)(?:-[A-Z]+)?-\d+\b")
HEAD_RE = re.compile(r"^### ((?:BR|STK|SYS|SUB|HW|SW|IF|CMP|VER)(?:-[A-Z]+)?-\d+) — (.+)$")
FIELD_RE = re.compile(r"^- \*\*([A-Za-z ]+):\*\* ?(.*)$")
SCN_RE = re.compile(r"^((?:BR|STK|SYS|SUB|HW|SW|IF|CMP)(?:-[A-Z]+)?-\d+-S\d\d): (.+)$")
RULE_RE = re.compile(r"^((?:BR|STK|SYS|SUB|HW|SW|IF|CMP)(?:-[A-Z]+)?-\d+): (.+)$")
TEST_DEF_RE = re.compile(r"\bTEST(?:_F|_P)?\(\s*\w+\s*,\s*("
                         r"(?:BR|STK|SYS|SUB|HW|SW|IF|CMP)(?:_[A-Z]+)?_\d+_S\d\d_T\d\d)")
RESULT_ID_RE = re.compile(r"((?:BR|STK|SYS|SUB|HW|SW|IF|CMP)(?:_[A-Z]+)?_\d+_S\d\d_T\d\d)")
SOURCES = ["*.c", "*.S", "*.lds", "include/*.h", "tools/mkimage.c",
           "tools/build-toolchain.sh", "Makefile"]


def prefix(rid):
    return rid.split("-")[0]


def ids_in(text):
    return ID_RE.findall(text or "")


def natkey(rid):
    return [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", rid or "")]


def norm(text):
    return " ".join((text or "").split())


def status_key(text):
    t = (text or "").lower()
    for k in STATUS:
        if k in t:
            return k
    return None


# ------------------------------------------------------------------ records

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
            elif cur is not None and line.startswith("  ") and line.strip() and cur["fields"]:
                last = list(cur["fields"])[-1]   # e.g. a numbered list in a Statement
                cur["fields"][last] += "\n" + line.strip()
    return reqs, errors


def record_fields(lines):
    """'- **A:** x · **B:** y' lines (+ indented continuations) -> {label: value}."""
    fields, last = {}, None
    for ln in lines:
        if ln.startswith("- **"):
            for m in re.finditer(r"\*\*([^*]+?):\*\* ?(.*?)(?= · \*\*[^*]+?:\*\*|$)", ln[2:]):
                last = m.group(1).strip()
                fields[last] = m.group(2).strip()
        elif last and ln.startswith("  ") and ln.strip():
            fields[last] += "\n" + ln.strip()
    return fields


def parse_sections(path, head_re):
    """Sections '## <ID> — title' of a record file, plus its Index table rows."""
    items, index, errors = {}, {}, []
    if not os.path.exists(path):
        return items, index, [f"{os.path.basename(path)}: missing"]
    text = open(path, encoding="utf-8").read().split("\n")
    cur, start = None, 0
    for n, line in enumerate(text, 1):
        m = re.match(r"^## (" + head_re + r") — (.+)$", line)
        if m or line.startswith("## "):
            if cur:
                cur["fields"] = record_fields(text[start:n - 1])
            cur = None
        if m:
            if m.group(1) in items:
                errors.append(f"{os.path.basename(path)}:{n}: duplicate ID {m.group(1)}")
            cur = {"id": m.group(1), "title": m.group(2).strip(), "line": n}
            items[m.group(1)] = cur
            start = n
        row = re.match(r"^\| (" + head_re + r") \|(.*)\|\s*$", line)
        if row:
            index[row.group(1)] = [c.strip() for c in row.group(2).split("|")]
    if cur:
        cur["fields"] = record_fields(text[start:])
    return items, index, errors


def parse_actors(path):
    actors, errors = {}, []
    if not os.path.exists(path):
        return actors, [f"{os.path.basename(path)}: missing"]
    retired = False
    for n, line in enumerate(open(path, encoding="utf-8"), 1):
        if line.startswith("## Retired"):
            retired = True
        m = re.match(r"^\| (ACT-[A-Z]*\d+) \| ([^|]*)\|(.*)\|\s*$", line)
        if not m:
            continue
        cells = [c.strip() for c in m.group(3).split("|")]
        if retired:
            if m.group(1) in actors:
                actors[m.group(1)]["retired"] = True
            continue
        if m.group(1) in actors:
            errors.append(f"actors.md:{n}: duplicate ID {m.group(1)}")
        actors[m.group(1)] = {"id": m.group(1), "name": m.group(2).strip(), "line": n,
                              "type": cells[0] if cells else "",
                              "personas": re.findall(r'"([^"]+)"', cells[-1] if cells else ""),
                              "retired": False}
    return actors, errors


def parse_features(feat_dir):
    """Features (with Rules and Scenarios), all tags as (file, line, tag)."""
    features, all_tags = [], []
    for path in sorted(glob.glob(os.path.join(feat_dir, "**", "*.feature"), recursive=True)):
        rel = os.path.relpath(path, feat_dir).replace(os.sep, "/")
        f = {"file": rel, "level": rel.split("/")[0] if "/" in rel else None, "id": None,
             "title": "", "tags": [], "desc": [], "rules": [], "orphans": [], "line": 1}
        pending, mode, rule, in_doc = [], None, None, False
        for n, raw in enumerate(open(path, encoding="utf-8"), 1):
            s = raw.strip()
            if s.startswith('"""') or s.startswith("```"):
                in_doc = not in_doc
                continue
            if in_doc or s.startswith("#"):
                continue
            if s.startswith("@"):
                tags = [t[1:] for t in s.split() if t.startswith("@")]
                pending += tags
                all_tags += [(rel, n, t) for t in tags]
                continue
            kw = re.match(r"^(Feature|Background|Rule|Scenario Outline|Scenario Template|"
                          r"Scenario|Example|Examples|Scenarios):\s*(.*)$", s)
            if kw:
                word, rest = kw.groups()
                if word == "Feature":
                    m = re.match(r"^(FEAT-\d+): (.+)$", rest)
                    f.update(id=m.group(1) if m else None, title=m.group(2) if m else rest,
                             tags=pending, line=n)
                    mode = "fdesc"
                elif word == "Rule":
                    m = RULE_RE.match(rest)
                    rule = {"id": m.group(1) if m else None, "title": m.group(2) if m else rest,
                            "tags": pending, "line": n, "desc": [], "scenarios": [],
                            "file": rel}
                    f["rules"].append(rule)
                    mode = "rdesc"
                elif word in ("Scenario", "Scenario Outline", "Scenario Template", "Example"):
                    m = SCN_RE.match(rest)
                    sc = {"id": m.group(1) if m else None, "title": m.group(2) if m else rest,
                          "tags": pending, "line": n, "file": rel, "rule": rule}
                    (rule["scenarios"] if rule else f["orphans"]).append(sc)
                    mode = "steps"
                else:
                    mode = "other"
                pending = []
                continue
            if mode == "fdesc":
                f["desc"].append(s)
            elif mode == "rdesc":
                rule["desc"].append(s)
        features.append(f)
    return features, all_tags


def parse_tests(root):
    tests = {}
    for path in sorted(glob.glob(os.path.join(root, "tests", "gtest", "**", "*.cpp"),
                                 recursive=True)):
        rel = os.path.relpath(path, root)
        for n, line in enumerate(open(path, encoding="utf-8"), 1):
            m = TEST_DEF_RE.search(line)
            if m:
                tests.setdefault(m.group(1).replace("_", "-"), []).append(f"{rel}:{n}")
    return tests, os.path.isdir(os.path.join(root, "tests", "bdd"))


def parse_results(root):
    """tests/results/*.xml -> {test id: {"pass": n, "fail": n, "skip": n}}."""
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


# -------------------------------------------------------------------- model

class Model:
    pass


def load(root):
    d = Model()
    docs = os.path.join(root, "docs")
    d.root = root
    d.errors, d.warnings, d.gaps = [], [], []
    d.reqs, errs = parse_requirements(os.path.join(docs, "requirements"))
    d.errors += errs
    d.actors, errs = parse_actors(os.path.join(docs, "actors.md"))
    d.errors += errs
    d.epics, d.epic_index, errs = parse_sections(os.path.join(docs, "epics.md"), r"EP-\d+")
    d.errors += errs
    d.stories, d.story_index, errs = parse_sections(os.path.join(docs, "stories.md"), r"US-\d+")
    d.errors += errs
    d.features, d.all_tags = parse_features(os.path.join(docs, "features"))
    d.tests, d.has_bdd = parse_tests(root)
    d.results = parse_results(root)
    d.rules = {}
    d.scenarios = []
    for f in d.features:
        for r in f["rules"]:
            r["feature"] = f
            for sc in r["scenarios"]:
                sc["feature"] = f
                d.scenarios.append(sc)
        for sc in f["orphans"]:
            sc["feature"] = f
            d.scenarios.append(sc)
    return d


def vers_of(d, r):
    return sorted(set(ids_in(d.reqs[r]["fields"].get("Verified by"))) | set(d.verifiers[r]),
                  key=natkey)


def test_verified(d, r):
    return any(d.reqs[v]["fields"].get("Method") == "Test" for v in vers_of(d, r)
               if v in d.reqs)


def check(root):
    d = load(root)
    reqs, E, W = d.reqs, d.errors, d.warnings
    d.children = {rid: [] for rid in reqs}
    d.verifiers = {rid: [] for rid in reqs}

    # --- requirements (as in v1, plus Priority, Rationale, Story)
    for rid, r in reqs.items():
        p, f = prefix(rid), r["fields"]
        where = f"{r['file']}:{r['line']}"
        if p == "VER":
            method = f.get("Method", "")
            if method not in METHODS:
                E.append(f"{where}: {rid} has no single TAID method (got '{method}')")
            if not f.get("Status"):
                E.append(f"{where}: {rid} has no status")
            targets = ids_in(f.get("Verifies"))
            if not targets:
                E.append(f"{where}: {rid} verifies nothing")
            for t in targets:
                if t not in reqs:
                    E.append(f"{where}: {rid} verifies unknown {t}")
                elif prefix(t) == "VER":
                    E.append(f"{where}: {rid} verifies another VER {t}")
                else:
                    d.verifiers[t].append(rid)
            continue
        if f.get("Type") != TYPES[p][0]:
            E.append(f"{where}: {rid} type is '{f.get('Type')}', expected '{TYPES[p][0]}'")
        for field in ("EARS", "Statement", "Rationale"):
            if not f.get(field):
                E.append(f"{where}: {rid} has no {field.lower()}")
        if f.get("Priority") not in PRIORITIES:
            E.append(f"{where}: {rid} has no priority (Must/Should/Could)")
        parents = ids_in(f.get("Derives from"))
        allowed = TYPES[p][1]
        if allowed and not parents:
            E.append(f"{where}: {rid} derives from nothing")
        for par in parents:
            if par not in reqs:
                E.append(f"{where}: {rid} derives from unknown {par}")
            elif prefix(par) not in allowed:
                E.append(f"{where}: {rid} ({p}) may not derive from {par} "
                         f"({prefix(par)}); allowed: {', '.join(allowed)}")
            else:
                d.children[par].append(rid)
        for us in re.findall(r"US-\d+", f.get("Story", "")):
            if us not in d.stories:
                E.append(f"{where}: {rid} refines unknown story {us}")
    for rid, r in reqs.items():
        if prefix(rid) == "VER":
            continue
        where = f"{r['file']}:{r['line']}"
        listed = ids_in(r["fields"].get("Verified by"))
        if not listed and not d.verifiers[rid]:
            E.append(f"{where}: {rid} is not verified")
        for v in listed:
            if v not in reqs:
                E.append(f"{where}: {rid} names unknown verifier {v}")
            elif rid not in ids_in(reqs[v]["fields"].get("Verifies")):
                E.append(f"{where}: {rid} names {v}, but {v} does not list {rid}")
        for v in d.verifiers[rid]:
            if v not in listed:
                E.append(f"{where}: {v} verifies {rid}, but {rid} does not name {v}")
        if prefix(rid) in NEEDS_CHILDREN and not d.children[rid]:
            W.append(f"{where}: {rid} has no derived requirement")

    # --- actors
    for a in d.actors.values():
        if a["type"] not in ACTOR_TYPES:
            E.append(f"actors.md:{a['line']}: {a['id']} type '{a['type']}' is not "
                     f"{'/'.join(ACTOR_TYPES)}")
        if a["type"] == "Primary" and not a["personas"]:
            E.append(f"actors.md:{a['line']}: Primary actor {a['id']} has no persona")

    # --- epics and stories
    d.refiners = {s: sorted([r for r in reqs if s in re.findall(r"US-\d+",
                                                                reqs[r]["fields"].get("Story", ""))],
                            key=natkey) for s in d.stories}
    feat_ids = {f["id"] for f in d.features}
    for e in d.epics.values():
        f, where = e["fields"], f"epics.md:{e['line']}"
        e["realises"] = ids_in(f.get("Realises"))
        e["listed"] = re.findall(r"US-\d+", f.get("Stories", ""))
        e["status"] = status_key(f.get("Status"))
        for br in e["realises"]:
            if br not in reqs or prefix(br) != "BR":
                E.append(f"{where}: {e['id']} realises {br}, which is not a business requirement")
        if not e["realises"]:
            E.append(f"{where}: {e['id']} realises no business requirement")
        if e["status"] is None:
            E.append(f"{where}: {e['id']} has no status")
        if f.get("Priority") not in PRIORITIES:
            E.append(f"{where}: {e['id']} has no priority")
        m = re.search(r"\((\d+) of (\d+) Done\)", f.get("Stories", ""))
        n_done = sum(1 for u in e["listed"] if u in d.stories and
                     status_key(d.stories[u]["fields"].get("Status")) == "done")
        if m and (int(m.group(1)), int(m.group(2))) != (n_done, len(e["listed"])):
            E.append(f"{where}: {e['id']} says {m.group(0)}, but {n_done} of "
                     f"{len(e['listed'])} of its stories are recorded Done; run "
                     f"tracecheck.py --record-status")
        row = d.epic_index.get(e["id"])
        if not row or status_key(row[-1]) != e["status"]:
            E.append(f"{where}: {e['id']} index row disagrees with its section (status)")
    for s in d.stories.values():
        f, where = s["fields"], f"stories.md:{s['line']}"
        s["epic"] = (re.findall(r"EP-\d+", f.get("Epic", "")) or [None])[0]
        s["actor"] = (re.findall(r"ACT-[A-Z]*\d+", f.get("Actor", "")) or [None])[0]
        s["status"] = status_key(f.get("Status"))
        s["narrative"] = norm(f.get("Story"))
        s["ac"] = []
        for item in re.split(r"\n(?=\d+\. )", f.get("Acceptance criteria → requirements", "")):
            if item.strip():
                s["ac"].append(ids_in(item.rsplit("→", 1)[-1]) if "→" in item else [])
        if s["epic"] not in d.epics:
            E.append(f"{where}: {s['id']} belongs to unknown epic {s['epic']}")
        elif s["id"] not in d.epics[s["epic"]]["listed"]:
            E.append(f"{where}: {s['id']} is in {s['epic']}, but epics.md does not list it there")
        if s["actor"] not in d.actors:
            E.append(f"{where}: {s['id']} names unknown actor {s['actor']}")
        if f.get("Priority") not in PRIORITIES:
            E.append(f"{where}: {s['id']} has no priority")
        if s["status"] is None:
            E.append(f"{where}: {s['id']} has no status")
        if not s["narrative"].startswith("As "):
            E.append(f"{where}: {s['id']} has no 'As a …, I want …, so that …' narrative")
        if not s["ac"] or any(not ids for ids in s["ac"]):
            E.append(f"{where}: {s['id']} has an acceptance criterion with no requirement")
        for ids in s["ac"]:
            for r in ids:
                if r not in reqs:
                    E.append(f"{where}: {s['id']} criterion names unknown {r}")
        refined = ids_in(f.get("Refined by"))
        if not d.refiners[s["id"]]:
            E.append(f"{where}: {s['id']} is refined by no requirement (no Story field names it)")
        for r in refined:
            if r not in d.refiners[s["id"]]:
                E.append(f"{where}: {s['id']} lists {r} as refining it, but {r} names no such story")
        for fid in re.findall(r"FEAT-\d+", f.get("Feature(s)", "")):
            if fid not in feat_ids:
                E.append(f"{where}: {s['id']} names unknown feature {fid}")
        if s["status"] == "done" and not norm(f.get("Completion record")).strip("— "):
            E.append(f"{where}: {s['id']} is Done but has no completion record")
        row = d.story_index.get(s["id"])
        if not row or status_key(row[-1]) != s["status"] or s["epic"] not in row \
                or s["actor"] not in row:
            E.append(f"{where}: {s['id']} index row disagrees with its section")
    for e in d.epics.values():
        for us in e["listed"]:
            if us not in d.stories:
                E.append(f"epics.md:{e['line']}: {e['id']} lists unknown story {us}")
            elif d.stories[us]["epic"] != e["id"]:
                E.append(f"epics.md:{e['line']}: {e['id']} lists {us}, which stories.md files "
                         f"under {d.stories[us]['epic']}")
        if not e["listed"]:
            E.append(f"epics.md:{e['line']}: {e['id']} has no story")
        if e["status"] == "done" and not norm(e["fields"].get("Completion record")).strip("— "):
            E.append(f"epics.md:{e['line']}: {e['id']} is Done but has no completion record")
    for br in [r for r in reqs if prefix(r) == "BR"]:
        if not any(br in e["realises"] for e in d.epics.values()):
            E.append(f"{reqs[br]['file']}:{reqs[br]['line']}: {br} is realised by no epic")
    for a in d.actors.values():
        if a["type"] == "Primary" and not a["retired"] and \
                not any(s["actor"] == a["id"] for s in d.stories.values()):
            E.append(f"actors.md:{a['line']}: Primary actor {a['id']} appears in no story")

    # --- features, rules, scenarios
    seen_feat, rule_of = {}, {}
    for f in d.features:
        where = f"features/{f['file']}:{f['line']}"
        if not f["id"]:
            E.append(f"{where}: feature title is not 'FEAT-nnn: <capability>'")
        elif f["id"] in seen_feat:
            E.append(f"{where}: duplicate feature ID {f['id']} (also {seen_feat[f['id']]})")
        else:
            seen_feat[f["id"]] = where
        if f["id"] and f["id"] not in f["tags"]:
            E.append(f"{where}: {f['id']} is not tagged @{f['id']}")
        eps = [t for t in f["tags"] if re.fullmatch(r"EP-\d+", t)]
        f["epic"] = eps[0] if len(eps) == 1 else None
        if len(eps) != 1:
            E.append(f"{where}: a feature belongs to exactly one epic (tags: {eps})")
        if f["level"] not in LEVEL_DIRS:
            E.append(f"{where}: feature is not in a level folder "
                     f"({', '.join(LEVEL_DIRS)})")
        for sc in f["orphans"]:
            E.append(f"features/{sc['file']}:{sc['line']}: scenario {sc['id']} sits outside a Rule")
        # narrative: system/acceptance features repeat the stories word for word
        desc, cur = f["desc"], None
        f["narr"], f["supports"] = {}, []
        for ln in desc + [""]:
            m = re.match(r"^(US-\d+)\s{2,}(.*)$", ln)
            if m:
                cur = m.group(1)
                f["narr"][cur] = m.group(2)
            elif cur and ln and not re.match(r"^(Actors|Supports|Epic|User stories)\b", ln):
                f["narr"][cur] += " " + ln
            else:
                cur = None
            m = re.match(r"^Supports: (US-\d+) via (.*)$", ln)
            if m:
                f["supports"].append(m.group(1))
        for us, text in f["narr"].items():
            if us not in d.stories:
                E.append(f"{where}: narrative of unknown story {us}")
            elif norm(text) != d.stories[us]["narrative"]:
                E.append(f"{where}: narrative of {us} differs from stories.md")
        for us in f["supports"]:
            if us not in d.stories:
                E.append(f"{where}: supports unknown story {us}")
        if f["level"] in NARRATIVE_LEVELS and f["supports"]:
            E.append(f"{where}: a {f['level']} feature repeats story narratives, not 'Supports:'")
        for r in f["rules"]:
            rwhere = f"features/{r['file']}:{r['line']}"
            rid = r["id"]
            if not rid or rid not in reqs or prefix(rid) == "VER":
                E.append(f"{rwhere}: Rule is not titled with a known requirement ID")
                continue
            if rid in rule_of:
                E.append(f"{rwhere}: {rid} is already a Rule in {rule_of[rid]}")
            rule_of[rid] = rwhere
            if rid not in r["tags"]:
                E.append(f"{rwhere}: Rule {rid} is not tagged @{rid}")
            if f["level"] in LEVEL_DIRS and prefix(rid) not in LEVEL_DIRS[f["level"]]:
                E.append(f"{rwhere}: Rule {rid} ({TYPES[prefix(rid)][0]}) is in a "
                         f"{f['level']} feature")
            ears = norm(" ".join(r["desc"]))
            if not ears.startswith("EARS: ") or \
                    ears[6:] != norm(reqs[rid]["fields"].get("Statement", "")):
                E.append(f"{rwhere}: Rule {rid}'s EARS line differs from its requirement")
            for sc in r["scenarios"]:
                if sc["id"] and sc["id"].rsplit("-S", 1)[0] != rid:
                    E.append(f"features/{sc['file']}:{sc['line']}: scenario {sc['id']} is under "
                             f"Rule {rid}")
    d.rule_of = {r["id"]: r for f in d.features for r in f["rules"] if r["id"] in reqs}

    # --- tags
    epics, stories = set(d.epics), set(d.stories)
    for fname, n, tag in d.all_tags:
        where = f"features/{fname}:{n}"
        if tag in ENV_TAGS:
            continue
        if re.fullmatch(r"EP-\d+", tag):
            if tag not in epics:
                E.append(f"{where}: unknown epic tag @{tag}")
        elif re.fullmatch(r"FEAT-\d+", tag):
            if tag not in seen_feat:
                E.append(f"{where}: unknown feature tag @{tag}")
        elif re.fullmatch(r"US-\d+", tag):
            if tag not in stories:
                E.append(f"{where}: unknown story tag @{tag}")
        elif ID_RE.fullmatch(tag):
            if tag not in reqs:
                E.append(f"{where}: unknown requirement tag @{tag}")
        else:
            E.append(f"{where}: unrecognised tag @{tag}")

    # --- scenarios and tests
    seen = {}
    for sc in d.scenarios:
        where = f"features/{sc['file']}:{sc['line']}"
        sc["tests"] = []
        if not sc["id"]:
            E.append(f"{where}: scenario has no ID ('<REQ>-Snn: title')")
            continue
        if sc["id"] in seen:
            E.append(f"{where}: duplicate scenario ID {sc['id']} (also {seen[sc['id']]})")
        seen[sc["id"]] = where
        sc["gtest"] = "gtest" in sc["tags"]
        if d.has_bdd and not sc["gtest"]:
            sc["tests"].append(f"{sc['id']}-T01")
    by_sid = {sc["id"]: sc for sc in d.scenarios if sc["id"]}
    for tid, wheres in sorted(d.tests.items(), key=lambda kv: natkey(kv[0])):
        sid = tid.rsplit("-T", 1)[0]
        if len(wheres) > 1:
            E.append(f"{wheres[1]}: duplicate test ID {tid} (also {wheres[0]})")
        if sid not in by_sid:
            E.append(f"{wheres[0]}: test {tid} names unknown scenario {sid}")
            continue
        if tid.endswith("-T01") and d.has_bdd and not by_sid[sid]["gtest"]:
            E.append(f"{wheres[0]}: {tid} is reserved for the pytest-bdd binding; "
                     f"number GoogleTest tests of {sid} from T02, or tag it @gtest")
            continue
        by_sid[sid]["tests"].append(tid)
    for sc in d.scenarios:
        if sc["id"] and not sc["tests"]:
            E.append(f"features/{sc['file']}:{sc['line']}: scenario {sc['id']} has no test")

    # --- epics/stories/actor coverage, VER evidence: computed for the ledger
    for sc in d.scenarios:
        tot = {"pass": 0, "fail": 0, "skip": 0}
        for t in sc["tests"]:
            for k, v in d.results.get(t, {}).items():
                tot[k] += v
        sc["counts"] = tot
        if not sc["tests"]:
            sc["state"] = "⚠"
        elif tot["fail"]:
            sc["state"] = "🔴"
        elif not sum(tot.values()):
            sc["state"] = "📝"
        elif tot["skip"]:
            sc["state"] = "⏭"
        else:
            sc["state"] = "✅"
    d.rule_state = {}
    for rid in reqs:
        if prefix(rid) == "VER":
            continue
        r = d.rule_of.get(rid)
        if r is None:
            d.rule_state[rid] = "⚠ no rule"
        elif not r["scenarios"]:
            d.rule_state[rid] = "⚠ no scenario"
        else:
            states = {sc["state"] for sc in r["scenarios"]}
            for sym, word in (("🔴", "red"), ("⚠", "test missing"), ("📝", "not run"),
                              ("⏭", "skipped here"), ("✅", "green")):
                if sym in states:
                    d.rule_state[rid] = f"{sym} {word}"
                    break
        if test_verified(d, rid) and d.rule_state[rid].startswith("⚠ no"):
            d.gaps.append(f"{reqs[rid]['file']}:{reqs[rid]['line']}: {rid} is verified by Test "
                          f"but {'has no Rule' if r is None else 'its Rule has no scenario'}")

    # stories: traced Test-verified requirements, derived status
    def below(rs):
        out, todo = set(), list(rs)
        while todo:
            x = todo.pop()
            if x not in out:
                out.add(x)
                todo += d.children[x]
        return out
    for s in d.stories.values():
        direct = d.refiners[s["id"]]
        traced = below(direct)
        s["direct"] = [r for r in direct if test_verified(d, r)]
        s["needed"] = sorted([r for r in traced if test_verified(d, r)], key=natkey)
        s["green"] = [r for r in s["needed"] if d.rule_state[r].startswith("✅")]
        s["derived"] = "done" if s["needed"] and len(s["green"]) == len(s["needed"]) else "open"
        if s["status"] in ("open", "done") and s["status"] != s["derived"]:
            E.append(f"stories.md:{s['line']}: {s['id']} is recorded "
                     f"{STATUS[s['status']]} but its rules make it {STATUS[s['derived']]}; "
                     f"run tracecheck.py --record-status")
    for e in d.epics.values():
        live = [d.stories[u] for u in e["listed"] if u in d.stories
                and d.stories[u]["status"] != "retired"]
        e["derived"] = "done" if live and all(s["derived"] == "done" for s in live) else "open"
        if e["status"] in ("open", "done") and e["status"] != e["derived"]:
            E.append(f"epics.md:{e['line']}: {e['id']} is recorded {STATUS[e['status']]} but "
                     f"its stories make it {STATUS[e['derived']]}; run tracecheck.py "
                     f"--record-status")
    return d


# ------------------------------------------------------------------ outputs

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
    return (sum(sum(1 for _ in open(f, encoding="utf-8", errors="replace")) for f in files),
            len(files))


def req_status(d, r):
    st = d.rule_state[r]
    if test_verified(d, r):
        return st
    methods = sorted({d.reqs[v]["fields"].get("Method") for v in vers_of(d, r)} - {"Test"})
    icon = ", ".join(("🔍 " if m == "Inspection" else "📊 ") + m for m in methods)
    return icon + ("" if st.startswith("⚠") else f" · rule {st}")


def stories_of_req(d, r):
    """Stories a requirement traces to: its own Story field, else its parents'."""
    own = re.findall(r"US-\d+", d.reqs[r]["fields"].get("Story", ""))
    if own:
        return own, True
    out = set()
    for q in ids_in(d.reqs[r]["fields"].get("Derives from")):
        if q in d.reqs:
            out |= set(stories_of_req(d, q)[0])
    return sorted(out, key=natkey), False


def ver_evidence(d, v):
    f = d.reqs[v]["fields"]
    targets = ids_in(f.get("Verifies"))
    cited = re.findall(r"@(VER-[A-Z]+-\d+)", f.get("Evidence", ""))
    out = []
    for sc in d.scenarios:
        rule = sc["rule"]["id"] if sc["rule"] else None
        if rule in targets or v in sc["tags"] or any(c in sc["tags"] for c in cited):
            out.append(sc)
    return out


def write_ledger(d):
    reqs, out = d.reqs, []
    w = out.append
    w("# Traceability matrix (ledger)\n")
    w("Generated by `tools/tracecheck.py` from the records, the test names and the last "
      "`tests/run_all.sh` results (`tests/results/`); do not edit by hand. This is the only "
      "place test status is written: story and epic status in `stories.md` and `epics.md` "
      "follow from it, and `backlog.md` lists what is still open. Framework: "
      "[`bdd-framework.md`](bdd-framework.md) v2.0.\n")
    w("Status legend: ✅ green · 🔴 tests failing · ⏭ skipped here (no QEMU, board or cross "
      "compiler) · 📝 tests not run · ⚠ gap (no rule, no scenario or no test) · 📊 "
      "Analysis/Demonstration · 🔍 Inspection · ⛔ RETIRED\n")

    # summary
    w("## Summary\n")
    w("| Item | Count |")
    w("|---|---|")
    w(f"| Actors | {len(d.actors)} ({sum(1 for a in d.actors.values() if a['type'] == 'Primary')} primary) |")
    w(f"| Epics | {len(d.epics)} ({sum(1 for e in d.epics.values() if e['status'] == 'done')} Done) |")
    w(f"| User stories | {len(d.stories)} ({sum(1 for s in d.stories.values() if s['status'] == 'done')} Done) |")
    for p in ORDER:
        w(f"| {TYPES[p][0]} requirements (`{p}`) | {sum(1 for r in reqs if prefix(r) == p)} |")
    w(f"| Features | {len(d.features)} |")
    w(f"| Rules | {len(d.rule_of)} ({sum(1 for r in d.rule_of.values() if not r['scenarios'])} without a scenario) |")
    w(f"| Scenarios | {len(d.scenarios)} |")
    w(f"| Test IDs | {sum(len(s['tests']) for s in d.scenarios)} |")
    w("")
    vers = [r for r in reqs.values() if prefix(r["id"]) == "VER"]
    w("| Verification method | Count |   | Verification status | Count |")
    w("|---|---|---|---|---|")
    stat = [(s, sum(1 for v in vers if status_word(v["fields"].get("Status")) == s))
            for s in ("Passed", "Partial", "Pending")] + [("", "")]
    for (m, s) in zip(METHODS, stat):
        w(f"| {m} | {sum(1 for v in vers if v['fields'].get('Method') == m)} |   | {s[0]} | {s[1]} |")
    sys_ids = [r for r in reqs if prefix(r) == "SYS"]
    covered = [r for r in sys_ids if any(re.search(r"QEMU|Host", reqs[v]["fields"].get(
        "Environment", "")) for v in d.verifiers[r])]
    lines, nfiles = source_lines(d.root)
    w("")
    w(f"* **Emulator/host coverage (BR-05 KPI):** {len(covered)} of {len(sys_ids)} system "
      f"requirements ({100.0 * len(covered) / max(len(sys_ids), 1):.0f} %) have a verification "
      "runnable in QEMU or on the host (target ≥ 80 %).")
    w(f"* **Source size (BR-01 KPI):** {lines} lines in {nfiles} firmware, tool and build "
      "files (target ≤ 2,500).")
    w(f"* **Check result:** {len(d.errors)} errors, {len(d.gaps)} coverage gaps, "
      f"{len(d.warnings)} warnings.\n")

    # requirement coverage
    w("## Requirement coverage\n")
    w("Story: the story the requirement refines (↑ = inherited through Derives from).\n")
    w("| REQ ID | Level | Derives from | Story | Feature | Pattern | Scenario ID(s) | "
      "Test ID(s) | VER (method) | Status |")
    w("|---|---|---|---|---|---|---|---|---|---|")
    for p in ORDER[:-1]:
        for r in sorted((x for x in reqs if prefix(x) == p), key=natkey):
            f = reqs[r]["fields"]
            sts, own = stories_of_req(d, r)
            story = ", ".join(sts) if own else ("↑" if sts else "—")
            rule = d.rule_of.get(r)
            scs = rule["scenarios"] if rule else []
            tests = sorted({t for s in scs for t in s["tests"]}, key=natkey)
            vs = ", ".join(f"{v} ({reqs[v]['fields'].get('Method', '?')})" for v in vers_of(d, r))
            w(f"| {r} | {TYPES[p][0]} | {', '.join(ids_in(f.get('Derives from'))) or '—'} | "
              f"{story} | {rule['feature']['id'] if rule else '—'} | {f.get('EARS', '')} | "
              f"{', '.join(s['id'] for s in scs) or '—'} | {', '.join(tests) or '—'} | {vs} | "
              f"{req_status(d, r)} |")
    w("")

    # story coverage
    w("## Story coverage\n")
    w("Rules: the Test-verified requirements that trace to the story, directly (its "
      "refining requirements) or inherited (everything derived from them). A story is "
      "Done in `stories.md` exactly when Rules ✅ equals the total.\n")
    w("| Epic | Realises | Story | Actor | Refined by | Feature(s) | Rules (direct + inherited) | Rules ✅ |")
    w("|---|---|---|---|---|---|---|---|")
    for s in sorted(d.stories.values(), key=lambda s: (natkey(s["epic"]), natkey(s["id"]))):
        e = d.epics.get(s["epic"], {"realises": []})
        feats = re.findall(r"FEAT-\d+", s["fields"].get("Feature(s)", ""))
        inh = len(s["needed"]) - len(s["direct"])
        w(f"| {s['epic']} | {', '.join(e['realises'])} | {s['id']} | {s['actor']} | "
          f"{', '.join(d.refiners[s['id']])} | {', '.join(feats)} | "
          f"{', '.join(s['direct']) or '—'} + {inh} inherited | "
          f"{len(s['green'])} of {len(s['needed'])} |")
    w("")
    w("## Actor coverage\n")
    w("| Actor | Type | Stories | Personas used in features |")
    w("|---|---|---|---|")
    feature_text = {f["id"]: open(os.path.join(d.root, "docs", "features", f["file"]),
                                  encoding="utf-8").read() for f in d.features}
    for a in sorted(d.actors.values(), key=lambda a: natkey(a["id"])):
        sts = [s["id"] for s in d.stories.values() if s["actor"] == a["id"]]
        used = []
        for p in a["personas"]:
            fs = [fid for fid, t in feature_text.items() if f'"{p}"' in t.split("Rule:", 1)[-1]]
            used.append(f'"{p}" ({", ".join(fs) or "not yet in a scenario"})')
        w(f"| {a['id']} {a['name']} | {a['type']} | {', '.join(sts) or '—'} | "
          f"{'; '.join(used) or '—'} |")
    w("")

    # scenarios
    w("## Scenarios and tests\n")
    w("T01 of a scenario not tagged `@gtest` is its pytest-bdd binding; other tests are "
      "GoogleTest.\n")
    w("| Scenario | Rule | Feature | Environment | Tests | Passed | Failed | Skipped | State |")
    w("|---|---|---|---|---|---|---|---|---|")
    for sc in sorted(d.scenarios, key=lambda s: natkey(s["id"] or "")):
        env = " ".join(t for t in ("host", "qemu", "hardware", "pending", "gtest")
                       if t in sc["tags"])
        c = sc["counts"]
        w(f"| {sc['id']} | {sc['rule']['id'] if sc['rule'] else '—'} | {sc['feature']['id']} | "
          f"{env} | {', '.join(sorted(sc['tests'], key=natkey))} | {c['pass']} | {c['fail']} | "
          f"{c['skip']} | {sc['state']} |")
    w("")

    # VER entries
    w("## Verification entries\n")
    w("Evidence outcome: the states of the scenarios under the rules of the requirements "
      "the entry verifies, tagged with the entry, or tagged with an entry its Evidence "
      "field cites.\n")
    w("| ID | Verifies | Method | Environment | Recorded status | Evidence outcome |")
    w("|---|---|---|---|---|---|")
    for v in sorted((r for r in reqs if prefix(r) == "VER"), key=natkey):
        f = reqs[v]["fields"]
        ev = ver_evidence(d, v)
        counts = {}
        for sc in ev:
            counts[sc["state"]] = counts.get(sc["state"], 0) + 1
        outc = " ".join(f"{k}{n}" for k, n in sorted(counts.items())) or "— (manual procedure)"
        w(f"| {v} | {', '.join(ids_in(f.get('Verifies')))} | {f.get('Method')} | "
          f"{f.get('Environment', '')} | {status_word(f.get('Status'))} | {outc} |")
    w("")
    write_audit(d, w)

    w("## Derivation tree (BR → STK → SYS)\n")
    for br in sorted((r for r in reqs if prefix(r) == "BR"), key=natkey):
        w(f"* **{br}** {reqs[br]['title']}")
        for stk in sorted(d.children[br], key=natkey):
            w(f"  * {stk} {reqs[stk]['title']}")
            for s in sorted(d.children[stk], key=natkey):
                w(f"    * {s} {reqs[s]['title']}")
    w("")
    for title, items in (("Errors", d.errors), ("Coverage gaps", d.gaps),
                         ("Warnings", d.warnings)):
        if items:
            w(f"## {title}\n")
            w("\n".join(f"* {x}" for x in items))
            w("")
    path = os.path.join(d.root, "docs", "traceability.md")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(out))
    return path


def write_audit(d, w):
    reqs = d.reqs
    ordinary = [r for r in reqs if prefix(r) != "VER"]
    w("## Audit (Phase 6)\n")
    w("### Epics and stories\n")
    w(f"* Business requirements realised by no epic: "
      f"{sum(1 for r in reqs if prefix(r) == 'BR' and not any(r in e['realises'] for e in d.epics.values()))}.")
    w(f"* Epics with no story: {sum(1 for e in d.epics.values() if not e['listed'])}. "
      f"Stories with no epic, actor or refining requirement: "
      f"{sum(1 for s in d.stories.values() if not (s['epic'] in d.epics and s['actor'] in d.actors and d.refiners[s['id']]))}.")
    w(f"* Primary actors in no story: "
      f"{sum(1 for a in d.actors.values() if a['type'] == 'Primary' and not any(s['actor'] == a['id'] for s in d.stories.values()))}.")
    w(f"* Stories Done: {sum(1 for s in d.stories.values() if s['status'] == 'done')} of "
      f"{len(d.stories)}; epics Done: {sum(1 for e in d.epics.values() if e['status'] == 'done')} "
      f"of {len(d.epics)}.\n")
    w("### Downward\n")
    orphans = [r for r in ordinary if TYPES[prefix(r)][1] and not ids_in(
        reqs[r]["fields"].get("Derives from"))]
    childless = [r for r in ordinary if prefix(r) in NEEDS_CHILDREN and not d.children[r]]
    w(f"* Requirements below Business with no parent: {len(orphans)}. Parents (BR, STK, SYS, "
      f"SUB, SW) with no child: {len(childless)}.\n")
    w("### Behaviour\n")
    tv = [r for r in ordinary if test_verified(d, r)]
    norule = [r for r in tv if r not in d.rule_of]
    empty = [r for r in d.rule_of if not d.rule_of[r]["scenarios"]]
    w(f"* Features: {len(d.features)}, each in one epic and one level folder.")
    w(f"* Test-verified requirements: {len(tv)}; with no Rule: {len(norule)}"
      + (f" ({', '.join(norule)})" if norule else "") + ".")
    w(f"* Rules with no scenario: {len(empty)}. A requirement exercised by another rule's "
      "scenarios (an extra requirement tag) still needs a scenario under its own Rule:\n")
    if empty:
        w("| Rule | Feature | Exercised by (tagged scenarios) |")
        w("|---|---|---|")
        for r in sorted(empty, key=natkey):
            by = [sc["id"] for sc in d.scenarios if r in sc["tags"]]
            w(f"| {r} | {d.rule_of[r]['feature']['id']} | {', '.join(by) or '—'} |")
        w("")
    w("### Across and up\n")
    test_vers = sorted((v for v in reqs if prefix(v) == "VER"
                        and reqs[v]["fields"].get("Method") == "Test"), key=natkey)
    def outcome(v):
        states = {sc["state"] for sc in ver_evidence(d, v)}
        if "🔴" in states:
            return "failing"
        if "✅" in states:
            return "passing"
        if states:
            return "not yet passing (skipped or not run)"
        return "manual procedure only"
    groups = {}
    for v in test_vers:
        groups.setdefault(outcome(v), []).append(v)
    w(f"* Requirements with no VER entry: {sum(1 for r in ordinary if not vers_of(d, r))}. "
      f"Scenarios with no test: {sum(1 for s in d.scenarios if not s['tests'])}.")
    w(f"* Test-method VER entries: {len(test_vers)}.\n")
    w("| Evidence outcome | VER entries |")
    w("|---|---|")
    for k in ("passing", "failing", "not yet passing (skipped or not run)",
              "manual procedure only"):
        w(f"| {k} | {len(groups.get(k, []))}: {', '.join(groups.get(k, [])) or '—'} |")
    w("")
    w("### Thread check (Business → epic → story → … → passing unit test)\n")
    w("| Business requirement | Example thread |")
    w("|---|---|")
    broken = []
    for br in sorted((r for r in reqs if prefix(r) == "BR"), key=natkey):
        found = None
        for e in sorted((e for e in d.epics.values() if br in e["realises"]),
                        key=lambda e: natkey(e["id"])):
            for us in e["listed"]:
                for top in d.refiners.get(us, []):
                    path = thread(d, top, [top])
                    if path and (found is None or len(path) < len(found[2])):
                        found = (e["id"], us, path)
        if not found:
            broken.append(br)
            w(f"| {br} | **broken** |")
        else:
            e, us, path = found
            sc = next(s["id"] for s in d.rule_of[path[-1]]["scenarios"] if s["state"] == "✅")
            w(f"| {br} | {br} → {e} → {us} → {' → '.join(path)} → {sc} |")
    w("")
    w(f"Result: {len([r for r in reqs if prefix(r) == 'BR']) - len(broken)} of "
      f"{len([r for r in reqs if prefix(r) == 'BR'])} business requirements reach a passing "
      "unit test" + (f"; broken: {', '.join(broken)}." if broken else ".") + "\n")
    w("### Retired items\n")
    retired = [a["id"] for a in d.actors.values() if a["retired"]] + \
        [x["id"] for x in list(d.epics.values()) + list(d.stories.values())
         if x["status"] == "retired"]
    w((", ".join(retired) if retired else "None in the records.") +
      " Retired v1 feature IDs (F-01…F-18) are listed in `features.md`.\n")


def thread(d, r, path):
    rule = d.rule_of.get(r)
    if prefix(r) == "CMP" and rule and any(s["state"] == "✅" for s in rule["scenarios"]):
        return path
    best = None
    for c in sorted(d.children[r], key=natkey):
        p = thread(d, c, path + [c])
        if p and (best is None or len(p) < len(best)):
            best = p
    return best


def write_backlog(d):
    out = []
    w = out.append
    open_ = [s for s in d.stories.values() if s["status"] not in ("done", "retired")]
    prio = {p: i for i, p in enumerate(PRIORITIES)}
    open_.sort(key=lambda s: (s["status"] == "proposed",
                              prio.get(s["fields"].get("Priority"), 9),
                              natkey(s["epic"]), natkey(s["id"])))
    w("# Backlog (work view)\n")
    w("Generated by `tools/tracecheck.py` from `stories.md` and `traceability.md`; holds "
      "nothing of its own. Done and retired stories are not listed: their record is in "
      "`stories.md`.\n")
    w("## Open work\n")
    if not open_:
        w(f"None. All {len(d.stories)} stories and {len(d.epics)} epics are Done; see "
          "stories.md and epics.md.")
    else:
        done_s = sum(1 for s in d.stories.values() if s["status"] == "done")
        done_e = sum(1 for e in d.epics.values() if e["status"] == "done")
        w(f"**Progress:** {done_s} of {len(d.stories)} stories Done · {done_e} of "
          f"{len(d.epics)} epics Done · **Next:** {open_[0]['id']}\n")
        w("| Order | Story | Title | Epic | Actor | Priority | Status | Rules ✅ | Still needs |")
        w("|---|---|---|---|---|---|---|---|---|")
        for i, s in enumerate(open_, 1):
            counts = {}
            for r in s["needed"]:
                sym = d.rule_state[r].split()[0]
                if sym != "✅":
                    counts[sym] = counts.get(sym, 0) + 1
            needs = " · ".join(f"{k} {n}" for k, n in sorted(counts.items())) or "—"
            w(f"| {i} | {s['id']} | {s['title']} | {s['epic']} | {s['actor']} | "
              f"{s['fields'].get('Priority')} | {STATUS[s['status']]} | "
              f"{len(s['green'])} of {len(s['needed'])} | {needs} |")
        w("")
        w("Order: Must → Should → Could, then epic and story ID; Proposed stories last. "
          "Still needs counts the story's rules by state: 🔴 failing (Phase 5: fix), ⏭ "
          "skipped here (run in QEMU, on a board or with the cross compiler), 📝 not run, "
          "⚠ no rule or no scenario (Phase 3: write one).\n")
        w("## What each open story still needs\n")
        action = {"🔴": "fix until its tests pass (Phase 5)",
                  "⏭": "run where its environment exists (QEMU, board or cross compiler)",
                  "📝": "run its tests",
                  "⚠": "write a scenario under its Rule (Phase 3), then its test (Phase 4)"}
        for i, s in enumerate(open_, 1):
            w(f"### {i}. {s['id']} — {s['title']}\n")
            groups = {}
            for r in s["needed"]:
                sym = d.rule_state[r].split()[0]
                if sym != "✅":
                    groups.setdefault(sym, []).append(r)
            if not s["needed"]:
                w("- No Test-verified requirement traces to this story yet.")
            for sym in ("🔴", "⚠", "📝", "⏭"):
                if sym in groups:
                    w(f"- {sym} {action[sym]}: {', '.join(groups[sym])}")
            w("")
    w("## Defects not tied to a story\n")
    storyless = [r for r in d.reqs if prefix(r) != "VER" and test_verified(d, r)
                 and not d.rule_state[r].startswith("✅")
                 and not any(r in s["needed"] for s in d.stories.values())]
    if d.errors:
        w(f"- {len(d.errors)} errors from the last check; see `traceability.md`.")
    if storyless:
        w(f"- Not green and traced to no story: {', '.join(sorted(storyless, key=natkey))}.")
    if not d.errors and not storyless:
        w("None.")
    w("")
    path = os.path.join(d.root, "docs", "backlog.md")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(out))
    return path


def record_status(d, today=None):
    """Write derived story and epic status changes into the records."""
    today = today or datetime.date.today().isoformat()
    changed = []
    for fname, items, kind in (("stories.md", d.stories, "story"), ("epics.md", d.epics, "epic")):
        path = os.path.join(d.root, "docs", fname)
        text = open(path, encoding="utf-8").read()
        for x in items.values():
            if x["status"] not in ("open", "done") or x["status"] == x["derived"]:
                continue
            head = re.search(r"^## " + re.escape(x["id"]) + r" — .*$", text, re.M)
            end = re.search(r"^## ", text[head.end():], re.M)
            stop = head.end() + (end.start() if end else len(text) - head.end())
            sec = text[head.end():stop]
            if x["derived"] == "done":
                if kind == "story":
                    rules = " · ".join(f"{r} ({', '.join(sorted({t for s in d.rule_of[r]['scenarios'] for t in s['tests']}, key=natkey))})"
                                       for r in x["needed"])
                    other = "; ".join(f"{v} {d.reqs[v]['fields'].get('Method')}: "
                                      f"{status_word(d.reqs[v]['fields'].get('Status'))}"
                                      for r in d.refiners[x["id"]] for v in vers_of(d, r)
                                      if d.reqs[v]["fields"].get("Method") != "Test")
                    rec = f"{today} · Rules ✅: {rules}" + (f" · Other verification: {other}" if other else "")
                else:
                    rec = f"{today} · " + " · ".join(f"{u} Done" for u in x["listed"])
                sec = re.sub(r"^- \*\*Status:\*\* .*$", "- **Status:** ✅ Done", sec, flags=re.M)
                sec = re.sub(r"^- \*\*Completion record:\*\* .*$",
                             f"- **Completion record:** {rec}", sec, flags=re.M)
                note = f"{today} Done"
            else:
                why = [r for r in x.get("needed", []) if not d.rule_state[r].startswith("✅")]
                sec = re.sub(r"^- \*\*Status:\*\* .*$", "- **Status:** ⏳ Open", sec, flags=re.M)
                sec = re.sub(r"^(- \*\*Completion record:\*\* )(.*)$",
                             lambda m: f"{m.group(1)}— (reopened {today}; last record: {m.group(2)})",
                             sec, count=1, flags=re.M)
                note = f"{today} Reopened" + (f" ({', '.join(why[:5])} not green)" if why else "")
            sec = re.sub(r"^(- \*\*History:\*\* [^\n]*(?:\n  [^\n]*)*)",
                         lambda m: m.group(1) + f" · {note}", sec, count=1, flags=re.M)
            text = text[:head.end()] + sec + text[stop:]
            new = "✅ Done" if x["derived"] == "done" else "⏳ Open"
            text = re.sub(r"^(\| " + re.escape(x["id"]) + r" \|.*\| )[^|]*(\|\s*)$",
                          lambda m: m.group(1) + new + " " + m.group(2), text, count=1,
                          flags=re.M)
            changed.append(f"{x['id']}: {STATUS[x['status']]} → {new}")
        if kind == "epic":   # "(n of m Done)" follows the stories' recorded status
            def count(m):
                ids = re.findall(r"US-\d+", m.group(2))
                n = sum(1 for u in ids if u in d.stories and
                        (d.stories[u]["derived"] if d.stories[u]["status"] in ("open", "done")
                         else d.stories[u]["status"]) == "done")
                return f"{m.group(1)}({n} of {len(ids)} Done)"
            text = re.sub(r"^(- \*\*Stories:\*\* ((?:US-\d+(?:, )?)+) )\(\d+ of \d+ Done\)",
                          count, text, flags=re.M)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
    return changed


# ---------------------------------------------------------------- self test

FIXTURE = {
    "docs/actors.md": "| ID | Actor | Type | Goal | Personas |\n|---|---|---|---|---|\n"
                      "| ACT-H1 | Dev | Primary | build | \"dana\" |\n",
    "docs/epics.md": "## Index\n\n| ID | Epic | Realises | Priority | Stories | Status |\n"
                     "|---|---|---|---|---|---|\n| EP-01 | E | BR-01 | Must | US-01 | ⏳ Open |\n\n"
                     "## EP-01 — E\n- **Realises:** BR-01 · **Priority:** Must\n"
                     "- **Stories:** US-01\n- **Status:** ⏳ Open\n- **Completion record:** —\n"
                     "- **History:** x\n",
    "docs/stories.md": "## Index\n\n| ID | Title | Epic | Actor | Priority | Status |\n"
                       "|---|---|---|---|---|---|\n| US-01 | S | EP-01 | ACT-H1 | Must | ⏳ Open |\n\n"
                       "## US-01 — S\n- **Epic:** EP-01 · **Actor:** ACT-H1 Dev · **Priority:** Must\n"
                       "- **Story:** As a developer, I want x, so that y.\n"
                       "- **Acceptance criteria → requirements:**\n  1. It works. → STK-01\n"
                       "- **Refined by:** STK-01 · **Feature(s):** FEAT-001\n"
                       "- **Status:** ⏳ Open\n- **Completion record:** —\n- **History:** x\n",
    "docs/requirements/BR.md": "### BR-01 — b\n- **Type:** Business\n- **EARS:** Ubiquitous\n"
                               "- **Priority:** Must\n- **Statement:** s\n- **Derives from:** —\n"
                               "- **Rationale:** r\n- **Verified by:** VER-BR-01\n",
    "docs/requirements/STK.md": "### STK-01 — k\n- **Type:** Stakeholder\n- **EARS:** Ubiquitous\n"
                                "- **Priority:** Must\n- **Statement:** The user needs k.\n"
                                "- **Derives from:** BR-01\n- **Story:** US-01\n"
                                "- **Rationale:** r\n- **Verified by:** VER-STK-01\n",
    "docs/requirements/VER.md": "### VER-BR-01 — v\n- **Type:** Verification\n- **Verifies:** BR-01\n"
                                "- **Method:** Analysis\n- **Environment:** Host\n- **Status:** Passed\n\n"
                                "### VER-STK-01 — v\n- **Type:** Verification\n- **Verifies:** STK-01\n"
                                "- **Method:** Test\n- **Environment:** Host\n- **Status:** Passed\n",
    "docs/features/acceptance/f.feature":
        "@EP-01 @FEAT-001\nFeature: FEAT-001: f\n  Epic: EP-01\n\n  User stories delivered:\n"
        "    US-01  As a developer, I want x,\n           so that y.\n\n"
        "  @STK-01 @US-01\n  Rule: STK-01: k\n    EARS: The user needs k.\n\n"
        "    @host @VER-STK-01\n    Scenario: STK-01-S01: s\n      Given x\n\n"
        "    @host @gtest\n    Scenario: STK-01-S02: u\n      Given y\n",
    "tests/gtest/t.cpp": "TEST(U, STK_01_S02_T01_u) {}\n",
    "tests/bdd/.keep": "",
}


def self_test():
    """Build small fixture trees, one per error class, and expect detection."""
    F = FIXTURE
    feat, story = "docs/features/acceptance/f.feature", "docs/stories.md"
    cases = {
        "clean": ({}, None),
        "duplicate ID": ({"docs/requirements/BR.md": F["docs/requirements/BR.md"] * 2},
                         "duplicate ID"),
        "unknown parent": ({"docs/requirements/STK.md": F["docs/requirements/STK.md"].replace(
            "from:** BR-01", "from:** BR-09")}, "derives from unknown"),
        "wrong level": ({"docs/requirements/STK.md": F["docs/requirements/STK.md"].replace(
            "from:** BR-01", "from:** STK-01")}, "may not derive"),
        "unverified": ({"docs/requirements/STK.md": F["docs/requirements/STK.md"].replace(
            "- **Verified by:** VER-STK-01\n", ""),
            "docs/requirements/VER.md": F["docs/requirements/VER.md"].split("\n\n")[0] + "\n"},
            "is not verified"),
        "no method": ({"docs/requirements/VER.md": F["docs/requirements/VER.md"].replace(
            "Method:** Test", "Method:** Guess")}, "no single TAID method"),
        "no priority": ({"docs/requirements/STK.md": F["docs/requirements/STK.md"].replace(
            "- **Priority:** Must\n", "")}, "has no priority"),
        "unknown tag": ({feat: F[feat].replace("@VER-STK-01", "@SYS-77")},
                        "unknown requirement tag"),
        "scenario without ID": ({feat: F[feat].replace("STK-01-S01: ", "")},
                                "scenario has no ID"),
        "scenario outside a rule": ({feat: F[feat].replace("  @STK-01 @US-01\n  Rule: STK-01: k\n"
                                                           "    EARS: The user needs k.\n", "")},
                                    "sits outside a Rule"),
        "rule at the wrong level": ({"docs/features/unit/f.feature": F[feat], feat: None},
                                    "is in a unit feature"),
        "EARS line differs": ({feat: F[feat].replace("EARS: The user", "EARS: A user")},
                              "EARS line differs"),
        "narrative differs": ({feat: F[feat].replace("I want x,", "I want z,")},
                              "differs from stories.md"),
        "unknown actor": ({story: F[story].replace("**Actor:** ACT-H1", "**Actor:** ACT-H9")},
                          "unknown actor"),
        "epic and story disagree": ({"docs/epics.md": F["docs/epics.md"].replace(
            "- **Stories:** US-01", "- **Stories:** US-02")}, "does not list it"),
        "story refined by nothing": ({"docs/requirements/STK.md": F["docs/requirements/STK.md"]
                                      .replace("- **Story:** US-01\n", "")},
                                     "refined by no requirement"),
        "Done without its rules green": ({story: F[story].replace("⏳ Open", "✅ Done")},
                                         "is recorded ✅ Done"),
        "gtest scenario without test": ({"tests/gtest/t.cpp": ""}, "has no test"),
        "test for unknown scenario": ({"tests/gtest/t.cpp": F["tests/gtest/t.cpp"] +
                                       "TEST(U, STK_01_S09_T01_x) {}\n"},
                                      "names unknown scenario"),
        "T01 reused by GoogleTest": ({"tests/gtest/t.cpp": F["tests/gtest/t.cpp"] +
                                      "TEST(U, STK_01_S01_T01_x) {}\n"},
                                     "reserved for the pytest-bdd binding"),
    }
    ok = True
    for name, (override, expect) in cases.items():
        with tempfile.TemporaryDirectory() as root:
            files = dict(F, **override)
            for rel, txt in files.items():
                if txt is None:
                    continue
                path = os.path.join(root, rel)
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, "w", encoding="utf-8") as fh:
                    fh.write(txt)
            errs = check(root).errors
            good = not errs if expect is None else any(expect in e for e in errs)
            print(f"  {'ok ' if good else 'BAD'} {name}" + ("" if good else f": {errs}"))
            ok &= good
    print("self-test: all error classes detected" if ok else "self-test: FAILED")
    return 0 if ok else 1


def main(argv):
    if "--self-test" in argv:
        return self_test()
    d = check(ROOT)
    if "--record-status" in argv:
        for c in record_status(d):
            print("recorded", c)
        d = check(ROOT)
    for e in d.errors:
        print("error:", e)
    for x in d.warnings:
        print("warning:", x)
    if "--check" not in argv and "--strict" not in argv:
        for p in (write_ledger(d), write_backlog(d)):
            print("wrote", os.path.relpath(p, ROOT))
    print(f"{len(d.reqs)} requirements, {len(d.stories)} stories, {len(d.features)} features, "
          f"{len(d.scenarios)} scenarios: {len(d.errors)} errors, {len(d.gaps)} coverage gaps, "
          f"{len(d.warnings)} warnings")
    if "--strict" in argv:
        for g in d.gaps:
            print("gap:", g)
        return 1 if d.errors or d.gaps else 0
    return 1 if d.errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
