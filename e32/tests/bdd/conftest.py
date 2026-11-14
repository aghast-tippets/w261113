"""
conftest.py -- environment detection, tag markers, skip and pending rules
for the e32 pytest-bdd layer.  See tests/README.md.

Order of decisions for every scenario:
 1. Collection: @hardware / @qemu scenarios whose environment is missing
    are marked skip with a precise reason, so no step ever runs.
 2. Before the first step: every step must resolve to a step definition
    (a StepDefinitionNotFoundError is raised otherwise, even for @pending).
 3. @pending scenarios (unless listed in AUTOMATED_PENDING) then fail with
    "PENDING automation: ..." -- the red state of the BDD pipeline.
 4. Steps that need a tool (cross compiler, esptool, QEMU, the GoogleTest
    binary) skip when it is absent.

E32_BDD_FORCE_ALL=1 turns off 1 and 4, so every step of every runnable
scenario executes; with tools absent such runs fail at the tool invocation.
"""
import pytest
from pytest_bdd.parser import FeatureParser
from pytest_bdd.scenario import get_step_function

from support import ENV, FEATURES, World, norm_tag, scenario_id

# @pending scenarios whose steps are nevertheless automated here; they run
# instead of failing with "PENDING automation:".  Keep docs/pipeline.md and
# the VER status in step when the feature files drop their @pending tag.
AUTOMATED_PENDING = {
    "SW-IMG-03-S01",   # crafted ELF files, run against the real tools/mkimage
    "CMP-21-S01",      # delegated to the GoogleTest suite (*CMP_21_S01*)
    "SW-FMT-01-S01",   # delegated to the GoogleTest suite (*SW_FMT_01_S01*)
}

ENV_TAGS = ("host", "qemu", "hardware", "pending")


def feature_files():
    return sorted(FEATURES.glob("*.feature"))


def _all_tags():
    tags = set()
    for path in feature_files():
        feature = FeatureParser(str(FEATURES), path.name).parse()
        tags |= feature.tags
        for sc in feature.scenarios.values():
            tags |= sc.tags
            for ex in sc.examples:
                tags |= ex.tags
    return tags


def pytest_configure(config):
    for tag in sorted(_all_tags()):
        if tag not in ENV_TAGS:
            config.addinivalue_line("markers", f"{norm_tag(tag)}: Gherkin tag @{tag}")


def pytest_report_header(config):
    return f"e32 bdd environment: {ENV.summary()}"


def pytest_bdd_apply_tag(tag, function):
    """Gherkin @SYS-12 becomes marker SYS_12 (hyphens are not valid in -m)."""
    getattr(pytest.mark, norm_tag(tag))(function)
    return True


def pytest_collection_modifyitems(config, items):
    for item in items:
        tags = {m.name for m in item.iter_markers() if m.name in ENV_TAGS}
        reason = ENV.environment_skip_reason(tags)
        if reason:
            item.add_marker(pytest.mark.skip(reason=reason))


def pytest_bdd_before_scenario(request, feature, scenario):
    sid = scenario_id(scenario.name)
    request.node.e32_scenario_id = sid
    request.node.e32_tags = set(scenario.tags)
    missing = [s for s in scenario.steps if get_step_function(request, s) is None]
    if missing:
        from pytest_bdd.exceptions import StepDefinitionNotFoundError
        raise StepDefinitionNotFoundError(
            "Step definition is not found: " + "; ".join(repr(s.name) for s in missing))
    if "pending" in scenario.tags and sid not in AUTOMATED_PENDING:
        pytest.fail(f"PENDING automation: {sid} ({scenario.name.split(': ', 1)[-1]}) is "
                    "tagged @pending: its steps resolve, but it is not automated yet "
                    "(docs/pipeline.md, Phase 3)", pytrace=False)


@pytest.fixture
def world(request, tmp_path):
    example = {}
    if "_pytest_bdd_example" in request.fixturenames:
        example = request.getfixturevalue("_pytest_bdd_example") or {}
    w = World(request=request, tmp=tmp_path,
              sid=getattr(request.node, "e32_scenario_id", None), example=dict(example),
              tags=getattr(request.node, "e32_tags", set()))
    yield w
    w.close()
