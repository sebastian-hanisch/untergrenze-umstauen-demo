"""Abbildungen: Farben je Rolle des Containers, feste Achsen, Kategorienachse des Histogramms, Beschriftungen."""

import uum_constants as C
import uum_evaluation as ev
import uum_visualization as V


def _cell_colors(fig):
    out = {}
    for tr in fig.data:
        for txt, color in zip(tr.text, tr.marker.color):
            if txt:
                out[int(txt)] = color
    return out


def test_bay_colours_by_role(mini):
    bay, h = mini
    cols = _cell_colors(V.build_bay(bay, h, target=1))
    assert cols[1] == C.COLOR_TARGET and cols[4] == C.COLOR_BLOCK            # nächster Abruf grün, die 4 blockiert die 1
    assert cols[5] == cols[6] == cols[2] == cols[3] == C.COLOR_CELL           # die übrigen blockieren nichts (2 < 5, 3 < 6)
    assert sorted(_cell_colors(V.build_bay(bay, h))) == [1, 2, 3, 4, 5, 6] and len(V.build_bay(bay, h).data) == h


def test_blocker_cells_by_position_and_agreement_with_the_kernel():
    assert V.blocker_cells(((1, 4), (5, 2), (6, 3))) == {(0, 1)}
    assert V.blocker_cells(((3, 6), (2, 4), (1, 5))) == {(0, 1), (1, 1), (2, 1)}
    assert V.blocker_cells(((5, 3), (2, 1))) == set()
    from uum_scenario import make_bay
    for sd in range(20):
        bay = make_bay(4, 3, sd)
        assert len(V.blocker_cells(bay)) == len(__import__("uum_algorithm").initial_blockers(bay)) == __import__("uum_algorithm").blocker_count(bay)


def test_axes_are_locked_in_every_figure():
    a = ev.analyse(ev.Settings())
    stats = ev.cell_stats(ev.sample_rows(3, 2, 2))
    bands = ev.load_bands()
    figs = [V.build_bay(a.bay, a.height), V.build_gap_histogram(ev.gap_histogram(ev.sample_rows(3, 2, 2))), V.build_proof(stats),
            V.build_layer_curve(ev.layer_points(bands, 4)), V.build_fill_curve({h: ev.fill_points(bands, h) for h in C.FILL_CELLS})]
    for fig in figs:
        assert fig.layout.xaxis.fixedrange is True and fig.layout.yaxis.fixedrange is True


def test_gap_histogram_axis_is_categorical():
    fig = V.build_gap_histogram([60, 30, 7, 2, 1])
    assert fig.layout.xaxis.type == "category" and list(fig.data[0].x) == ["0 (trifft)", "1", "2", "3", "4 oder mehr"] and list(fig.data[0].y) == [60, 30, 7, 2, 1]


def test_proof_figure_stacks_three_categories_up_to_n():
    stats = {"n": 100, "proven": 20, "unproven": 71, "miss": 9}
    fig = V.build_proof(stats)
    assert [list(t.x)[0] for t in fig.data] == [20, 71, 9] and fig.layout.barmode == "stack" and list(fig.layout.xaxis.range) == [0, 100]


def test_layer_and_fill_curves_carry_the_stored_numbers():
    bands = ev.load_bands()
    fig = V.build_layer_curve(ev.layer_points(bands, 4))
    assert list(fig.data[0].x) == [2, 3, 4] and list(fig.data[0].y) == [70.0, 20.0, 4.0]
    fig = V.build_fill_curve({h: ev.fill_points(bands, h) for h in C.FILL_CELLS})
    assert [t.name for t in fig.data] == ["Höchsthöhe 5", "Höchsthöhe 6"] and len(fig.data[1].x) == 5
    assert [round(y, 2) for y in fig.data[0].y] == [0.05, 0.50, 1.29, 2.74]
