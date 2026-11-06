"""Orakel-Test untergrenze-umstauen-demo (ORACLE-PLAYBOOK, DEMO-PLAYBOOK §12): Kern und angezeigte Kennzahlen gegen einen ANDEREN Rechenweg.

Orakel 1: Breitensuche über alle Buchtzustände (ungeordnete Stapel, kein Symmetriebruch, keine Untergrenze, kein Budget) liefert das Optimum.
Orakel 2: Aufzählung ALLER Hubfolgen mit genau dem optimalen Budget; daran werden die Sätze geprüft (nur Blocker werden bewegt, jeder Blocker mindestens einmal,
Zerlegung Hübe = Untergrenze + Mehrfachhübe). Die Untergrenze wird mit einer eigenen Zählung nachgerechnet (nicht aus dem Kern). Vorher am Handbeispiel
geprüft: Optimum 2 für (1, 4), (5, 2), (6, 3), keine Hubfolge mit einem Hub."""

from itertools import permutations

import uum_algorithm as A
from uum_scenario import canonical, make_bay, max_height, partial_bay


def own_blockers(bay):
    """Eigene Zählung der anfangs blockierenden Container (Nummern): irgendwo darunter steht eine kleinere Nummer."""
    return {c for s in bay for j, c in enumerate(s) if any(x < c for x in s[:j])}


def _pop(st):
    st = [list(s) for s in st]
    while True:
        items = [c for s in st for c in s]
        if not items:
            return st
        t = min(items)
        hit = [s for s in st if s and s[-1] == t]
        if not hit:
            return st
        hit[0].pop()


def bfs_optimum(bay, height):
    start = tuple(tuple(s) for s in _pop(bay))
    if not any(start):
        return 0
    frontier, seen, depth = {start}, {start}, 0
    while frontier:
        depth += 1
        nxt = set()
        for state in frontier:
            t = min(c for s in state for c in s)
            src = next(i for i, s in enumerate(state) if t in s)
            c = state[src][-1]
            for dst in range(len(state)):
                if dst == src or len(state[dst]) >= height:
                    continue
                st = [list(s) for s in state]
                st[src].pop()
                st[dst].append(c)
                new = tuple(tuple(s) for s in _pop(st))
                if not any(new):
                    return depth
                if new not in seen:
                    seen.add(new)
                    nxt.add(new)
        frontier = nxt
    raise AssertionError("keine Lösung")


def all_sequences(bay, height, budget):
    """Alle Hubfolgen [(Container, Zielstapel), ...] mit genau `budget` Hüben, die die Bucht leeren (Aufzählung, kein Memo)."""
    st = _pop(bay)
    if not any(st):
        return [[]] if budget == 0 else []
    if budget == 0:
        return []
    t = min(c for s in st for c in s)
    src = next(i for i, s in enumerate(st) if t in s)
    c = st[src][-1]
    out = []
    for dst in range(len(st)):
        if dst == src or len(st[dst]) >= height:
            continue
        nxt = [list(s) for s in st]
        nxt[src].pop()
        nxt[dst].append(c)
        out.extend([(c, dst)] + rest for rest in all_sequences(nxt, height, budget - 1))
    return out


def all_bays_3x2():
    seen = {}
    for perm in permutations(range(1, 7)):
        bay = tuple(tuple(perm[i * 2:(i + 1) * 2]) for i in range(3))
        seen.setdefault(canonical(bay), bay)
    return list(seen.values())


def test_oracle_on_the_hand_bay(mini):
    bay, h = mini
    assert bfs_optimum(bay, h) == 2 and A.solve_exact(bay, h) == 2
    assert all_sequences(bay, h, 1) == [] and len(all_sequences(bay, h, 2)) > 0
    assert A.count_sequences(bay, h, 2) == len(all_sequences(bay, h, 2))


def test_lower_bound_counts_agree_with_the_own_count():
    for sd in range(80):
        bay = make_bay(4, 3, sd)
        assert set(A.initial_blockers(bay)) == own_blockers(bay) and A.blocker_count(bay) == len(own_blockers(bay)), sd


def test_exact_solver_matches_breadth_first_search_and_the_lower_bound_is_valid():
    for stacks, layers, extra, seeds in ((3, 2, 2, 100), (4, 2, 2, 60), (3, 3, 2, 60), (3, 3, 1, 40), (4, 2, 4, 30)):
        h = max_height(layers, extra)
        for sd in range(seeds):
            bay = make_bay(stacks, layers, sd)
            opt = bfs_optimum(bay, h)
            assert A.solve_exact(bay, h) == opt, (stacks, layers, extra, sd)
            assert len(own_blockers(bay)) <= opt, (stacks, layers, extra, sd)


def test_partial_bays_match_the_breadth_first_search_and_the_bound():
    for sd in range(40):
        bay = partial_bay(4, 5, 9, sd)
        opt = bfs_optimum(bay, 5)
        assert A.solve_exact(bay, 5) == opt and len(own_blockers(bay)) <= opt, sd


def test_the_theorems_hold_for_every_optimal_sequence_of_every_3x2_bay():
    """Alle 120 Buchten 3 x 2: in JEDER optimalen Hubfolge werden nur Blocker bewegt, jeder Blocker mindestens einmal, Hübe = Untergrenze + Mehrfachhübe."""
    h = max_height(2, 2)
    bays = all_bays_3x2()
    assert len(bays) == 120
    for bay in bays:
        opt = bfs_optimum(bay, h)
        blockers = own_blockers(bay)
        for seq in all_sequences(bay, h, opt):
            moved = {}
            for c, _ in seq:
                moved[c] = moved.get(c, 0) + 1
            assert set(moved) == blockers, bay                                   # nur Blocker, und jeder mindestens einmal
            assert len(seq) == len(blockers) + sum(n - 1 for n in moved.values()), bay


def test_distribution_of_lower_bound_and_optimum_over_all_3x2_bays():
    from collections import Counter
    h = max_height(2, 2)
    table = Counter((len(own_blockers(b)), bfs_optimum(b, h)) for b in all_bays_3x2())
    assert dict(table) == {(0, 0): 15, (1, 1): 30, (1, 2): 15, (2, 2): 24, (2, 3): 20, (2, 4): 1, (3, 3): 7, (3, 4): 8}


def test_lower_bound_hit_implies_tight_fit_hit_on_all_3x2_and_a_3x3_sample():
    """Messbefund (kein Satz): Untergrenze = Optimum  =>  engste Passung = Optimum; vollständig auf 3 x 2, Stichprobe auf 3 x 3."""
    h = max_height(2, 2)
    for bay in all_bays_3x2():
        if len(own_blockers(bay)) == bfs_optimum(bay, h):
            assert A.run_rule(bay, h, A.rule_tight_fit).moves == len(own_blockers(bay)), bay
    h3 = max_height(3, 2)
    for sd in range(10000, 10300):
        bay = make_bay(3, 3, sd)
        if A.blocker_count(bay) == A.solve_exact(bay, h3):
            assert A.run_rule(bay, h3, A.rule_tight_fit).moves == A.blocker_count(bay), sd
