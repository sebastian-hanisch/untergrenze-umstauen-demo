"""Untergrenze: blockierende Container zählen - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Stück 2 der Reihe „Umstauen: Untergrenze und Suche“. Jeder Container, der über einem früher abzurufenden liegt, muss mindestens einmal bewegt werden:
das ist eine billige, immer gültige Untergrenze für die Hubzahl. Die Demo zeigt, wie weit sie trägt (eine Bucht, 100 feste Buchten), wie oft sie
Optimalität beweist, woraus die Lücke besteht (Mehrfachhübe) und wie sie mit Lagen und Füllgrad wächst. Die beiden Kurven sind vorberechnet (uum_bands.json).

Lauffähig mit: streamlit run app.py
"""

import streamlit as st

import uum_constants as C
from uum_evaluation import (
    Settings,
    analyse,
    cell_stats,
    fill_exception_note,
    fill_exceptions,
    fill_points,
    gap_histogram,
    hub_table,
    hubs,
    layer_points,
    load_bands,
    sample_rows,
    single_blocker,
    share,
    step_lines,
    verdict_bay,
    verdict_fill,
    verdict_layers,
    verdict_proof,
    verdict_sample,
    verdict_single,
    verdict_validity,
)
from uum_layout import dunkles_design, kopf_css
from uum_presets import (
    bounds,
    init_session_state_defaults,
    load_permalink_settings,
    randomize_seed,
    sidebar_presets,
    sync_query_params,
)
from uum_visualization import build_bay, build_fill_curve, build_gap_histogram, build_layer_curve, build_proof

st.set_page_config(page_title="Untergrenze – Sebastian Hanisch", layout="wide")


@st.cache_data(show_spinner=False)
def _analysis(settings):
    return analyse(settings)


@st.cache_data(show_spinner=False)
def _rows(stacks, layers, extra):
    return sample_rows(stacks, layers, extra)


@st.cache_data(show_spinner=False)
def _bands():
    return load_bands()


@st.cache_data(show_spinner=False)
def _single():
    return single_blocker()


# Fester Kopf: nur der Titel bleibt beim Scrollen oben (Stylesheet in uum_layout.py).
st.html(kopf_css(dunkles_design()))
with st.container(key="kopf"):
    st.title("📏 Untergrenze: blockierende Container zählen")
st.markdown(
    """
In einer **Bucht** werden Container in bekannter Reihenfolge abgerufen; wer über einem früher gebrauchten liegt, **blockiert** und muss auf einen anderen Stapel (jeder Hub kostet). Wie viele Hübe sind **mindestens** nötig? Eine Zahl, die man ohne jede Suche ablesen kann, ist die Zahl der blockierenden Container. Die Demo zeigt, **warum sie immer gilt**, **wie oft sie das Optimum trifft** (und damit Optimalität beweist) und **woraus die Lücke besteht**, wenn sie es nicht tut.

Weiter unten: die Abschnitte **🔬 Experiment** (gilt sie immer, wie weit trägt sie, Beweisquote, Lagen und Füllgrad, der einzelne Blocker), **🚧 Wo die Annahmen enden** und der Expander **📐 Mathematische Formulierung**. Dies ist das zweite Stück der Reihe „Umstauen: Untergrenze und Suche“; das erste ([Zielstapel wählen](https://sebastianhanisch-umstauen-regeln-demo.streamlit.app/)) vergleicht drei Regeln mit dem Optimum.
"""
)

with st.expander("So funktioniert die Untergrenze", expanded=True):
    st.markdown(
        """
1. **Blockierend ist,** wer im selben Stapel über einem Container mit kleinerer Nummer liegt: Der kleinere muss zuerst abgerufen werden, kommt aber nicht heran.
2. **Mindestens ein Hub je Blocker:** Der Blocker muss auf einen anderen Stapel, bevor der kleinere frei wird. Also braucht jede Spur mindestens so viele Hübe, wie es blockierende Container gibt.
3. **Nur Blocker werden bewegt:** Wer anfangs nicht blockiert, hat unter sich nur größere Nummern; die ändern sich nie (neue Container kommen nur oben drauf). Wer nicht blockiert, liegt nie über dem nächsten Abruf und wird deshalb nie bewegt.
4. **Die Lücke:** Hübe einer Spur = Zahl der Blocker + **Mehrfachhübe** (ein Container wird mehr als einmal bewegt, weil er auf einem Stapel landet, auf dem er wieder blockiert). Die Untergrenze zählt die Mehrfachhübe nicht.
        """
    )

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    sidebar_presets()  # Schnellstart oben, das aktive Preset ist hervorgehoben
    st.header("⚙️ Einstellungen")
    st.markdown("**Bucht**")
    stacks = st.slider("Stapel", *bounds("stacks_slider"), key="stacks_slider", help="Wie viele Stapel die Bucht hat.")
    layers = st.slider("Lagen je Stapel", *bounds("layers_slider"), key="layers_slider", help="So viele Container stehen anfangs auf jedem Stapel.")
    extra = st.slider("Platz (Lagen über der Anfangshöhe)", *bounds("extra_slider"), key="extra_slider",
                      help="Höchsthöhe = Lagen + Platz. Standard 2; die beiden Kurven weiter unten sind für Platz 2 vorberechnet.")
    seed = st.number_input("Bucht-Nummer (Seed)", *bounds("seed_input"), key="seed_input", step=1, help="Die Nummer bestimmt, wie die Abrufnummern auf die Plätze verteilt sind.")
    st.button("🎲 Neue Bucht würfeln", width="stretch", on_click=randomize_seed)

sync_query_params({"stacks_slider": int(stacks), "layers_slider": int(layers), "extra_slider": int(extra), "seed_input": int(seed)})

settings = Settings(int(stacks), int(layers), int(extra), int(seed))
a = _analysis(settings)

# --- Ergebnis ------------------------------------------------------------------------------------------------------------------------------

st.markdown("## 🎯 Ergebnis")
m1, m2, m3 = st.columns(3)
m1.metric("Untergrenze (mindestens)", a.lower, delta="blockierende Container", delta_color="off", help="Jeder Container, der über einem früher abzurufenden liegt, muss mindestens einmal bewegt werden.")
m2.metric("Optimum (bewiesen)", a.optimum, delta="Referenz", delta_color="off")
# Delta immer als „mein Wert minus Referenz“; die Farbe regelt delta_color="inverse" (Vorzeichen-Falle, DEMO-PLAYBOOK §2).
m3.metric("Lücke (Mehrfachhübe)", a.gap, delta=a.optimum - a.lower, delta_color="inverse", help="Optimum minus Untergrenze: so oft wird in der optimalen Folge ein Container ein weiteres Mal bewegt.")
st.plotly_chart(build_bay(a.bay, a.height, target=min(c for s in a.bay for c in s)), width="stretch", key="chart_bay")
st.caption("Rot: blockierende Container (liegen über einem früher abzurufenden), grün: der nächste Abruf, grau-blau: alle übrigen.")

st.markdown("**Hübe in der optimalen Folge, je blockierendem Container**")
rows_hub = hub_table(a)
if rows_hub:
    table = ["| Container | Hübe | davon Mehrfachhübe |", "|---|---|---|"]
    for r in rows_hub:
        table.append(f"| {r['container']} | {r['hubs']} | {r['extra']} |")
    table.append(f"| **Summe** | **{sum(r['hubs'] for r in rows_hub)}** | **{sum(r['extra'] for r in rows_hub)}** |")
    st.markdown("\n".join(table))
    st.caption(f"Untergrenze {a.lower} + Mehrfachhübe {a.gap} = Optimum {a.optimum}.")
    with st.expander("Die optimale Folge im Wortlaut"):
        st.markdown("\n".join(f"{i}. {line.split(': ', 1)[1]}" for i, line in enumerate(step_lines(a.opt_trace), 1)))
else:
    st.caption("Kein Container blockiert: Es ist kein Hub nötig.")

# --- Kernfrage -----------------------------------------------------------------------------------------------------------------------------

st.markdown("## ❓ Kernfrage: Wie viele Hübe sind mindestens nötig, und reicht das?")
kind, text = verdict_bay(a)
getattr(st, kind)(text)

st.markdown("---")

# --- Experiment: 100 feste Buchten ---------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment: Gilt die Untergrenze immer, und wie weit trägt sie?")
st.caption(f"Die Bucht-Nummern 0 bis {C.SAMPLE_SEEDS[-1]} bei {settings.stacks} Stapeln, {settings.layers} Lagen und Platz {settings.extra}: Untergrenze, Optimum und engste Passung je Bucht "
           f"(nie eine einzelne Bucht als Befund).")
with st.spinner("Rechne 100 Buchten …"):
    rows = _rows(settings.stacks, settings.layers, settings.extra)
stat = cell_stats(rows)
kind, text = verdict_validity(stat)
getattr(st, kind)(text)
st.plotly_chart(build_gap_histogram(gap_histogram(rows)), width="stretch", key="chart_gap")
st.caption(f"Das Optimum liegt im Mittel bei {stat['opt_mean']:.2f} Hüben, die Untergrenze bei {stat['lb_mean']:.2f}; im Mittel über die Buchten ist das Optimum das {stat['ratio_mean']:.2f}-fache der Untergrenze "
           f"(Mittel der Verhältnisse je Bucht, nicht das Verhältnis der Mittelwerte; Buchten ohne blockierende Container zählen im Verhältnis nicht mit).")
kind, text = verdict_sample(stat)
getattr(st, kind)(text)

st.markdown("---")

st.subheader("🔬 Experiment: Wie oft beweist die Untergrenze, dass eine Regel optimal ist?")
st.caption("Trifft eine Regel die Untergrenze, ist sie ohne Suche bewiesen optimal. Hier die engste Passung aus Stück 1 über dieselben 100 Buchten.")
st.plotly_chart(build_proof(stat), width="stretch", key="chart_proof")
kind, text = verdict_proof(stat)
getattr(st, kind)(text)

st.markdown("---")

st.subheader("🔬 Experiment: Wie hängt die Lücke von Lagen und Füllgrad ab?")
st.caption(f"Je Zelle dieselben 100 festen Buchten. **Lagen:** {settings.stacks} Stapel, volle Buchten, Platz 2. **Füllgrad:** Zufallsbuchten mit ungleich hohen Stapeln "
           f"(eine andere Familie als oben), {C.FILL_STACKS} Stapel. Beide Kurven sind vorberechnet (`generate_precomputed.py`).")
bands = _bands()
pts = layer_points(bands, settings.stacks)
st.plotly_chart(build_layer_curve(pts), width="stretch", key="chart_layers")
kind, text = verdict_layers(pts, settings.stacks)
getattr(st, kind)(text)
curves = {h: fill_points(bands, h) for h in C.FILL_CELLS}
st.plotly_chart(build_fill_curve(curves), width="stretch", key="chart_fill")
for h, p in curves.items():
    kind, text = verdict_fill(p, h)
    getattr(st, kind)(text)
st.caption(fill_exception_note(*fill_exceptions(bands)))

st.markdown("---")

st.subheader("🔬 Experiment: Der einzelne Blocker")
one = _single()
st.caption("3 Stapel mit je 2 Containern, Höchsthöhe 4: Nur die 4 blockiert (sie liegt über der 1). Ein Vorgriff auf das Stück über schärfere Untergrenzen.")
st.plotly_chart(build_bay(one["bay"], one["height"], target=1), width="stretch", key="chart_single")
st.markdown("\n".join(f"{i}. {line.split(': ', 1)[1]}" for i, line in enumerate(step_lines(one["trace"]), 1)))
kind, text = verdict_single(one)
getattr(st, kind)(text)

st.markdown("---")

# --- Grenzen -------------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Restricted:** nur Container über dem gesuchten werden bewegt | Wer auch andere bewegen darf, kann Hübe sparen; die Untergrenze gilt weiter (sie zählt Mindestbewegungen), das Optimum kann aber kleiner werden. Hier nicht gemessen. | späteres Stück der Reihe |
| **Die ganze Abrufreihenfolge ist bekannt** | Bei unbekannter Reihenfolge ist „blockierend“ nicht zu bestimmen. | spätere Stücke der Reihe |
| **Volle Buchten mit gleich hohen Stapeln** (Lagenkurve) und **Zufallsbuchten** (Füllgradkurve) | Die beiden Familien sind verschieden; ein Vergleich über die Familien hinweg ist nur ungefähr. Andere Stapelzahlen und Höhen sind nur teilweise gemessen. | – |
| **Die Untergrenze zählt jeden Blocker einmal** | Sie sieht nicht, dass ein umgesetzter Container wieder blockieren kann; die Lücke wächst mit Lagen und Füllgrad. | Stück über schärfere Untergrenzen, Stück über die Suche |
| **Zahlen aus Zufallsbuchten** | Größenordnungen aus 100 festen Buchten je Zelle, keine Messung an einem echten Terminal oder Lager. | – |
"""
)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Gegeben:** eine Bucht aus $s$ Stapeln der Höchsthöhe $H$, die Container tragen die Abrufnummern $1, \dots, N$ (kleiner = früher). Ein Hub setzt den obersten Container eines Stapels auf einen anderen Stapel mit Platz; im *restricted* Modell werden nur Container über der nächsten abzurufenden Nummer bewegt, die nächste Nummer wird entnommen, sobald sie oben liegt.

**Blockierend:** Ein Container $c$ ist *blockierend*, wenn im selben Stapel unter ihm ein Container mit Nummer kleiner als $c$ liegt. Sei $B$ die Menge der anfangs blockierenden Container und $L = \lvert B \rvert$ die Untergrenze.

**Satz 1 (Gültigkeit).** Jede Hubfolge, die die Bucht leert, hat mindestens $L$ Hübe. *Beweis:* Der kleinere Container unter einem blockierenden $c$ muss vor $c$ abgerufen werden. Er ist nur erreichbar, wenn $c$ nicht mehr über ihm liegt, und $c$ kann nur durch einen Hub weg, bevor es ihn ersetzt. Jeder Blocker braucht also mindestens einen eigenen Hub.

**Satz 2 (nur Blocker werden bewegt).** Ein anfangs nicht blockierender Container wird nie bewegt. *Beweis:* Unter einem nicht blockierenden $c$ liegen nur größere Nummern. Neue Container kommen nur oben auf Stapel, also ändert sich nichts unter $c$; $c$ bleibt nicht blockierend. Würde $c$ bewegt, läge es über der nächsten abzurufenden Nummer, die kleiner als $c$ wäre und unter $c$ läge, also wäre $c$ blockierend.

**Folgerung (Zerlegung).** Für jede Hubfolge gilt: Zahl der Hübe $= \sum_{c \in B} h_c = L + \sum_{c \in B} (h_c - 1)$, wobei $h_c \ge 1$ die Zahl der Hübe von $c$ ist. Die Lücke zum Optimum $\text{OPT} - L$ ist also die Zahl der *Mehrfachhübe* der optimalen Folge.

**Beweisquote.** Ist eine Regel genau so lang wie die Untergrenze, ist sie wegen Satz 1 optimal, ohne dass gesucht werden muss. Dass die engste Passung die Untergrenze immer trifft, wenn das Optimum sie trifft, ist ein **Messbefund**, kein Satz.

**Literatur.** Das Problem heißt in der Literatur Block Relocation Problem (auch Container Relocation Problem). Eine Klassifikation verwandter Stapelprobleme geben Lehnfeld und Knust, European Journal of Operational Research 239(2), 2014, S. 297–312 (Fundstelle geprüft, Volltext nicht gelesen). Die Zählung der blockierenden Container als Untergrenze und die Zerlegung in Mehrfachhübe sind hier selbst hergeleitet; ob sie unter einem Namen in der Literatur stehen, wurde nicht geprüft.
        """
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html)."
)
