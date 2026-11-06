"""Inhalt der App: Kennzahlen der Presets, Tabelle der Hübe, Verdikte, Permalink (AppTest, DEMO-PLAYBOOK §5)."""

import os
from pathlib import Path

from streamlit.testing.v1 import AppTest

import uum_constants as C

APP = str(Path(__file__).resolve().parent.parent / "app.py")
TIMEOUT = int(os.environ.get("APPTEST_TIMEOUT", "300"))


def _run(at=None):
    if at is None:                                              # nicht `at or ...`: ein ungelaufener AppTest ist falsy
        at = AppTest.from_file(APP, default_timeout=TIMEOUT)
    at.run()
    assert not at.exception, [str(e) for e in at.exception]
    return at


def _metrics(at):
    return {m.label: m.value for m in at.metric}


def _preset(at, name):
    at.sidebar.button(key=f"preset_{name}").click().run()
    assert not at.exception, [str(e) for e in at.exception]
    return at


def _texts(at):
    return " ".join(md.value for md in at.markdown)


def test_default_bay_shows_the_everyday_numbers_and_the_table():
    at = _run()
    m = _metrics(at)
    assert m["Untergrenze (mindestens)"] == "4" and m["Optimum (bewiesen)"] == "5" and m["Lücke (Mehrfachhübe)"] == "1"
    text = _texts(at)
    assert "| Container | Hübe | davon Mehrfachhübe |" in text and "| **Summe** | **5** | **1** |" in text
    assert any("Untergrenze 4 + Mehrfachhübe 1 = Optimum 5." in c.value for c in at.caption)
    assert any("liegt 1 Hub unter dem Optimum: mindestens 4 Hübe, das Optimum ist 5" in w.value for w in at.warning)


def test_exact_preset_says_the_bound_is_proven():
    at = _preset(_run(), "Die Untergrenze trifft")
    m = _metrics(at)
    assert m["Untergrenze (mindestens)"] == m["Optimum (bewiesen)"] == "4" and m["Lücke (Mehrfachhübe)"] == "0"
    assert any("Die Untergrenze trifft" in s.value and "ohne jede Suche bewiesen optimal" in s.value for s in at.success)
    assert "| **Summe** | **4** | **0** |" in _texts(at)


def test_gap_preset_shows_a_large_gap():
    at = _preset(_run(), "Große Lücke (4 Stapel, 4 Lagen)")
    m = _metrics(at)
    assert m["Untergrenze (mindestens)"] == "6" and m["Optimum (bewiesen)"] == "11" and m["Lücke (Mehrfachhübe)"] == "5"
    assert any("liegt 5 Hübe unter dem Optimum" in w.value for w in at.warning)


def test_single_blocker_preset_shows_one_blocker_and_two_hubs():
    at = _preset(_run(), "Der einzelne Blocker")
    m = _metrics(at)
    assert m["Untergrenze (mindestens)"] == "1" and m["Optimum (bewiesen)"] == "2"
    assert "| 4 | 2 | 1 |" in _texts(at) and "| **Summe** | **2** | **1** |" in _texts(at)


def test_sorted_bay_has_no_table_and_says_so():
    at = AppTest.from_file(APP, default_timeout=TIMEOUT)
    at.query_params.update({"stacks": "3", "layers": "2", "seed": "0"})
    _run(at)
    assert any("kein Container blockiert" in c.value.lower() or "Kein Container blockiert" in c.value for c in at.caption)
    assert any("schon sortiert" in s.value for s in at.success)
    assert "| Container | Hübe |" not in _texts(at)


def test_space_slider_changes_the_numbers_and_keeps_the_lower_bound():
    at = _run()
    at.sidebar.slider(key="extra_slider").set_value(1).run()
    assert not at.exception
    m = _metrics(at)
    assert m["Untergrenze (mindestens)"] == "4"                                # die Untergrenze hängt nicht vom Platz ab
    assert at.sidebar.slider(key="extra_slider").value == 1


def test_permalink_is_clamped_to_the_slider_bounds():
    at = AppTest.from_file(APP, default_timeout=TIMEOUT)
    at.query_params["stacks"] = "99"
    at.query_params["layers"] = "-4"
    at.query_params["extra"] = "17"
    _run(at)
    assert at.sidebar.slider(key="stacks_slider").value == C.STACKS_MAX
    assert at.sidebar.slider(key="layers_slider").value == C.LAYERS_MIN
    assert at.sidebar.slider(key="extra_slider").value == C.EXTRA_MAX


def test_sections_name_the_default_cell_numbers():
    at = _run()
    bodies = " ".join(e.value for kind in (at.success, at.info, at.warning) for e in kind)
    assert "In 20 von 100 Buchten ist die Untergrenze gleich dem Optimum; im Mittel liegt sie 1.28 Hübe darunter" in bodies
    assert "in 20 von 100 Buchten bewiesen optimal" in bodies and "in 71 optimal, aber nur mit Suche zu beweisen" in bodies
    assert "70 von 100 Buchten mit 2 Lagen und in 4 von 100 mit 4 Lagen" in bodies
    assert "Es blockiert nur ein Container, die Untergrenze ist 1, und das Optimum ist 2." in bodies
    assert any("1 Ausnahme in 900 Buchten" in c.value for c in at.caption)
