"""Randfälle, an denen Kernroutinen erfahrungsgemäß brechen (DEMO-PLAYBOOK §12)."""

import pytest

import uum_algorithm as A
import uum_evaluation as ev
from uum_scenario import partial_bay


def test_sorted_bay_has_no_blocker_and_needs_no_hub():
    bay = ((5, 3), (2, 1), (6, 4))
    assert A.blocker_count(bay) == 0 and A.initial_blockers(bay) == frozenset() and A.solve_exact(bay, 4) == 0
    assert A.optimal_trace(bay, 4).steps == () and A.hub_counts(A.optimal_trace(bay, 4)) == {}


def test_two_stacks_and_one_hub():
    bay = ((1, 2), ())
    assert A.solve_exact(bay, 3) == 1 and A.blocker_count(bay) == 1 and A.count_sequences(bay, 3, 1) == 1


def test_single_container_and_empty_bay():
    assert A.solve_exact(((1,), ()), 2) == 0 and A.solve_exact(((), ()), 2) == 0
    assert A.count_sequences(((), ()), 2, 0) == 1 and A.count_sequences(((), ()), 2, 1) == 0


def test_exactly_two_containers_in_each_order():
    assert A.solve_exact(((2,), (1,)), 2) == 0 and A.solve_exact(((2, 1),), 2) == 0 and A.solve_exact(((1, 2), ()), 2) == 1


def test_lower_bound_equals_optimum_when_every_blocker_has_a_free_stack():
    bay = ((1, 2), (3, 4), (5, 6), ())                                   # jeder Blocker hat den leeren Stapel oder einen Stapel mit größeren Nummern
    assert A.blocker_count(bay) == 3 and A.solve_exact(bay, 4) == 3


def test_tie_between_empty_stacks_is_equivalent():
    a = A.run_rule(((1, 2), (), ()), 3, A.rule_tight_fit)
    assert a.moves == 1 and a.steps[0].dst == 1


def test_partial_bay_input_checks():
    with pytest.raises(ValueError):
        partial_bay(4, 5, 16, 0)                                          # mehr als (Stapel - 1) * Höchsthöhe
    with pytest.raises(ValueError):
        partial_bay(4, 5, 0, 0)
    assert len(partial_bay(4, 5, 1, 0)) == 4 and sum(len(s) for s in partial_bay(4, 5, 1, 0)) == 1


def test_share_has_no_division_by_zero_and_grammar():
    assert ev.share(3, 0) == 0.0 and ev.share(1, 4) == 25.0
    assert ev.hubs(1) == "1 Hub" and ev.hubs(0) == "0 Hübe" and ev.times(1) == "einmal" and ev.times(2) == "zweimal" and ev.times(3) == "3-mal"


def test_histogram_caps_large_gaps_in_the_last_bucket():
    assert ev.gap_histogram([{"lb": 1, "opt": 1}, {"lb": 1, "opt": 9}, {"lb": 2, "opt": 3}]) == [1, 1, 0, 0, 1]
