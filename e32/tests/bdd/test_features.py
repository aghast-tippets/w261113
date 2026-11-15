"""
Binds every scenario of the feature files (docs/features/<level>/*.feature)
to a pytest test, except those tagged @gtest, which the GoogleTest suite
implements (conftest.py deselects them).

Each scenario's binding is its test T01: "CMP-21-S01: ..." becomes
test_CMP_21_S01_T01_<slug>, so `pytest -k CMP_21_S01` selects it.
"""
from pytest_bdd import scenarios
from pytest_bdd.exceptions import NoScenariosFound

from steps_acceptance import *  # noqa: F401,F403  (step definitions)
from steps_build import *  # noqa: F401,F403
from steps_console import *  # noqa: F401,F403
from steps_gtest import *  # noqa: F401,F403
from support import bind_scenario_ids, feature_files

for _feature in feature_files():
    try:
        scenarios(str(_feature))
    except NoScenariosFound:
        pass  # only empty Rules so far (Phase 3 gaps); nothing to bind

bind_scenario_ids(globals())
