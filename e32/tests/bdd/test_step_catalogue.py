"""
Static check, independent of the environment: every step of every
top-level scenario (each Examples row rendered) matches exactly one step
definition.  Catches a missing step even where the scenario itself is
skipped, and catches ambiguous patterns, whose winner would be arbitrary.
"""
from pytest_bdd.parser import FeatureParser
from pytest_bdd.steps import step_function_context_registry

import steps_acceptance  # noqa: F401  (registers the step definitions)
import steps_build  # noqa: F401
import steps_console  # noqa: F401
import steps_gtest  # noqa: F401
from support import FEATURES


def rendered_steps():
    for path in sorted(FEATURES.glob("*.feature")):
        feature = FeatureParser(str(FEATURES), path.name).parse()
        for name, template in feature.scenarios.items():
            contexts = [c for ex in template.examples for c in ex.as_contexts()] or [{}]
            for ctx in contexts:
                for st in template.render(ctx).steps:
                    yield path.name, name, st


def test_every_step_has_exactly_one_definition():
    contexts = list(step_function_context_registry.values())
    problems = []
    count = 0
    for fname, scen, st in rendered_steps():
        count += 1
        hits = [c for c in contexts
                if (c.type is None or c.type == st.type) and c.parser.is_matching(st.name)]
        if len(hits) != 1:
            names = sorted({c.step_func.__name__ for c in hits})
            problems.append(f"{fname}: {scen}: {st.type} {st.name!r} -> {len(hits)} definitions {names}")
    assert count > 0
    assert not problems, "\n".join(problems)
