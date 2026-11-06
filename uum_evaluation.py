"""Kennzahlen, Verdikt-Logik, Stichprobe über feste Buchten und vorberechnete Kurven. Reine Funktionen: die App ruft st.<Art>(Text),
die Tests prüfen jede Zahl und jede Schwelle."""

import json
from dataclasses import dataclass
from pathlib import Path
from statistics import mean

import uum_algorithm as A
import uum_constants as C
from uum_scenario import make_bay, max_height, partial_bay

BANDS_FILE = Path(__file__).resolve().parent / "uum_bands.json"


@dataclass(frozen=True)
class Settings:
    stacks: int = C.DEFAULT_STACKS
    layers: int = C.DEFAULT_LAYERS
    extra: int = C.DEFAULT_EXTRA
    seed: int = C.EVERYDAY_SEED


@dataclass(frozen=True)
class Analysis:
    bay: tuple
    height: int
    lower: int          # Untergrenze: blockierende Container
    optimum: int        # bewiesen
    tight: int          # Hübe der engsten Passung
    opt_trace: A.Trace
    blockers: tuple     # anfangs blockierende Container (Nummern, aufsteigend)

    @property
    def gap(self) -> int:
        return self.optimum - self.lower


def analyse(settings: Settings) -> Analysis:
    bay = make_bay(settings.stacks, settings.layers, settings.seed)
    height = max_height(settings.layers, settings.extra)
    opt_trace = A.optimal_trace(bay, height)
    return Analysis(bay, height, A.blocker_count(bay), opt_trace.moves, A.run_rule(bay, height, A.rule_tight_fit).moves,
                    opt_trace, tuple(sorted(A.initial_blockers(bay))))


def hubs(n: int) -> str:
    return f"{n} Hub" if n == 1 else f"{n} Hübe"


def times(n: int) -> str:
    return "einmal" if n == 1 else "zweimal" if n == 2 else f"{n}-mal"


def hub_table(a: Analysis) -> list[dict]:
    """Eine Zeile je anfangs blockierendem Container: Hübe in der optimalen Folge und davon Mehrfachhübe (Hübe minus 1)."""
    counts = A.hub_counts(a.opt_trace)
    return [{"container": c, "hubs": counts.get(c, 0), "extra": max(counts.get(c, 0) - 1, 0)} for c in a.blockers]


def step_lines(trace: A.Trace) -> list[str]:
    """Eine Zeile je Hub in Worten (Stapel ab 1 gezählt)."""
    return [f"Hub {i}: Container {s.container} (über der {s.target}) von Stapel {s.src + 1} auf Stapel {s.dst + 1}" for i, s in enumerate(trace.steps, 1)]


def moved_non_blockers(bay, trace) -> list[int]:
    """Bewegte Container, die anfangs nicht blockierend waren (laut Satz leer)."""
    blockers = A.initial_blockers(bay)
    return sorted({s.container for s in trace.steps if s.container not in blockers})


# ---------------------------------------------------------------- Verdikte einer Bucht

def verdict_bay(a: Analysis) -> tuple[str, str]:
    """Verdikt der Kernfrage an der gezeigten Bucht als (Art, Text): trägt die Untergrenze?"""
    if a.optimum == 0:
        return "success", "Die Bucht ist schon sortiert: kein Container blockiert, die Untergrenze und das Optimum sind 0."
    if a.gap == 0:
        return "success", (f"Die Untergrenze trifft: Es sind mindestens {hubs(a.lower)} nötig, und das Optimum ist {a.optimum}. "
                           f"Eine Regel, die so viele Hübe braucht, ist damit ohne jede Suche bewiesen optimal.")
    again = [r for r in hub_table(a) if r["extra"] > 0]
    who = ""
    if again:
        who = " Mehrfach bewegt werden: " + ", ".join(f"Container {r['container']} ({times(r['hubs'])})" for r in again) + "."
    return "warning", (f"Die Untergrenze liegt {a.gap} {'Hub' if a.gap == 1 else 'Hübe'} unter dem Optimum: mindestens {hubs(a.lower)}, das Optimum ist {a.optimum}. "
                       f"Die Lücke besteht aus Mehrfachhüben: Container, die auf einen Stapel kommen, auf dem sie wieder blockieren.{who}")


# ---------------------------------------------------------------- Stichprobe

def sample_rows(stacks: int, layers: int, extra: int, seeds=C.SAMPLE_SEEDS) -> list[dict]:
    """Eine Zeile je feste Bucht: Untergrenze, Optimum, Hübe der engsten Passung, bewegte Nicht-Blocker in der optimalen Folge und in der engsten Passung."""
    height = max_height(layers, extra)
    rows = []
    for sd in seeds:
        bay = make_bay(stacks, layers, sd)
        opt_trace = A.optimal_trace(bay, height)
        tight_trace = A.run_rule(bay, height, A.rule_tight_fit)
        rows.append({"seed": sd, "lb": A.blocker_count(bay), "opt": opt_trace.moves, "tight": tight_trace.moves,
                     "bad": len(moved_non_blockers(bay, opt_trace)) + len(moved_non_blockers(bay, tight_trace))})
    return rows


def partial_rows(stacks: int, height: int, n: int, seeds=C.SAMPLE_SEEDS) -> list[dict]:
    """Wie `sample_rows` für teilgefüllte Zufallsbuchten (ohne die Spurprüfung)."""
    rows = []
    for sd in seeds:
        bay = partial_bay(stacks, height, n, sd)
        rows.append({"seed": sd, "lb": A.blocker_count(bay), "opt": A.solve_exact(bay, height),
                     "tight": A.run_rule(bay, height, A.rule_tight_fit).moves, "bad": 0})
    return rows


def cell_stats(rows: list[dict]) -> dict:
    """Kennzahlen einer Stichprobe: Mittel, Lücke, Untergrenze = Optimum, Beweisquote (bewiesen / optimal ohne Beweis / verfehlt)."""
    n = len(rows)
    positive = [r for r in rows if r["lb"] > 0]
    return {
        "n": n,
        "opt_mean": mean(r["opt"] for r in rows), "lb_mean": mean(r["lb"] for r in rows),
        "gap_mean": mean(r["opt"] - r["lb"] for r in rows), "gap_max": max(r["opt"] - r["lb"] for r in rows),
        "ratio_mean": mean(r["opt"] / r["lb"] for r in positive) if positive else 0.0,
        "lb_equal": sum(r["lb"] == r["opt"] for r in rows),
        "valid": sum(r["lb"] <= r["opt"] for r in rows),
        "proven": sum(r["tight"] == r["lb"] for r in rows),
        "unproven": sum(r["tight"] == r["opt"] and r["tight"] > r["lb"] for r in rows),
        "miss": sum(r["tight"] > r["opt"] for r in rows),
        "exceptions": sum(r["lb"] == r["opt"] and r["tight"] > r["opt"] for r in rows),
        "bad_moves": sum(r["bad"] for r in rows),
    }


def gap_histogram(rows: list[dict], cap: int = 4) -> list[int]:
    """Zahl der Buchten mit Lücke 0, 1, ..., cap-1 und `cap` oder mehr."""
    counts = [0] * (cap + 1)
    for r in rows:
        counts[min(r["opt"] - r["lb"], cap)] += 1
    return counts


def share(count: int, n: int) -> float:
    return 100.0 * count / n if n else 0.0


def verdict_sample(stats: dict) -> tuple[str, str]:
    """Verdikt „trägt die Untergrenze?“ in drei Zuständen nach dem Anteil der Buchten mit Untergrenze = Optimum."""
    n, k = stats["n"], stats["lb_equal"]
    pct = share(k, n)
    base = (f"In {k} von {n} Buchten ist die Untergrenze gleich dem Optimum; im Mittel liegt sie {stats['gap_mean']:.2f} Hübe darunter "
            f"(Optimum {stats['opt_mean']:.2f}, Untergrenze {stats['lb_mean']:.2f}, größte Lücke {stats['gap_max']}).")
    if pct >= C.SHARE_STRONG:
        return "success", base + " Die Untergrenze trägt hier in der Mehrzahl der Buchten."
    if pct >= C.SHARE_WEAK:
        return "info", base + " Die Untergrenze trägt hier nur in einem Teil der Buchten."
    return "warning", base + " Die Untergrenze trägt hier fast nie: Ohne Suche lässt sich das Optimum kaum beweisen."


def verdict_validity(stats: dict) -> tuple[str, str]:
    """Verdikt „gilt die Untergrenze immer?“: Zahl der Buchten mit Untergrenze <= Optimum und bewegte Nicht-Blocker."""
    n = stats["n"]
    if stats["valid"] == n and stats["bad_moves"] == 0:
        return "success", (f"Die Untergrenze gilt in allen {n} Buchten (nie über dem Optimum), und in den geprüften Spuren "
                           f"(optimale Folge und engste Passung) wird kein anfangs nicht blockierender Container bewegt.")
    return "warning", (f"Achtung: Die Untergrenze liegt in {n - stats['valid']} von {n} Buchten über dem Optimum, "
                       f"und es wurden {stats['bad_moves']} Hübe an anfangs nicht blockierenden Containern gezählt; das widerspricht dem Satz.")


def verdict_proof(stats: dict) -> tuple[str, str]:
    """Verdikt der Beweisquote: bewiesen / optimal ohne Beweis / verfehlt, dazu der Messbefund „trifft die Untergrenze, trifft die Regel“."""
    n = stats["n"]
    text = (f"Die engste Passung ist in {stats['proven']} von {n} Buchten bewiesen optimal (sie trifft die Untergrenze), in {stats['unproven']} optimal, "
            f"aber nur mit Suche zu beweisen, und verfehlt das Optimum in {stats['miss']}.")
    if stats["exceptions"] == 0:
        return "info", text + f" In allen {n} Buchten gilt: Trifft die Untergrenze das Optimum, trifft es auch die engste Passung (Messbefund, kein Satz)."
    return "warning", text + f" In {stats['exceptions']} Buchten trifft die Untergrenze das Optimum, die engste Passung aber nicht (Messbefund)."


# ---------------------------------------------------------------- Kurven (vorberechnet)

def load_bands() -> dict:
    """Vorberechnete Kennzahlen, erzeugt von generate_precomputed.py: {"lagen": {"s,l": Kennzahlen}, "fuell": {"H,N": Kennzahlen}}."""
    return json.loads(BANDS_FILE.read_text(encoding="utf-8"))


def layer_key(stacks: int, layers: int) -> str:
    return f"{stacks},{layers}"


def fill_key(height: int, n: int) -> str:
    return f"{height},{n}"


def layer_points(bands: dict, stacks: int) -> list[dict]:
    """Untergrenze = Optimum (in %) und mittlere Lücke über die Lagen für eine Stapelzahl (Zuschlag 2)."""
    pts = []
    for layers in C.LAYER_CURVE:
        st = bands["lagen"][layer_key(stacks, layers)]
        pts.append({"layers": layers, "n": st["n"], "lb_equal": st["lb_equal"], "gap_mean": st["gap_mean"], "opt_mean": st["opt_mean"]})
    return pts


def verdict_layers(points: list[dict], stacks: int) -> tuple[str, str]:
    """Verdikt der Lagenkurve: Untergrenze = Optimum bei den wenigsten und den meisten Lagen."""
    first, last = points[0], points[-1]
    a, b = first["lb_equal"], last["lb_equal"]
    text = (f"Bei {stacks} Stapeln ist die Untergrenze gleich dem Optimum in {a} von {first['n']} Buchten mit {first['layers']} Lagen und in {b} von {last['n']} "
            f"mit {last['layers']} Lagen; die mittlere Lücke wächst von {first['gap_mean']:.2f} auf {last['gap_mean']:.2f} Hübe.")
    if a - b >= C.CURVE_STEP:
        return "warning", text + " Mit mehr Lagen trägt die Untergrenze deutlich seltener."
    if b - a >= C.CURVE_STEP:
        return "info", text + " Mit mehr Lagen trägt die Untergrenze öfter."
    return "info", text + " Die Zahl der Lagen ändert hier wenig."


def fill_points(bands: dict, height: int) -> list[dict]:
    """Füllgrad in % der Plätze (N / (4 * H)), mittlere Lücke und Untergrenze = Optimum für eine Höchsthöhe."""
    pts = []
    for n in C.FILL_CELLS[height]:
        st = bands["fuell"][fill_key(height, n)]
        pts.append({"n_containers": n, "fill": 100.0 * n / (C.FILL_STACKS * height), "gap_mean": st["gap_mean"], "lb_equal": st["lb_equal"], "n": st["n"]})
    return pts


def fill_exceptions(bands: dict) -> tuple[int, int]:
    """(Ausnahmen, Buchten) über alle Zellen der Füllgradkurve: Buchten, in denen die Untergrenze das Optimum trifft, die engste Passung aber nicht."""
    cells = bands["fuell"].values()
    return sum(c["exceptions"] for c in cells), sum(c["n"] for c in cells)


def fill_exception_note(exceptions: int, total: int) -> str:
    """Satz zum Messbefund „Untergrenze trifft ⇒ engste Passung trifft“ in den Zufallsbuchten."""
    if exceptions == 0:
        return f"Der Messbefund „Trifft die Untergrenze das Optimum, trifft es auch die engste Passung“ gilt in allen {total} Zufallsbuchten dieser Kurve."
    return (f"Der Messbefund „Trifft die Untergrenze das Optimum, trifft es auch die engste Passung“ gilt in diesen Zufallsbuchten nicht ausnahmslos: "
            f"{exceptions} {'Ausnahme' if exceptions == 1 else 'Ausnahmen'} in {total} Buchten.")


def verdict_fill(points: list[dict], height: int) -> tuple[str, str]:
    """Verdikt der Füllgradkurve: mittlere Lücke bei dem geringsten und dem höchsten Füllgrad."""
    first, last = points[0], points[-1]
    text = (f"Bei Höchsthöhe {height} und {C.FILL_STACKS} Stapeln liegt die mittlere Lücke bei {first['fill']:.0f} % Füllgrad bei {first['gap_mean']:.2f} Hüben "
            f"und bei {last['fill']:.0f} % bei {last['gap_mean']:.2f}; die Untergrenze trifft das Optimum in {first['lb_equal']} bzw. {last['lb_equal']} von {last['n']} Buchten.")
    if last["gap_mean"] - first["gap_mean"] >= C.FILL_GAP_STEP:
        return "warning", text + " Je voller die Bucht, desto weniger trägt die Untergrenze."
    return "info", text + " Der Füllgrad ändert die Lücke hier wenig."


# ---------------------------------------------------------------- einzelner Blocker (Vorgriff)

def single_blocker() -> dict:
    """Die Bucht mit einem einzigen blockierenden Container (3 Stapel x 2 Lagen): Untergrenze, Optimum und die Zahl der Hubfolgen mit einem Hub, die sie leeren."""
    bay, height = C.SINGLE_BAY, max_height(2, C.DEFAULT_EXTRA)
    tr = A.optimal_trace(bay, height)
    return {"bay": bay, "height": height, "lower": A.blocker_count(bay), "optimum": tr.moves, "trace": tr,
            "one_hub_solutions": A.count_sequences(bay, height, 1), "mins": sorted(min(s) for s in bay)}


def verdict_single(d: dict) -> tuple[str, str]:
    """Verdikt des einzelnen Blockers: Untergrenze 1, Optimum 2, keine Hubfolge mit einem Hub."""
    if d["optimum"] == d["lower"]:
        return "info", f"An dieser Bucht trifft die Untergrenze ({d['lower']}) das Optimum; sie ist kein Beispiel für eine Lücke."
    return "warning", (f"Es blockiert nur ein Container, die Untergrenze ist {d['lower']}, und das Optimum ist {d['optimum']}. "
                       f"Die kleinsten Nummern der drei Stapel sind {', '.join(str(m) for m in d['mins'])}: Auf jedem anderen Stapel liegt unten etwas Früheres als der Blocker, "
                       f"er blockiert also überall wieder. Hubfolgen mit einem Hub, die die Bucht leeren: {d['one_hub_solutions']}.")
