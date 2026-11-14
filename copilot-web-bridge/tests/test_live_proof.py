"""The live proof script: its verifiers, and a full rehearsal against the fake Copilot."""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import zipfile
from pathlib import Path

import live_proof as lp

BRIDGE_DIR = Path(__file__).resolve().parent.parent


def test_verifiers():
    assert lp.word_present("The code word is kestrel-48213.", "KESTREL-48213")
    assert lp.digits_present("The number shown is 482 796.", "482796")
    assert not lp.digits_present("I can't read it", "482796")
    assert lp.compare_lines("alpha X\nbravo Y\n", ["alpha X", "bravo Y"]) == "exact"
    assert lp.compare_lines("1. alpha X\n2. bravo Y", ["alpha X", "bravo Y"]) == "partial"
    assert lp.compare_lines("nothing", ["alpha X"]) == "missing"
    assert lp.check_csv_sum("a,b,sum\n1,2,3\n-4,10,6\n", [(1, 2), (-4, 10)]) == (True, "all sums correct")
    assert not lp.check_csv_sum("a,b,sum\n1,2,4\n", [(1, 2)])[0]
    assert not lp.check_csv_sum("x,y\n1,2\n", [(1, 2)])[0]


def test_file_contains_handles_office_files(tmp_path):
    docx = tmp_path / "proof.docx"
    with zipfile.ZipFile(docx, "w") as z:
        z.writestr("word/document.xml", "<w:t>OSPREY-12345</w:t>")
    assert lp.file_contains(docx, "OSPREY-12345")
    plain = tmp_path / "p.txt"
    plain.write_text("nope")
    assert not lp.file_contains(plain, "OSPREY-12345")


def test_rehearsal_proves_every_step():
    out = subprocess.run([sys.executable, str(BRIDGE_DIR / "live_proof.py"), "--rehearse"],
                         capture_output=True, text=True, timeout=600, cwd=BRIDGE_DIR, env=dict(os.environ))
    assert out.returncode == 0, out.stdout[-3000:] + out.stderr[-3000:]
    report_path = re.search(r"Full report with evidence: (.+)", out.stdout).group(1).strip()
    report = json.loads(Path(report_path).read_text(encoding="utf-8"))
    assert {s["id"]: s["status"] for s in report["steps"]} == {f"P{i}": "PASS" for i in range(1, 7)}
