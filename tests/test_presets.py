"""Presets: Vollständigkeit, gültige Werte, Standard-Preset = Standardeinstellungen; Eigenschaften der Sonderbuchten und der vorberechneten Kurven."""

import pytest

import uum_algorithm as A
import uum_constants as C
import uum_evaluation as ev
import uum_presets as P
from uum_scenario import canonical, make_bay, max_height


def test_every_preset_has_help_and_all_keys():
    assert set(C.PRESETS) == set(C.PRESET_HELP)
    for name, preset in C.PRESETS.items():
        assert set(preset) == set(P.PRESET_KEYS), name
        assert C.PRESET_HELP[name]


def test_preset_values_are_inside_the_slider_bounds():
    for preset in C.PRESETS.values():
        assert C.STACKS_MIN <= preset["stacks"] <= C.STACKS_MAX and C.LAYERS_MIN <= preset["layers"] <= C.LAYERS_MAX
        assert C.EXTRA_MIN <= preset["extra"] <= C.EXTRA_MAX and 0 <= preset["seed"] <= C.SEED_MAX


def test_default_preset_equals_the_default_settings():
    p = C.PRESETS[next(iter(C.PRESETS))]
    assert ev.Settings(p["stacks"], p["layers"], p["extra"], p["seed"]) == ev.Settings()


def test_setting_specs_cover_every_preset_key():
    assert set(P.PRESET_KEYS.values()) == set(P.SETTING_SPECS)


def _analysis(name):
    p = C.PRESETS[name]
    return ev.analyse(ev.Settings(p["stacks"], p["layers"], p["extra"], p["seed"]))


def test_everyday_preset_has_a_gap_of_one():
    a = _analysis("Alltag (4 Stapel, 3 Lagen)")
    assert (a.lower, a.optimum, a.gap) == (4, 5, 1)


def test_exact_preset_has_a_hit_with_blockers():
    a = _analysis("Die Untergrenze trifft")
    assert a.lower == a.optimum and a.lower >= 4


def test_gap_preset_has_a_gap_of_at_least_five():
    a = _analysis("Große Lücke (4 Stapel, 4 Lagen)")
    assert a.gap >= 5 and (a.lower, a.optimum) == (6, 11)


def test_single_blocker_preset_is_the_hand_bay():
    p = C.PRESETS["Der einzelne Blocker"]
    bay = make_bay(p["stacks"], p["layers"], p["seed"])
    assert canonical(bay) == canonical(C.SINGLE_BAY)
    a = _analysis("Der einzelne Blocker")
    assert (a.lower, a.optimum) == (1, 2) and A.count_sequences(bay, a.height, 1) == 0


def test_the_sorted_case_is_a_valid_input_of_every_section():
    a = ev.analyse(ev.Settings(3, 2, 2, 0))                              # Bucht 0 bei 3 x 2 ist schon sortiert (Stück 1)
    assert a.optimum == 0 and ev.hub_table(a) == [] and ev.verdict_bay(a)[0] == "success"


@pytest.mark.parametrize("cell", [(3, 2), (4, 3), (3, 4)])
def test_stored_layer_bands_equal_a_fresh_computation(cell):
    stored = ev.load_bands()["lagen"][ev.layer_key(*cell)]
    fresh = ev.cell_stats(ev.sample_rows(*cell, C.DEFAULT_EXTRA))
    assert _same(stored, fresh)


@pytest.mark.parametrize("cell", [(5, 6), (5, 15), (6, 12)])
def test_stored_fill_bands_equal_a_fresh_computation(cell):
    stored = ev.load_bands()["fuell"][ev.fill_key(*cell)]
    fresh = ev.cell_stats(ev.partial_rows(C.FILL_STACKS, *cell))
    assert _same(stored, fresh)


def _same(stored, fresh):
    assert set(stored) == set(fresh)
    for k, v in stored.items():
        assert v == pytest.approx(fresh[k]), k
    return True


def test_every_band_cell_exists():
    bands = ev.load_bands()
    assert set(bands["lagen"]) == {ev.layer_key(s, l) for s in C.STACK_CURVE for l in C.LAYER_CURVE}
    assert set(bands["fuell"]) == {ev.fill_key(h, n) for h, cells in C.FILL_CELLS.items() for n in cells}
    assert all(n <= (C.FILL_STACKS - 1) * h for h, cells in C.FILL_CELLS.items() for n in cells)


def test_sample_rows_use_the_fixed_seeds_and_are_consistent():
    rows = ev.sample_rows(3, 2, 2)
    assert [r["seed"] for r in rows] == list(C.SAMPLE_SEEDS)
    for r in rows:
        assert r["lb"] <= r["opt"] <= r["tight"] and r["bad"] == 0
    st = ev.cell_stats(rows)
    assert st["valid"] == st["n"] == 100 and st["proven"] + st["unproven"] + st["miss"] == 100
    assert st["lb_equal"] == sum(r["lb"] == r["opt"] for r in rows)


def test_the_curves_follow_their_orders():
    bands = ev.load_bands()
    assert [p["layers"] for p in ev.layer_points(bands, 4)] == list(C.LAYER_CURVE)
    pts = ev.fill_points(bands, 6)
    assert [p["n_containers"] for p in pts] == list(C.FILL_CELLS[6]) and [round(p["fill"]) for p in pts] == [25, 38, 50, 62, 75]
