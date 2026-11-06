"""JEDE Zahl aus dem README wird hier nachgerechnet (DEMO-PLAYBOOK §4): über dieselben Auswertungsfunktionen wie in der App, über die festen Buchten 0 bis 99
je Zelle, nie über eine einzelne Bucht."""

from functools import lru_cache

import pytest

import uum_algorithm as A
import uum_constants as C
import uum_evaluation as ev
from uum_scenario import make_bay, max_height

BANDS = ev.load_bands()


def lay(s, l):
    return BANDS["lagen"][ev.layer_key(s, l)]


# Zelle: Optimum, Untergrenze, Optimum / Untergrenze, Lücke, größte Lücke, Untergrenze = Optimum, bewiesen, optimal ohne Beweis, verfehlt
GRID = {
    (3, 2): (1.74, 1.41, 1.24, 0.33, 1, 67, 67, 31, 2),
    (4, 2): (2.25, 1.95, 1.16, 0.30, 1, 70, 70, 30, 0),
    (5, 2): (2.83, 2.51, 1.13, 0.32, 1, 68, 68, 32, 0),
    (3, 3): (5.05, 3.53, 1.42, 1.52, 4, 19, 19, 68, 13),
    (4, 3): (5.81, 4.53, 1.32, 1.28, 4, 20, 20, 71, 9),
    (5, 3): (6.94, 5.69, 1.22, 1.25, 4, 25, 25, 70, 5),
    (3, 4): (8.92, 5.68, 1.59, 3.24, 8, 1, 1, 60, 39),
    (4, 4): (10.44, 7.44, 1.42, 3.00, 7, 4, 4, 48, 48),
    (5, 4): (12.52, 9.49, 1.32, 3.03, 7, 3, 3, 57, 40),
}


@pytest.mark.parametrize("cell", list(GRID))
def test_readme_table_cell(cell):
    opt, lb, ratio, gap, gap_max, equal, proven, unproven, miss = GRID[cell]
    st = lay(*cell)
    assert st["n"] == 100 and st["valid"] == 100
    assert round(st["opt_mean"], 2) == opt and round(st["lb_mean"], 2) == lb and round(st["ratio_mean"], 2) == ratio
    assert round(st["gap_mean"], 2) == gap and st["gap_max"] == gap_max and st["lb_equal"] == equal
    assert (st["proven"], st["unproven"], st["miss"]) == (proven, unproven, miss)


def test_the_bound_is_valid_in_every_cell_and_no_non_blocker_is_ever_moved():
    for cell in GRID:
        st = lay(*cell)
        assert st["valid"] == st["n"] and st["bad_moves"] == 0, cell


def test_implication_has_no_exception_in_the_equal_height_family():
    assert all(lay(*cell)["exceptions"] == 0 for cell in GRID)
    # in den Zufallsbuchten gibt es eine Ausnahme (Höchsthöhe 5, 12 Container)
    assert ev.fill_exceptions(BANDS) == (1, 900) and BANDS["fuell"][ev.fill_key(5, 12)]["exceptions"] == 1


def test_bound_hits_the_optimum_more_often_with_fewer_layers():
    for s in (3, 4, 5):
        eq = [lay(s, l)["lb_equal"] for l in (2, 3, 4)]
        assert eq[0] > eq[1] > eq[2], (s, eq)
    assert [lay(4, l)["lb_equal"] for l in (2, 3, 4)] == [70, 20, 4]
    assert [round(lay(4, l)["gap_mean"], 2) for l in (2, 3, 4)] == [0.30, 1.28, 3.00]


# Platz (4 Stapel, gleich hohe Stapel): Zuschlag -> (Optimum, Lücke, Untergrenze = Optimum, engste Passung optimal)
PLATZ = {
    3: {1: (5.86, 1.33, 18, 84), 2: (5.81, 1.28, 20, 91), 3: (5.81, 1.28, 20, 93), 4: (5.81, 1.28, 20, 93)},
    4: {1: (10.89, 3.45, 3, 47), 2: (10.44, 3.00, 4, 52), 3: (10.39, 2.95, 4, 53), 4: (10.39, 2.95, 4, 53)},
}


@lru_cache(maxsize=None)
def _platz(layers, extra):
    return ev.cell_stats(ev.sample_rows(4, layers, extra))


@pytest.mark.parametrize("layers,extra", [(l, e) for l in (3, 4) for e in (1, 2, 3, 4)])
def test_readme_space_table(layers, extra):
    opt, gap, equal, tight_opt = PLATZ[layers][extra]
    st = _platz(layers, extra)
    assert round(st["opt_mean"], 2) == opt and round(st["gap_mean"], 2) == gap and st["lb_equal"] == equal
    assert st["proven"] + st["unproven"] == tight_opt


# Füllgrad (4 Stapel, Zufallsbuchten): (Höchsthöhe, Container) -> (Optimum, Untergrenze, Lücke, größte Lücke, Untergrenze = Optimum, engste Passung optimal)
FUELL = {
    (5, 6): (1.32, 1.27, 0.05, 1, 95, 100), (5, 9): (3.69, 3.19, 0.50, 3, 61, 99), (5, 12): (6.15, 4.86, 1.29, 4, 25, 87), (5, 15): (9.92, 7.18, 2.74, 7, 4, 71),
    (6, 6): (1.32, 1.27, 0.05, 1, 95, 100), (6, 9): (3.75, 3.24, 0.51, 3, 60, 99), (6, 12): (6.16, 4.88, 1.28, 4, 29, 86), (6, 15): (9.76, 7.15, 2.61, 6, 9, 70),
    (6, 18): (13.92, 9.37, 4.55, 9, 2, 42),
}


@pytest.mark.parametrize("cell", list(FUELL))
def test_readme_fill_table(cell):
    opt, lb, gap, gap_max, equal, tight_opt = FUELL[cell]
    st = BANDS["fuell"][ev.fill_key(*cell)]
    assert st["n"] == 100 and st["valid"] == 100
    assert round(st["opt_mean"], 2) == opt and round(st["lb_mean"], 2) == lb and round(st["gap_mean"], 2) == gap
    assert st["gap_max"] == gap_max and st["lb_equal"] == equal and st["proven"] + st["unproven"] == tight_opt


def test_fill_gap_grows_with_the_fill_in_both_heights():
    for h in (5, 6):
        gaps = [p["gap_mean"] for p in ev.fill_points(BANDS, h)]
        assert gaps == sorted(gaps) and gaps[-1] - gaps[0] >= C.FILL_GAP_STEP, h
    assert [round(p["fill"]) for p in ev.fill_points(BANDS, 5)] == [30, 45, 60, 75]


def test_the_hub_decomposition_per_blocker_in_the_optimal_sequences():
    """Zerlegungstabelle (README, Teil A): Hübe je Blocker, Anteil der Blocker mit mindestens zwei Hüben, größte Hubzahl eines Containers."""
    expected = {(3, 3): (1.42, 41, 3), (4, 3): (1.32, 30, 3), (3, 4): (1.59, 51, 4), (4, 4): (1.42, 40, 3), (5, 4): (1.32, 31, 3)}
    for (s, l), (per, share2, maxm) in expected.items():
        h = max_height(l, 2)
        pers, shares, maxs = [], [], []
        for sd in C.SAMPLE_SEEDS:
            bay = make_bay(s, l, sd)
            tr = A.optimal_trace(bay, h)
            counts = A.hub_counts(tr)
            lb = A.blocker_count(bay)
            pers.append(tr.moves / lb)
            shares.append(sum(1 for n in counts.values() if n >= 2) / lb)
            maxs.append(max(counts.values()))
        assert round(sum(pers) / 100, 2) == per and round(sum(shares)) == share2 and max(maxs) == maxm, (s, l)
