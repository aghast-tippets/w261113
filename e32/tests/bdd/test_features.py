"""
Binds every scenario of the top-level feature files (docs/features/*.feature;
docs/features/unit/ belongs to another layer) to a pytest test.

Each scenario's binding is its test T01: "CMP-21-S01: ..." becomes
test_CMP_21_S01_T01_<slug>, so `pytest -k CMP_21_S01` selects it.
"""
from pytest_bdd import scenarios

from steps_acceptance import *  # noqa: F401,F403  (step definitions)
from steps_build import *  # noqa: F401,F403
from steps_console import *  # noqa: F401,F403
from steps_gtest import *  # noqa: F401,F403
from support import FEATURES, bind_scenario_ids

for _feature in sorted(FEATURES.glob("*.feature")):
    scenarios(str(_feature))

bind_scenario_ids(globals())
