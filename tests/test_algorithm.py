"""Kern gegen Handrechnung, unabhängigen Prüfer und Eigenschaften (DEMO-PLAYBOOK §1b und §12)."""

import random

import pytest

import uum_algorithm as A
from uum_scenario import canonical, make_bay, max_height, partial_bay


def _moves(trace):
    return [(s.container, s.dst) for s in trace.steps]


def test_autopop_takes_what_is_on_top_and_due(mini):
    bay, _ = mini
    st, popped = A.autopop(bay)
    assert popped == [] and st == bay                                  # die 1 liegt unter der 4: nichts ist dran und erreichbar
    st2, popped2 = A.autopop(((2, 1), (3,)))
    assert popped2 == [1, 2, 3] and st2 == ((), ())


def test_blocker_count_and_initial_blockers_by_hand(mini, counter):
    assert A.blocker_count(mini[0]) == 1 and A.initial_blockers(mini[0]) == frozenset({4})
    assert A.blocker_count(counter[0]) == 3 and A.initial_blockers(counter[0]) == frozenset({4, 5, 6})
    assert A.stack_blockers((1, 2, 3)) == 2                            # 2 und 3 liegen über der 1
    assert A.stack_blockers((3, 2, 1)) == 0                            # absteigend von unten nach oben: nichts blockiert
    assert A.stack_blockers((2, 5, 3, 1)) == 2                         # 5 über der 2, 3 über der 2; die 1 blockiert nichts
    assert A.initial_blockers(((2, 5, 3, 1),)) == frozenset({5, 3})


def test_single_blocker_needs_two_hubs_and_no_single_hub_works(mini):
    bay, h = mini
    assert A.solve_exact(bay, h) == 2
    assert A.count_sequences(bay, h, 1) == 0                           # beide Ziele für die 4 blockieren wieder; ein einziger Hub leert die Bucht nicht
    assert A.count_sequences(bay, h, 2) > 0
    tr = A.optimal_trace(bay, h)
    assert tr.moves == 2 and A.hub_counts(tr) == {4: 2}                # die 4 wird zweimal bewegt: Lücke 1 = ein Mehrfachhub
    assert A.check_trace(bay, h, _moves(tr)) == 2


def test_counterexample_numbers_from_stage_one(counter):
    bay, h = counter
    assert A.solve_exact(bay, h) == 4 and A.run_rule(bay, h, A.rule_tight_fit).moves == 5
    tr = A.optimal_trace(bay, h)
    assert _moves(tr) == [(5, 1), (5, 2), (4, 2), (6, 1)] and A.hub_counts(tr) == {5: 2, 4: 1, 6: 1}


def test_hub_counts_and_decomposition_identity():
    for sd in range(40):
        bay, h = make_bay(4, 3, sd), max_height(3, 2)
        for tr in [A.optimal_trace(bay, h)] + [A.run_rule(bay, h, r, sd) for r in A.RULES.values()]:
            counts = A.hub_counts(tr)
            assert set(counts) <= A.initial_blockers(bay), sd           # Satz 2: nur Blocker werden bewegt
            assert sum(counts.values()) == tr.moves
            assert tr.moves == A.blocker_count(bay) + sum(n - 1 for n in counts.values()), sd   # Folgerung: Hübe = Untergrenze + Mehrfachhübe


def test_every_blocker_is_moved_at_least_once():
    for sd in range(40):
        bay, h = make_bay(4, 3, sd), max_height(3, 2)
        for tr in [A.optimal_trace(bay, h)] + [A.run_rule(bay, h, r, sd) for r in A.RULES.values()]:
            assert set(A.hub_counts(tr)) == A.initial_blockers(bay), sd  # Satz 1: jeder Blocker mindestens einmal


def test_tight_fit_hand_trace(counter):
    bay, h = counter
    tr = A.run_rule(bay, h, A.rule_tight_fit)
    assert _moves(tr) == [(5, 0), (4, 2), (5, 1), (6, 1), (6, 0)]
    assert A.check_trace(bay, h, _moves(tr)) == 5


def test_rules_choose_as_described():
    assert A.rule_tight_fit(((7,), (5, 8), (9,), ()), 0, 6, 3) == 1
    assert A.rule_tight_fit(((7,), (2, 8), (9,), ()), 0, 6, 3) == 2
    assert A.rule_tight_fit(((7,), (2, 8), (1,), (4,)), 0, 6, 9) == 3
    assert A.rule_lowest(((7,), (5, 8), (9,), ()), 0, 6, 3) == 3
    assert A.rule_lowest(((4, 5), (1,), (2,)), 0, 6, 3) == 1


def test_every_rule_produces_a_valid_trace_on_random_bays():
    for sd in range(60):
        s, l = 3 + sd % 3, 2 + sd % 3
        bay, h = make_bay(s, l, sd), max_height(l, 2)
        for key, rule in A.RULES.items():
            tr = A.run_rule(bay, h, rule, sd)
            assert A.check_trace(bay, h, _moves(tr)) == tr.moves, (sd, key)


def test_lower_bound_never_exceeds_the_optimum_and_rules_never_beat_it():
    for sd in range(60):
        bay, h = make_bay(4, 3, sd), max_height(3, 2)
        opt = A.solve_exact(bay, h)
        assert A.blocker_count(bay) <= opt, sd
        assert all(A.run_rule(bay, h, r, sd).moves >= opt for r in A.RULES.values()), sd


def test_optimal_trace_is_valid_and_has_the_optimum_length_for_every_extra():
    for extra in (1, 2, 3, 4):
        for sd in range(15):
            bay, h = make_bay(4, 3, sd), max_height(3, extra)
            tr = A.optimal_trace(bay, h)
            assert tr.moves == A.solve_exact(bay, h) and A.check_trace(bay, h, _moves(tr)) == tr.moves, (extra, sd)


def test_lower_bound_and_optimum_do_not_depend_on_the_order_of_the_stacks():
    rng = random.Random(3)
    for sd in range(30):
        bay, h = make_bay(4, 3, sd), max_height(3, 2)
        shuffled = list(bay)
        rng.shuffle(shuffled)
        shuffled = tuple(shuffled)
        assert A.blocker_count(shuffled) == A.blocker_count(bay) and A.solve_exact(shuffled, h) == A.solve_exact(bay, h), sd


def test_lower_bound_is_invariant_under_order_preserving_renumbering():
    bay = make_bay(4, 3, 5)
    values = sorted(c for s in bay for c in s)
    renumbered = tuple(tuple(values.index(c) * 3 + 10 for c in s) for s in bay)   # 10, 13, 16, ...: gleiche Reihenfolge der Abrufe
    assert A.blocker_count(renumbered) == A.blocker_count(bay)
    assert A.initial_blockers(renumbered) == frozenset(values.index(c) * 3 + 10 for c in A.initial_blockers(bay))


def test_check_trace_rejects_rule_violations(counter):
    bay, h = counter
    with pytest.raises(ValueError):
        A.check_trace(bay, h, [(6, 1)])
    with pytest.raises(ValueError):
        A.check_trace(bay, h, [(5, 2)])
    with pytest.raises(ValueError):
        A.check_trace(bay, h, [(5, 7)])
    with pytest.raises(ValueError):
        A.check_trace(bay, h, [])
    with pytest.raises(ValueError):
        A.check_trace(((2, 3), (4, 5), (1, 6)), 2, [(6, 0)])


def test_make_bay_and_partial_bay_are_deterministic_and_valid():
    assert make_bay(4, 3, 11) == make_bay(4, 3, 11) and make_bay(4, 3, 11) != make_bay(4, 3, 12)
    assert sorted(c for s in make_bay(5, 4, 7) for c in s) == list(range(1, 21))
    assert canonical(((3, 6), (2, 4), (1, 5))) == canonical(((1, 5), (3, 6), (2, 4)))
    for h, n in ((5, 6), (5, 15), (6, 18)):
        for sd in range(30):
            bay = partial_bay(4, h, n, sd)
            assert len(bay) == 4 and all(len(s) <= h for s in bay), (h, n, sd)
            assert sorted(c for s in bay for c in s) == list(range(1, n + 1)), (h, n, sd)
            assert partial_bay(4, h, n, sd) == bay


def test_partial_bays_are_solvable_up_to_the_documented_fill():
    for sd in range(20):
        bay = partial_bay(4, 5, 15, sd)                                 # 15 = (4 - 1) * 5: die größte erlaubte Füllung
        tr = A.optimal_trace(bay, 5)
        assert A.check_trace(bay, 5, _moves(tr)) == tr.moves, sd
