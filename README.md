# Untergrenze: blockierende Container zählen – Streamlit-Demo

<!-- TODO nach dem Deploy: direkt hierher den Live-Link setzen (Leerzeile davor und danach):
**[→ Demo live ausprobieren](https://sebastianhanisch-untergrenze-umstauen-demo.streamlit.app/)** -->

Zweites Stück der Konzepte-Reihe **„Umstauen: Untergrenze und Suche“** für die Website „Sebastian Hanisch – Operations Research und Machine Learning“. [Stück 1](https://sebastianhanisch-umstauen-regeln-demo.streamlit.app/) vergleicht drei Regeln für den Zielstapel mit dem bewiesenen Optimum und zeigt die Untergrenze nur als Zahl. Dieses Stück erklärt und vermisst sie: Jeder Container, der über einem früher abzurufenden liegt, muss mindestens einmal bewegt werden. Das ist eine billige, immer gültige Untergrenze für die Hubzahl, und trifft eine Regel sie, ist die Regel ohne Suche bewiesen optimal. Die Demo zeigt, **warum sie gilt**, **wie oft sie das Optimum trifft**, **woraus die Lücke besteht** und **wie die Lücke mit Lagen und Füllgrad wächst**.

## Warum dieses Problem

Eine Untergrenze ist die einfachste Art, über ein Optimum etwas zu wissen, ohne es zu berechnen. Hier lässt sie sich ablesen (Blocker zählen), beweisen (vier Sätze) und messen (Lücke zum Optimum). Das zeigt zugleich, was eine einfache Untergrenze nicht sieht: dass ein umgesetzter Container auf dem neuen Stapel wieder blockieren kann.

## Modell

Eine Bucht aus *s* Stapeln mit Höchsthöhe *H* = Lagen + Platz (Platz 1 bis 4, Standard 2); anfangs steht auf jedem Stapel dieselbe Zahl von Containern. Die Abrufnummern 1 bis *N* sind zufällig verteilt, 1 wird zuerst abgerufen. Ein Hub setzt den obersten Container eines Stapels auf einen anderen Stapel mit Platz; **restricted**: Es werden nur Container über dem gesuchten bewegt. Ein Container ist **blockierend**, wenn im selben Stapel unter ihm ein Container mit kleinerer Nummer liegt. **Untergrenze** = Zahl der blockierenden Container. Formal und mit den Beweisen im Expander „📐 Mathematische Formulierung“.

**Satz 1 (Gültigkeit):** Jede Hubfolge hat mindestens so viele Hübe, wie es blockierende Container gibt. **Satz 2:** Ein anfangs nicht blockierender Container wird nie bewegt. **Folgerung:** Hübe = Untergrenze + Mehrfachhübe; die Lücke zum Optimum ist die Zahl der Mehrfachhübe der optimalen Folge.

## Methodik

- **Untergrenze:** Zählung der blockierenden Container (`uum_algorithm.blocker_count`), ein Durchlauf je Stapel.
- **Optimum:** exakte Suche mit iterativer Vertiefung über das Hub-Budget, beginnend bei der Untergrenze, Zustände bis auf Vertauschen der Stapel gemerkt (aus Stück 1 kopiert); immer bewiesen, ohne Zeitgrenze. Die optimale Folge wird aus den bei der Suche gemerkten Zuständen rekonstruiert.
- **Engste Passung** (Regel aus Stück 1): unter den Stapeln, auf denen der Blocker nichts blockiert, der mit dem kleinsten frühesten Abruf; leerer Stapel zuletzt; sonst der Stapel mit dem größten frühesten Abruf.
- **Abschnitte der App:** Ergebnis (Untergrenze, Optimum, Lücke, Hübe je blockierendem Container); 100 feste Buchten (Bucht-Nummern 0 bis 99) für die gewählte Einstellung, live gerechnet (bei 5 Stapeln und 4 Lagen rund 11 Sekunden); Beweisquote; Lagenkurve und Füllgradkurve (vorberechnet in `uum_bands.json`, erzeugt von `generate_precomputed.py`, rund 25 Sekunden); der einzelne Blocker.
- **Zwei Familien von Buchten:** die Hauptbucht und die Lagenkurve nutzen **volle Buchten mit gleich hohen Stapeln**; die Füllgradkurve nutzt **Zufallsbuchten mit ungleich hohen Stapeln** (4 Stapel, Höchsthöhe 5 und 6, jeder Container auf einen zufällig gewählten Stapel mit Platz, höchstens (Stapel − 1) · Höchsthöhe Container, dann finden die Container über einem Ziel immer einen Ausweichplatz).

## Befunde (gemessen, keine Behauptungen)

Alle Zahlen sind Messungen an den festen Buchten 0 bis 99 je Einstellung (Python-Zufallsfolge, `random.shuffle`), nachgerechnet in `tests/test_claims.py`, `tests/test_presets.py` und `tests/test_oracle_untergrenze_umstauen.py`.

**Wie weit trägt die Untergrenze?** (volle Buchten, Platz 2; Beweisquote der engsten Passung: „bewiesen“ heißt, sie trifft die Untergrenze):

| Stapel × Lagen | Optimum (Mittel) | Untergrenze (Mittel) | Optimum / Untergrenze | Lücke (Mittel / größte) | Untergrenze = Optimum | engste Passung: bewiesen optimal | optimal, nur mit Suche zu beweisen | verfehlt das Optimum |
|---|---|---|---|---|---|---|---|---|
| 3 × 2 | 1,74 | 1,41 | 1,24 | 0,33 / 1 | 67 | 67 | 31 | 2 |
| 4 × 2 | 2,25 | 1,95 | 1,16 | 0,30 / 1 | 70 | 70 | 30 | 0 |
| 5 × 2 | 2,83 | 2,51 | 1,13 | 0,32 / 1 | 68 | 68 | 32 | 0 |
| 3 × 3 | 5,05 | 3,53 | 1,42 | 1,52 / 4 | 19 | 19 | 68 | 13 |
| 4 × 3 | 5,81 | 4,53 | 1,32 | 1,28 / 4 | 20 | 20 | 71 | 9 |
| 5 × 3 | 6,94 | 5,69 | 1,22 | 1,25 / 4 | 25 | 25 | 70 | 5 |
| 3 × 4 | 8,92 | 5,68 | 1,59 | 3,24 / 8 | 1 | 1 | 60 | 39 |
| 4 × 4 | 10,44 | 7,44 | 1,42 | 3,00 / 7 | 4 | 4 | 48 | 48 |
| 5 × 4 | 12,52 | 9,49 | 1,32 | 3,03 / 7 | 3 | 3 | 57 | 40 |

| Frage | Befund |
|---|---|
| **Gilt die Untergrenze immer?** | In allen 900 Buchten der neun Einstellungen liegt sie nicht über dem Optimum. In den optimalen Folgen und in den Folgen der engsten Passung wird nie ein anfangs nicht blockierender Container bewegt (Satz 2). Die Tests prüfen das zusätzlich an allen optimalen Folgen aller 120 Buchten mit 3 Stapeln × 2 Lagen. |
| **Woraus besteht die Lücke?** | Aus Mehrfachhüben (Folgerung). In der optimalen Folge braucht ein blockierender Container im Mittel 1,42 (3 × 3), 1,32 (4 × 3), 1,59 (3 × 4), 1,42 (4 × 4) und 1,32 Hübe (5 × 4); 41, 30, 51, 40 und 31 % der Blocker werden mehr als einmal bewegt; ein einzelner Container wird höchstens 3-mal bewegt (bei 3 × 4: 4-mal). |
| **Wie hängt es von den Lagen ab?** | Bei 4 Stapeln trifft die Untergrenze das Optimum bei 2, 3 und 4 Lagen in 70, 20 und 4 von 100 Buchten; die mittlere Lücke wächst von 0,30 über 1,28 auf 3,00 Hübe. Bei 3 und 5 Stapeln fällt die Zahl ebenfalls mit den Lagen. |
| **Wie hängt es vom Platz ab?** (4 Stapel, Platz 1 / 2 / 3 / 4) | 3 Lagen: Optimum 5,86 / 5,81 / 5,81 / 5,81, Lücke 1,33 / 1,28 / 1,28 / 1,28. 4 Lagen: Optimum 10,89 / 10,44 / 10,39 / 10,39, Lücke 3,45 / 3,00 / 2,95 / 2,95; engste Passung optimal in 47 / 52 / 53 / 53 von 100. Nur der knappste Platz (1) verändert das Bild, ab Platz 2 praktisch nichts. |
| **Wie hängt es vom Füllgrad ab?** (Zufallsbuchten, 4 Stapel) | Höchsthöhe 5, 6 / 9 / 12 / 15 Container (30, 45, 60, 75 %): Lücke 0,05 / 0,50 / 1,29 / 2,74, Untergrenze = Optimum in 95 / 61 / 25 / 4 von 100. Höchsthöhe 6, 6 / 9 / 12 / 15 / 18 Container (25, 38, 50, 62, 75 %): Lücke 0,05 / 0,51 / 1,28 / 2,61 / 4,55, Untergrenze = Optimum in 95 / 60 / 29 / 9 / 2. Alle Buchten bewiesen. |
| **Trifft die Regel immer, wenn die Untergrenze trifft?** (Messbefund, kein Satz) | In den vollen Buchten: ja, ohne Ausnahme (in der Demo 900 Buchten der neun Einstellungen; in den Tests alle 120 Buchten 3 × 2 und 300 Buchten 3 × 3; der große Lauf vor dem Bau mit 14 300 Buchten steht im Planungsordner der Reihe). In den **Zufallsbuchten gibt es eine Ausnahme** (Höchsthöhe 5, 12 Container) unter 900 Buchten. |
| **Der einzelne Blocker** | 3 Stapel × 2 Lagen mit den Stapeln (1, 4), (5, 2), (6, 3) von unten nach oben: Untergrenze 1, Optimum 2, keine Hubfolge mit einem Hub leert die Bucht (die Tests zählen alle Folgen). Die kleinsten Nummern der drei Stapel sind 1, 2 und 3: Auf jedem anderen Stapel liegt unten etwas Früheres als der Blocker 4. |
| **Alle Buchten 3 × 2** | Von 120 Buchten (bis auf Vertauschen der Stapel): (Untergrenze, Optimum) = (0, 0) 15, (1, 1) 30, (1, 2) 15, (2, 2) 24, (2, 3) 20, (2, 4) 1, (3, 3) 7, (3, 4) 8; Untergrenze = Optimum in 76, Lücke 1 in 43, Lücke 2 in einer. |

**Presets** (Eigenschaften in `tests/test_presets.py`): „Alltag“ (4 × 3, Bucht 11: Untergrenze 4, Optimum 5), „Die Untergrenze trifft“ (4 × 3, Bucht 2: 4 und 4), „Große Lücke“ (4 × 4, Bucht 2: 6 und 11), „Der einzelne Blocker“ (3 × 2, Bucht 223: 1 und 2).

## Ehrliche Grenzen

- **Restricted:** Es werden nur Container über dem gesuchten bewegt. Wer auch andere bewegen darf, kann Hübe sparen; die Untergrenze zählt dann weiter Mindestbewegungen, das Optimum kann aber kleiner werden. Hier nicht gemessen.
- **Die ganze Abrufreihenfolge ist bekannt.** Bei unbekannter Reihenfolge ist „blockierend“ nicht zu bestimmen.
- **Zwei Familien, nicht vergleichbar belegt:** volle Buchten mit gleich hohen Stapeln (Hauptbucht, Lagenkurve, Platz) und Zufallsbuchten mit ungleich hohen Stapeln (Füllgradkurve). Gleicher Füllgrad ergibt ähnliche Lücken (4 × 3 bei Platz 2 entspricht 60 % Füllgrad bei Höchsthöhe 5: 1,28 gegen 1,29), das ist aber nur an dieser Stelle verglichen.
- **Nur 3 bis 5 Stapel und 2 bis 4 Lagen**; die Füllgradkurve nur für 4 Stapel. Platz und Füllgrad sind nur bei den genannten Einstellungen gemessen.
- **Der Messbefund „Untergrenze trifft ⇒ Regel trifft“ ist kein Satz.** Ein Beweis liegt nicht vor, und in den Zufallsbuchten gibt es eine Ausnahme.
- **Zahlen aus Zufallsbuchten:** Größenordnungen aus 100 festen Buchten je Zelle, keine Messung an einem echten Terminal oder Lager. Die Buchten hängen von der Zufallsfolge von Python (`random.shuffle`) ab; die CI prüft die Zahlen unter Linux.
- **Die Untergrenze und die Zerlegung sind hier selbst hergeleitet;** ob sie in der Literatur unter einem Namen stehen, wurde nicht geprüft.

## Verifikation

- **Kern:** Zählung der Blocker gegen Handrechnung (zwei Mini-Buchten) und gegen eine **eigene Zählung** im Orakel; unabhängiger Prüfer (`check_trace`) spielt jede Spur der drei Regeln und der optimalen Folge nach; Untergrenze und Optimum sind invariant gegen Vertauschen der Stapel; Untergrenze invariant gegen ordnungserhaltendes Umnummerieren; keine Regel liegt unter dem Optimum.
- **Orakel:** Optimum gegen eine **Breitensuche** über alle Buchtzustände (ohne Symmetriebruch, Untergrenze und Budget) auf 3 × 2 und 4 × 2 (Platz 2), 3 × 3 (Platz 1 und 2), 4 × 2 (Platz 4) und auf Zufallsbuchten; **Satz 1, Satz 2 und die Zerlegung** an jeder optimalen Hubfolge aller 120 Buchten 3 × 2 (Aufzählung), die Verteilung (Untergrenze, Optimum) über diese 120 Buchten, und die Beweisquote als Implikation auf allen 120 Buchten und einer 3-×-3-Stichprobe.
- **Zahlen im README:** jede Zahl der Befunde in `tests/test_claims.py` (Tabelle, Platz, Füllgrad, Zerlegung); die vorberechneten Kurven gegen eine frische Rechnung (`tests/test_presets.py`).
- **Verdikte:** reine Funktionen, jede Schwelle (50 und 10 Prozent, zehn Punkte der Lagenkurve, ein Hub der Füllgradkurve) und jede genannte Zahl an von Hand gesetzten Werten (`tests/test_verdicts.py`).
- **Presets und Oberfläche:** AppTest-Rauchtest (jeder Button, jeder Regler an Minimum und Maximum), Inhalt (Kennzahlen je Preset, Tabelle der Hübe, Platzregler, Permalink), Layout (Schnellstart oben, fester Kopf, aktives Preset hervorgehoben, jede Reglerwirkung), Footer, Laufzeit-Importe.
- **Abbildungen:** Farben je Rolle des Containers, feste Achsen, Kategorienachse des Histogramms, Zahlen der Kurven.

## Dateistruktur

| Datei | Zweck |
|---|---|
| `.github/workflows/tests.yml` | CI: Push, Pull Request, wöchentlicher Canary |
| `.gitignore` | venv, Caches, Streamlit-Secrets |
| `.streamlit/config.toml` | Streamlit-Einstellungen (keine Nutzungsstatistik) |
| `app.py` | Streamlit-App (Aufbau nach DEMO-PLAYBOOK §2) |
| `generate_precomputed.py` | erzeugt `uum_bands.json` (Lagen- und Füllgradkurve) |
| `requirements-dev.txt` | Laufzeit plus pytest |
| `requirements.txt` | Laufzeit-Bibliotheken (ungepinnt) |
| `uum_algorithm.py` | Kern: Abruf, Untergrenze, Regeln, exakte Suche, optimale Folge, Zerlegung, unabhängiger Prüfer |
| `uum_bands.json` | vorberechnete Kennzahlen der 100 festen Buchten je Zelle |
| `uum_constants.py` | Regler-Grenzen, feste Annahmen, Farben, Sonderbuchten, Presets |
| `uum_evaluation.py` | Analyse einer Bucht, Stichprobe, Kennzahlen, Kurven, Verdikte (reine Funktionen) |
| `uum_layout.py` | Fester Kopf (Stylesheet), Tabellen scrollen im eigenen Rahmen |
| `uum_presets.py` | Permalink (Begrenzen), Presets (Schnellstart in der Seitenleiste, aktives Preset hervorgehoben), Zufalls-Seed-Button |
| `uum_scenario.py` | Buchten (volle Buchten, Zufallsbuchten) |
| `uum_visualization.py` | Plotly-Abbildungen (Achsen gesperrt) |
| `tests/` | Handrechnung, Orakel, Randfälle, Behauptungen, Verdikte, Presets, Abbildungen, AppTest, Layout, Footer, Laufzeit-Importe |

## Bewusst nicht umgesetzt

- **Wie das Optimum berechnet wird:** Tiefensuche, IDA\* mit Untergrenze, Symmetriebruch, ILP und Branch and Price sind die folgenden Stücke der Reihe; hier ist die Suche ein Maßstab ohne Erklärung.
- **Schärfere Untergrenzen** (Konflikte zwischen Stapeln): spätere Stücke; der einzelne Blocker ist nur ein Vorgriff.
- **Beweis des Messbefunds** „Untergrenze trifft ⇒ Regel trifft“: nicht versucht.
- **Unrestricted-Variante, Einlagern, unbekannte Abrufreihenfolge, Pre-Marshalling, lernbasierte Verfahren:** spätere Stücke.
- **Größere Buchten, andere Stapelzahlen bei der Füllgradkurve:** nicht gemessen.
- **PDF-Export:** nicht vorgesehen.

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

125 Tests, rund zwei Minuten.

Gebaut mit Streamlit und Plotly.

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html).
