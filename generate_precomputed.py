"""Erzeugt uum_bands.json: Kennzahlen der 100 festen Buchten (Seeds 0 bis 99) für zwei Kurven.

    python generate_precomputed.py

"lagen": Stapel (3 bis 5) x Lagen (2 bis 4), volle Buchten, Zuschlag 2 (wie Stück 1 der Reihe).
"fuell": Zufallsbuchten mit ungleich hohen Stapeln, 4 Stapel, Höchsthöhe 5 und 6, N Container (Zahlen in uum_constants.FILL_CELLS).

Rechenzeit rund eine halbe Minute. Dieselben Funktionen wie die App (`uum_evaluation.sample_rows`, `partial_rows`, `cell_stats`);
die Datei speichert nur Kennzahlen, keine Zeilen. tests/test_precomputed.py rechnet einzelne Zellen neu und vergleicht."""

import json
import sys

import uum_constants as C
import uum_evaluation as ev

sys.stdout.reconfigure(encoding="utf-8")


def main():
    bands = {"lagen": {}, "fuell": {}}
    for stacks in C.STACK_CURVE:
        for layers in C.LAYER_CURVE:
            bands["lagen"][ev.layer_key(stacks, layers)] = ev.cell_stats(ev.sample_rows(stacks, layers, C.DEFAULT_EXTRA))
            print(f"{stacks} Stapel x {layers} Lagen: fertig", flush=True)
    for height, cells in C.FILL_CELLS.items():
        for n in cells:
            bands["fuell"][ev.fill_key(height, n)] = ev.cell_stats(ev.partial_rows(C.FILL_STACKS, height, n))
            print(f"Höhe {height}, N {n}: fertig", flush=True)
    ev.BANDS_FILE.write_text(json.dumps(bands, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print("geschrieben:", ev.BANDS_FILE.name)


if __name__ == "__main__":
    main()
