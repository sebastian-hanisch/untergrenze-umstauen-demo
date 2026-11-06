"""Plotly-Abbildungen. Alle Achsen sind gesperrt (fixedrange), damit Touch-Geräte beim Scrollen nicht am Diagramm hängen bleiben."""

import plotly.graph_objects as go

import uum_algorithm as A
import uum_constants as C


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height=340):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", y=-0.25), plot_bgcolor="rgba(0,0,0,0)")
    return lock_axes(fig)


def blocker_cells(stacks) -> set:
    """Container, die über einem früher abzurufenden im selben Stapel liegen (Position (Stapel, Lage))."""
    out = set()
    for i, s in enumerate(stacks):
        lowest = A.INF
        for j, c in enumerate(s):
            if c > lowest:
                out.add((i, j))
            else:
                lowest = c
    return out


def build_bay(stacks, height, target=None):
    """Die Bucht als Säulen: je Lage ein Balken mit der Abrufnummer. Rot: blockiert einen früher abzurufenden, grün: nächster Abruf
    (`target`, eine Abrufnummer oder None), grau-blau: übrige."""
    blockers = blocker_cells(stacks)
    fig = go.Figure()
    xs = list(range(len(stacks)))
    for j in range(height):
        ys, colors, texts = [], [], []
        for i, s in enumerate(stacks):
            if j < len(s):
                c = s[j]
                ys.append(1)
                texts.append(str(c))
                colors.append(C.COLOR_TARGET if c == target else C.COLOR_BLOCK if (i, j) in blockers else C.COLOR_CELL)
            else:
                ys.append(0)
                texts.append("")
                colors.append(C.COLOR_CELL)
        fig.add_trace(go.Bar(x=xs, y=ys, base=j, marker_color=colors, text=texts, textposition="inside", insidetextanchor="middle",
                             textfont=dict(color="#ffffff", size=16), width=0.78, showlegend=False,
                             hovertemplate="Abruf %{text}<extra></extra>", marker_line=dict(width=0)))
    fig.update_layout(barmode="overlay")
    fig.add_hline(y=height, line_dash="dot", line_color="rgba(128,128,128,0.7)", annotation_text="Höchsthöhe", annotation_position="top left")
    fig.update_xaxes(tickvals=xs, ticktext=[f"Stapel {i + 1}" for i in xs], showgrid=False)
    fig.update_yaxes(range=[0, height + 0.35], showticklabels=False, showgrid=False, zeroline=False)
    return _base(fig, height=48 * height + 90)


def build_gap_histogram(counts):
    """Zahl der Buchten mit Lücke 0, 1, 2, 3 und 4 oder mehr Hüben zwischen Untergrenze und Optimum."""
    labels = ["0 (trifft)", "1", "2", "3", "4 oder mehr"]
    fig = go.Figure(go.Bar(x=labels, y=counts, marker_color=[C.COLOR_PROVEN] + [C.COLOR_LINES[1]] * (len(counts) - 1),
                           hovertemplate="Lücke %{x}: %{y} Buchten<extra></extra>"))
    fig.update_xaxes(title_text="Hübe zwischen Untergrenze und Optimum", type="category")   # sonst liest Plotly „1“, „2“ als Zahlen
    fig.update_yaxes(title_text="Zahl der Buchten")
    return _base(fig)


def build_proof(stats):
    """Beweisquote: ein gestapelter Balken aus bewiesen optimal / optimal, aber nur mit Suche zu beweisen / verfehlt das Optimum."""
    fig = go.Figure()
    for label, key, color in (("bewiesen optimal (trifft die Untergrenze)", "proven", C.COLOR_PROVEN), ("optimal, nur mit Suche zu beweisen", "unproven", C.COLOR_UNPROVEN),
                              ("verfehlt das Optimum", "miss", C.COLOR_MISS)):
        fig.add_trace(go.Bar(y=["engste Passung"], x=[stats[key]], name=label, orientation="h", marker_color=color,
                             text=[str(stats[key])], textposition="inside", textfont=dict(color="#ffffff", size=14),
                             hovertemplate="%{x} Buchten<extra>%{fullData.name}</extra>"))
    fig.update_layout(barmode="stack")
    fig.update_xaxes(title_text="Zahl der Buchten", range=[0, stats["n"]])
    fig.update_yaxes(showticklabels=False)
    fig = _base(fig, height=230)
    fig.update_layout(legend=dict(orientation="h", y=1.05, yanchor="bottom"), margin=dict(l=10, r=10, t=70, b=10))   # Legende oben: unten läge sie über dem Achsentitel
    return fig


def build_layer_curve(points):
    """Anteil der Buchten, in denen die Untergrenze gleich dem Optimum ist, über die Zahl der Lagen."""
    xs = [p["layers"] for p in points]
    fig = go.Figure(go.Scatter(x=xs, y=[100.0 * p["lb_equal"] / p["n"] for p in points], mode="lines+markers", name="Untergrenze = Optimum",
                               line=dict(color=C.COLOR_LINES[0], width=3), hovertemplate="%{x} Lagen: %{y:.0f} % der Buchten<extra></extra>"))
    fig.update_xaxes(title_text="Lagen je Stapel", tickvals=xs)
    fig.update_yaxes(title_text="Buchten mit Untergrenze = Optimum (%)", range=[-3, 103])
    return _base(fig)


def build_fill_curve(curves):
    """Mittlere Lücke (Hübe) über den Füllgrad, eine Linie je Höchsthöhe. `curves`: {Höchsthöhe: Punkte aus fill_points}."""
    fig = go.Figure()
    for idx, (height, pts) in enumerate(curves.items()):
        fig.add_trace(go.Scatter(x=[p["fill"] for p in pts], y=[p["gap_mean"] for p in pts], mode="lines+markers", name=f"Höchsthöhe {height}",
                                 line=dict(color=C.COLOR_LINES[idx % len(C.COLOR_LINES)], width=3),
                                 hovertemplate="%{x:.0f} % gefüllt: Lücke %{y:.2f} Hübe<extra>%{fullData.name}</extra>"))
    fig.update_xaxes(title_text="Füllgrad (% der Plätze)")
    fig.update_yaxes(title_text="mittlere Lücke (Hübe)", rangemode="tozero")
    return _base(fig)
