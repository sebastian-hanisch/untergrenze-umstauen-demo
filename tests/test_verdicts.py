"""Verdikte an von Hand gesetzten Werten (DEMO-PLAYBOOK §12): jede Zahl im Text und jede Schwelle der Art steht hier."""

import uum_algorithm as A
import uum_constants as C
import uum_evaluation as ev


def _trace(hub_list):
    """Spur mit den angegebenen Containern als Hübe (nur Container und Hubzahl zählen)."""
    return A.Trace(((),), tuple(A.Step(1, c, 0, 1, ((),)) for c in hub_list))


def _analysis(lower: int, hub_list, blockers):
    return ev.Analysis(((1,),), 4, lower, len(hub_list), len(hub_list), _trace(hub_list), tuple(blockers))


def test_bay_verdict_sorted():
    kind, text = ev.verdict_bay(_analysis(0, [], []))
    assert kind == "success" and "schon sortiert" in text and "0" in text


def test_bay_verdict_bound_hits_the_optimum():
    kind, text = ev.verdict_bay(_analysis(4, [4, 5, 6, 7], [4, 5, 6, 7]))
    assert kind == "success"
    assert "mindestens 4 Hübe nötig, und das Optimum ist 4" in text and "ohne jede Suche bewiesen optimal" in text


def test_bay_verdict_gap_names_gap_and_the_moved_again_containers():
    kind, text = ev.verdict_bay(_analysis(4, [10, 10, 4, 6, 8], [4, 6, 8, 10]))      # Optimum 5, Untergrenze 4, die 10 zweimal
    assert kind == "warning"
    assert "liegt 1 Hub unter dem Optimum: mindestens 4 Hübe, das Optimum ist 5" in text
    assert "Mehrfach bewegt werden: Container 10 (zweimal)." in text


def test_bay_verdict_gap_plural_and_several_containers():
    kind, text = ev.verdict_bay(_analysis(2, [4, 4, 4, 9, 9], [4, 9]))               # Optimum 5, Untergrenze 2
    assert "liegt 3 Hübe unter dem Optimum" in text and "Container 4 (3-mal), Container 9 (zweimal)" in text


def test_hub_table_by_hand():
    a = _analysis(3, [5, 5, 4, 6], [4, 5, 6])
    assert ev.hub_table(a) == [{"container": 4, "hubs": 1, "extra": 0}, {"container": 5, "hubs": 2, "extra": 1}, {"container": 6, "hubs": 1, "extra": 0}]
    assert a.gap == 1


def _stats(**kw):
    base = {"n": 100, "opt_mean": 5.81, "lb_mean": 4.53, "gap_mean": 1.28, "gap_max": 4, "lb_equal": 20, "valid": 100, "proven": 20, "unproven": 71, "miss": 9,
            "exceptions": 0, "bad_moves": 0, "ratio_mean": 1.32}
    base.update(kw)
    return base


def test_sample_verdict_three_states_and_thresholds():
    assert ev.verdict_sample(_stats(lb_equal=50))[0] == "success"                    # genau 50 % zählt zu „trägt“
    assert ev.verdict_sample(_stats(lb_equal=49))[0] == "info"
    assert ev.verdict_sample(_stats(lb_equal=10))[0] == "info"                       # genau 10 % zählt noch zu „teilweise“
    kind, text = ev.verdict_sample(_stats(lb_equal=9))
    assert kind == "warning" and "fast nie" in text


def test_sample_verdict_names_every_number():
    kind, text = ev.verdict_sample(_stats())
    assert "In 20 von 100 Buchten ist die Untergrenze gleich dem Optimum" in text and "1.28 Hübe darunter" in text
    assert "Optimum 5.81, Untergrenze 4.53, größte Lücke 4" in text and "nur in einem Teil der Buchten" in text


def test_validity_verdict_success_and_failure_cases():
    kind, text = ev.verdict_validity(_stats())
    assert kind == "success" and "in allen 100 Buchten" in text and "kein anfangs nicht blockierender Container" in text
    kind, text = ev.verdict_validity(_stats(valid=97))
    assert kind == "warning" and "in 3 von 100 Buchten über dem Optimum" in text
    kind, text = ev.verdict_validity(_stats(bad_moves=2))
    assert kind == "warning" and "2 Hübe an anfangs nicht blockierenden Containern" in text


def test_proof_verdict_names_counts_and_the_measurement_remark():
    kind, text = ev.verdict_proof(_stats())
    assert kind == "info"
    assert "in 20 von 100 Buchten bewiesen optimal" in text and "in 71 optimal, aber nur mit Suche zu beweisen" in text and "verfehlt das Optimum in 9" in text
    assert "In allen 100 Buchten gilt" in text and "Messbefund, kein Satz" in text
    kind, text = ev.verdict_proof(_stats(exceptions=2))
    assert kind == "warning" and "In 2 Buchten trifft die Untergrenze das Optimum, die engste Passung aber nicht" in text


def _layer_pts(a, b):
    return [{"layers": 2, "n": 100, "lb_equal": a, "gap_mean": 0.30}, {"layers": 4, "n": 100, "lb_equal": b, "gap_mean": 3.00}]


def test_layer_verdict_three_cases():
    kind, text = ev.verdict_layers(_layer_pts(70, 4), 4)
    assert kind == "warning" and "Bei 4 Stapeln ist die Untergrenze gleich dem Optimum in 70 von 100 Buchten mit 2 Lagen und in 4 von 100 mit 4 Lagen" in text
    assert "wächst von 0.30 auf 3.00 Hübe" in text and "deutlich seltener" in text
    assert ev.verdict_layers(_layer_pts(70, 60), 4)[0] == "warning"                  # genau 10 Punkte zählen als deutlich
    kind, text = ev.verdict_layers(_layer_pts(70, 61), 4)
    assert kind == "info" and "wenig" in text
    assert ev.verdict_layers(_layer_pts(10, 30), 4)[0] == "info" and "öfter" in ev.verdict_layers(_layer_pts(10, 30), 4)[1]


def _fill_pts(g1, g2):
    return [{"n_containers": 6, "fill": 30.0, "gap_mean": g1, "lb_equal": 95, "n": 100}, {"n_containers": 15, "fill": 75.0, "gap_mean": g2, "lb_equal": 4, "n": 100}]


def test_fill_verdict_threshold_is_one_hub():
    kind, text = ev.verdict_fill(_fill_pts(0.05, 2.74), 5)
    assert kind == "warning"
    assert "Höchsthöhe 5 und 4 Stapeln liegt die mittlere Lücke bei 30 % Füllgrad bei 0.05 Hüben und bei 75 % bei 2.74" in text and "in 95 bzw. 4 von 100 Buchten" in text
    assert ev.verdict_fill(_fill_pts(1.00, 2.00), 5)[0] == "warning"                  # genau ein Hub Unterschied zählt als deutlich
    kind, text = ev.verdict_fill(_fill_pts(1.00, 1.99), 5)
    assert kind == "info" and "wenig" in text


def test_single_blocker_verdict_and_the_real_numbers():
    kind, text = ev.verdict_single({"lower": 1, "optimum": 2, "mins": [1, 2, 3], "one_hub_solutions": 0})
    assert kind == "warning"
    assert "die Untergrenze ist 1, und das Optimum ist 2" in text and "kleinsten Nummern der drei Stapel sind 1, 2, 3" in text and "Hubfolgen mit einem Hub, die die Bucht leeren: 0" in text
    assert ev.verdict_single({"lower": 2, "optimum": 2, "mins": [1], "one_hub_solutions": 0})[0] == "info"
    d = ev.single_blocker()
    assert (d["lower"], d["optimum"], d["one_hub_solutions"], d["mins"]) == (1, 2, 0, [1, 2, 3])
    assert C.SINGLE_BAY == d["bay"]
