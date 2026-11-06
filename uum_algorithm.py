"""Kern: Umstauen in einer Bucht (Block Relocation Problem, restricted).

Eine Bucht besteht aus Stapeln (Tupel von unten nach oben). Die Abrufnummer 1 kommt zuerst dran (kleiner = früher);
nur der oberste Container eines Stapels ist erreichbar. Liegt die nächste Nummer nicht oben, werden die Container
darüber nacheinander (oberster zuerst) auf andere Stapel gesetzt, jeder Hub kostet 1. *Restricted*: Es werden nur
Container über dem gesuchten bewegt. Liegt die nächste Nummer oben, wird sie ohne Kosten abgerufen.

Bausteine (jeder einzeln geprüft, DEMO-PLAYBOOK §1b):
  autopop            ruft ab, was oben liegt und dran ist
  blocker_count      Untergrenze: Container über einem früher abzurufenden im selben Stapel
  rule_*             Zielstapel-Regeln für einen Blocker (engste Passung, niedrigster Stapel, Zufall)
  run_rule           eine Regel auf eine Bucht anwenden, mit Spur (jeder Hub)
  solve_exact        Optimum: Suche über Buchtzustände mit Untergrenze, Zustandsmerken, Symmetriebruch
  optimal_trace      eine optimale Hubfolge
  check_trace        unabhängiger Prüfer: spielt eine Spur nach und zählt
  initial_blockers   die anfangs blockierenden Container (Positionen und Nummern)
  hub_counts         Hübe je Container in einer Spur; Mehrfachhübe = Hübe minus Zahl der bewegten Container
  count_sequences    Zahl der Hubfolgen mit genau b Hüben, die die Bucht leeren (für kleine Buchten)

Kern aus Stück 1 der Reihe (umstauen-regeln-demo) kopiert, ergänzt um die Zerlegung Hübe = Untergrenze + Mehrfachhübe (Stück 2).
"""

import random
from dataclasses import dataclass

INF = 10 ** 9


@dataclass(frozen=True)
class Step:
    """Ein Hub: `container` lag über `target` auf Stapel `src` und kommt auf Stapel `dst` (0-basiert)."""
    target: int
    container: int
    src: int
    dst: int
    after: tuple   # Buchtzustand unmittelbar nach dem Hub (vor den folgenden Abrufen)


@dataclass(frozen=True)
class Trace:
    start: tuple
    steps: tuple

    @property
    def moves(self) -> int:
        return len(self.steps)


def autopop(stacks):
    """Ruft ab, was oben liegt und gerade dran ist. Gibt (neue Stapel, abgerufene Nummern in Reihenfolge) zurück."""
    st = [list(s) for s in stacks]
    popped = []
    while True:
        present = [c for s in st for c in s]
        if not present:
            return tuple(tuple(s) for s in st), popped
        t = min(present)
        for s in st:
            if s and s[-1] == t:
                s.pop()
                popped.append(t)
                break
        else:
            return tuple(tuple(s) for s in st), popped


def stack_blockers(stack):
    """Container in einem Stapel (unten nach oben), die über einem früher abzurufenden liegen."""
    total, lowest = 0, INF
    for c in stack:
        if c > lowest:
            total += 1
        else:
            lowest = c
    return total


def blocker_count(stacks):
    """Untergrenze für die Zahl der Hübe: jeder blockierende Container muss mindestens einmal bewegt werden."""
    return sum(stack_blockers(s) for s in stacks)


def target_stack(stacks):
    """(nächste Abrufnummer, Index ihres Stapels). Die Bucht darf nicht leer sein."""
    t = min(c for s in stacks for c in s)
    for i, s in enumerate(stacks):
        if t in s:
            return t, i


# ---------------------------------------------------------------- Regeln
# Eine Regel bekommt die Bucht NACH dem Herausnehmen des Blockers `c` aus Stapel `src` und gibt den Zielstapel zurück.

def _candidates(stacks, src, height):
    return [k for k, s in enumerate(stacks) if k != src and len(s) < height]


def rule_tight_fit(stacks, src, height, c, rng=None):
    """Engste Passung: Stapel, auf dem c nichts blockiert (frühester Abruf dort später als c), mit dem kleinsten solchen
    Wert (leerer Stapel zählt als unendlich und kommt zuletzt); gibt es keinen, der Stapel mit dem größten frühesten Abruf."""
    best_ok, best_bad = None, None
    for k in _candidates(stacks, src, height):
        m = min(stacks[k]) if stacks[k] else INF
        if m > c:
            if best_ok is None or m < best_ok[0]:
                best_ok = (m, k)
        elif best_bad is None or m > best_bad[0]:
            best_bad = (m, k)
    return (best_ok or best_bad)[1]


def rule_lowest(stacks, src, height, c, rng=None):
    """Niedrigster Stapel: der mit den wenigsten Containern, bei Gleichstand der kleinste Index."""
    return min(_candidates(stacks, src, height), key=lambda k: (len(stacks[k]), k))


def rule_random(stacks, src, height, c, rng):
    """Zufall: irgendein Stapel mit Platz (aus der übergebenen Zufallsfolge)."""
    return rng.choice(_candidates(stacks, src, height))


RULES = {"tight": rule_tight_fit, "lowest": rule_lowest, "random": rule_random}


def run_rule(stacks, height, rule, seed=0) -> Trace:
    """Wendet die Regel an, bis die Bucht leer ist. `seed` speist nur die Zufallsregel."""
    rng = random.Random(seed)
    start = tuple(tuple(s) for s in stacks)
    cur, _ = autopop(start)
    steps = []
    while any(cur):
        t, i = target_stack(cur)
        st = [list(s) for s in cur]
        c = st[i].pop()
        k = rule(tuple(tuple(s) for s in st), i, height, c, rng)
        st[k].append(c)
        after = tuple(tuple(s) for s in st)
        steps.append(Step(t, c, i, k, after))
        cur, _ = autopop(after)
    return Trace(start, tuple(steps))


# ---------------------------------------------------------------- exakte Suche

class _Search:
    def __init__(self, height):
        self.height = height
        self.calls = 0
        self.bad = {}     # Zustand -> größtes Budget, das als unmachbar bewiesen ist
        self.good = {}    # Zustand -> kleinstes Budget, das als machbar bewiesen ist

    def children(self, key):
        """(Zielstapel k, neuer Zustand) in Reihenfolge der engsten Passung; identische Stapel nur einmal."""
        t, i = target_stack(key)
        c = key[i][-1]
        cands, seen = [], set()
        for k, s in enumerate(key):
            if k == i or len(s) >= self.height or s in seen:
                continue
            seen.add(s)
            m = min(s) if s else INF
            cands.append(((0, m) if m > c else (1, -m), k))
        cands.sort()
        out = []
        for _, k in cands:
            nxt = [list(s) for s in key]
            nxt[i].pop()
            nxt[k].append(c)
            out.append((k, tuple(tuple(s) for s in nxt)))
        return i, c, out

    def feasible(self, stacks, budget):
        """Gibt es ab diesem Zustand eine Fortsetzung mit höchstens `budget` Hüben?"""
        self.calls += 1
        st, _ = autopop(stacks)
        if not any(st):
            return True
        key = tuple(sorted(st))               # Symmetriebruch: die Reihenfolge der Stapel spielt keine Rolle
        g = self.good.get(key)
        if g is not None and g <= budget:
            return True
        if self.bad.get(key, -1) >= budget:
            return False
        if blocker_count(key) > budget:
            self.bad[key] = max(self.bad.get(key, -1), budget)
            return False
        _, _, kids = self.children(key)
        for _, nxt in kids:
            if self.feasible(nxt, budget - 1):
                self.good[key] = min(self.good.get(key, INF), budget)
                return True
        self.bad[key] = max(self.bad.get(key, -1), budget)
        return False


def _solve(stacks, height):
    """(Optimum, Suchobjekt mit gemerkten Zuständen): iterative Vertiefung über das Budget, beginnend bei der Untergrenze,
    bis zur Lösung der engsten Passung (eine gültige Lösung, also eine obere Schranke)."""
    start = tuple(tuple(s) for s in stacks)
    upper = run_rule(start, height, rule_tight_fit).moves
    search = _Search(height)
    for budget in range(blocker_count(start), upper + 1):
        if search.feasible(start, budget):
            return budget, search
    return upper, search


def solve_exact(stacks, height) -> int:
    """Kleinste Zahl Hübe (bewiesen)."""
    return _solve(stacks, height)[0]


def optimal_trace(stacks, height) -> Trace:
    """Eine optimale Hubfolge (bei mehreren: die zuerst gefundene in der Reihenfolge der engsten Passung). Die Rekonstruktion
    nutzt die bei der Suche gemerkten Zustände mit."""
    start = tuple(tuple(s) for s in stacks)
    budget, search = _solve(start, height)
    cur, _ = autopop(start)
    steps = []
    while any(cur):
        t, i = target_stack(cur)
        c = cur[i][-1]
        _, _, kids = search.children(cur)
        for k, nxt in kids:
            if search.feasible(nxt, budget - 1):
                steps.append(Step(t, c, i, k, nxt))
                cur, _ = autopop(nxt)
                budget -= 1
                break
        else:                               # kann nicht eintreten: das Budget ist als machbar bewiesen
            raise AssertionError("keine Fortsetzung mit dem bewiesenen Budget")
    return Trace(start, tuple(steps))


# ---------------------------------------------------------------- unabhängiger Prüfer

def check_trace(stacks, height, trace_steps) -> int:
    """Spielt eine Hubfolge [(Container, Zielstapel), ...] auf der Bucht nach, prüft jede Regel des Modells und gibt die Zahl der
    Hübe zurück. Wirft ValueError bei jedem Regelbruch (kein Platz, falscher Container, Bucht danach nicht leer)."""
    st = [list(s) for s in stacks]
    moves = 0

    def pop_ready():
        while True:
            present = [c for s in st for c in s]
            if not present:
                return
            t = min(present)
            for s in st:
                if s and s[-1] == t:
                    s.pop()
                    break
            else:
                return

    pop_ready()
    for c, dst in trace_steps:
        present = [x for s in st for x in s]
        if not present:
            raise ValueError("Bucht schon leer")
        t = min(present)
        src = next(i for i, s in enumerate(st) if t in s)
        if not st[src] or st[src][-1] != c:
            raise ValueError(f"Container {c} liegt nicht oben auf dem Stapel des Ziels {t}")
        if c == t or dst == src or not (0 <= dst < len(st)) or len(st[dst]) >= height:
            raise ValueError(f"unzulässiger Hub von Container {c} auf Stapel {dst}")
        st[src].pop()
        st[dst].append(c)
        moves += 1
        pop_ready()
    if any(st):
        raise ValueError("Bucht nach der Hubfolge nicht leer")
    return moves


# ---------------------------------------------------------------- Zerlegung der Hubzahl (Stück 2)

def initial_blockers(stacks):
    """Nummern der Container, die anfangs über einem früher abzurufenden im selben Stapel liegen."""
    out = set()
    for s in stacks:
        lowest = INF
        for c in s:
            if c > lowest:
                out.add(c)
            else:
                lowest = c
    return frozenset(out)


def hub_counts(trace) -> dict:
    """{Container: Zahl seiner Hübe} in einer Spur (nur bewegte Container)."""
    counts = {}
    for st in trace.steps:
        counts[st.container] = counts.get(st.container, 0) + 1
    return counts


def count_sequences(stacks, height, budget) -> int:
    """Zahl der verschiedenen Hubfolgen (Container, Zielstapel) mit genau `budget` Hüben, die die Bucht leeren."""
    cur, _ = autopop(stacks)
    if not any(cur):
        return 1 if budget == 0 else 0
    if budget == 0:
        return 0
    _, i = target_stack(cur)
    c = cur[i][-1]
    total = 0
    for k in range(len(cur)):
        if k == i or len(cur[k]) >= height:
            continue
        nxt = [list(x) for x in cur]
        nxt[i].pop()
        nxt[k].append(c)
        total += count_sequences(tuple(tuple(x) for x in nxt), height, budget - 1)
    return total
