"""Konstanten: Regler-Grenzen, feste Annahmen, Farben und Presets."""

STACKS_MIN, STACKS_MAX, DEFAULT_STACKS = 3, 5, 4          # Zahl der Stapel
LAYERS_MIN, LAYERS_MAX, DEFAULT_LAYERS = 2, 4, 3          # Anfangsfüllung je Stapel (Lagen)
EXTRA_MIN, EXTRA_MAX, DEFAULT_EXTRA = 1, 4, 2             # Platz: Höchsthöhe = Lagen + Zuschlag (Standard 2 wie in Stück 1)
SEED_MAX = 999999

SAMPLE_SEEDS = tuple(range(100))                          # feste Buchten für die Stichprobe: nie eine einzelne Bucht als Befund
SHARE_STRONG, SHARE_WEAK = 50.0, 10.0                     # Verdikt „trägt“: Untergrenze = Optimum in mindestens 50 % / mindestens 10 % der Buchten
CURVE_STEP = 10.0                                         # Lagenkurve: so viele Prozentpunkte Unterschied zählen als deutlich
FILL_GAP_STEP = 1.0                                       # Füllgradkurve: so viele Hübe mehr Lücke zählen als deutlich
LAYER_CURVE = (2, 3, 4)                                   # Lagen der vorberechneten Kurve
STACK_CURVE = (3, 4, 5)                                   # Stapelzahlen der vorberechneten Kurve (Zuschlag 2)
FILL_STACKS = 4                                           # Füllgradkurve: Zufallsbuchten mit 4 Stapeln
FILL_CELLS = {5: (6, 9, 12, 15), 6: (6, 9, 12, 15, 18)}   # Höchsthöhe -> Zahl der Container; immer <= (Stapel - 1) * Höchsthöhe

COLOR_CELL = "#7a8fa6"
COLOR_BLOCK = "#b5545a"        # blockierend (liegt über einem früher abzurufenden)
COLOR_TARGET = "#2F6B65"       # nächster Abruf
COLOR_PROVEN, COLOR_UNPROVEN, COLOR_MISS = "#2F6B65", "#4c78a8", "#b5545a"
COLOR_LINES = ("#2F6B65", "#4c78a8", "#d9822b")

# Sonderbuchten (in der Vormessung gefunden, Eigenschaften in tests/test_presets.py festgehalten)
EVERYDAY_SEED = 11     # 4 Stapel x 3 Lagen, Zuschlag 2: Untergrenze 4, Optimum 5
EXACT_SEED = 2         # 4 x 3, Zuschlag 2: Untergrenze 4 = Optimum 4
GAP_SEED = 2           # 4 x 4, Zuschlag 2: Untergrenze 6, Optimum 11
SINGLE_SEED = 223      # 3 x 2: der einzelne Blocker (1, 4), (5, 2), (6, 3) bis auf Vertauschen der Stapel: Untergrenze 1, Optimum 2
SINGLE_BAY = ((1, 4), (5, 2), (6, 3))

PRESETS = {
    "Alltag (4 Stapel, 3 Lagen)": {"stacks": 4, "layers": 3, "extra": DEFAULT_EXTRA, "seed": EVERYDAY_SEED},
    "Die Untergrenze trifft": {"stacks": 4, "layers": 3, "extra": DEFAULT_EXTRA, "seed": EXACT_SEED},
    "Große Lücke (4 Stapel, 4 Lagen)": {"stacks": 4, "layers": 4, "extra": DEFAULT_EXTRA, "seed": GAP_SEED},
    "Der einzelne Blocker": {"stacks": 3, "layers": 2, "extra": DEFAULT_EXTRA, "seed": SINGLE_SEED},
}
PRESET_HELP = {
    "Alltag (4 Stapel, 3 Lagen)": "12 Container: die Untergrenze liegt einen Hub unter dem Optimum.",
    "Die Untergrenze trifft": "Eine Bucht, in der die Untergrenze genau das Optimum ist: ohne jede Suche bewiesen.",
    "Große Lücke (4 Stapel, 4 Lagen)": "16 Container: die Untergrenze liegt mindestens 5 Hübe unter dem Optimum.",
    "Der einzelne Blocker": "3 Stapel mit je 2 Containern, ein einziger blockierender Container, und trotzdem braucht es 2 Hübe.",
}
