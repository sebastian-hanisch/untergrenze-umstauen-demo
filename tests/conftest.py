"""Gemeinsame Fixtures: die Mini-Buchten, an denen jede Einheit von Hand geprüft wird (DEMO-PLAYBOOK §1b)."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


@pytest.fixture
def mini():
    """Der einzelne Blocker: 3 Stapel mit je 2 Containern, Höchsthöhe 4, Stapel von unten nach oben (1, 4), (5, 2), (6, 3).

    Handrechnung: Blockierend ist nur die 4 (über der 1); die 2 liegt über der 5, aber 2 < 5, die 3 liegt über der 6, aber 3 < 6. Untergrenze 1.
    Ein Hub genügt nicht: Setzt man die 4 auf Stapel 2, liegt sie über der 5 und der 2 (blockiert die 2), auf Stapel 3 über der 6 und der 3
    (blockiert die 3). Das Optimum ist 2."""
    return ((1, 4), (5, 2), (6, 3)), 4


@pytest.fixture
def counter():
    """Das kleinste Gegenbeispiel aus Stück 1: (3, 6), (2, 4), (1, 5), Höchsthöhe 4. Blockierend sind 6, 4 und 5: Untergrenze 3, Optimum 4."""
    return ((3, 6), (2, 4), (1, 5)), 4
