# SMT_PickupAnalytics

Eigenständige lokale Streamlit-Anwendung zur Analyse von Aufnahmefehlern der
SMT-Bestückautomaten. Bauteile werden für Continuous Improvement bewertet,
Feeder und Saugdüsen zur Priorisierung von Instandhaltungsuntersuchungen.

## Verbindliche Anforderungen und Entscheidungen

- Ausgliederung aus `Streamlit_collections/projects/SMT/MaintenanceInsights`.
  Das Originalprojekt bleibt unverändert.
- Lokaler Betrieb unter Windows mit Git Bash, eigene Python-3.11-Umgebung,
  kein Login, Bindung an `127.0.0.1:8501`; kein Deployment.
- Ausschliesslich lesende SQL-Zugriffe auf `profiler`. `profback` wird nicht verwendet.
  Laut Anwender enthält profiler aktuelle Produktionsabschnitte, profback ältere
  Abschnitte mit Wechsel ungefähr Oktober 2024. Überschneidungsfreiheit ist nicht
  gewährleistet. Daraus lässt sich kein garantierter Datenzeitraum ableiten.
- Bestehende Ranglisten und Gewichtungen zunächst übernehmen; keine neuen Prognosemodelle.
- DeviceComment ist laut Anwender eine verlässliche Bauteil-/Artikelnummer;
  Fidl und Nid sind eindeutige Kennungen physischer Feeder und Saugdüsen.
- Echte Credentials und lokale Settings bleiben lokal und werden nicht versioniert.
- Diese README ist die zentrale Übergabequelle bei Verlust der Chat-Historie.
  Bei jeder Änderung Anforderungen, Verhalten und Prüfstand aktualisieren und
  einen Eintrag zur Revision-History hinzufügen. Historische Einträge erhalten.

## Architektur und Datenfluss

`main.py` (Streamlit) → `data.py` → SQLAlchemy/pyodbc → SQL Server profiler.
`analysis.py` berechnet aus DataFrames die Ergebnisse ohne externe Zugriffe.
`device.sql` liest FUJIUSER.DeviceTrace; `nozzle.sql` liest FUJIUSER.NozzleTrace.
Die Abfragen enthalten weder Zeitfilter noch DISTINCT oder schreibende Befehle.
Die beiden Abfragen laufen nacheinander; ein gemeinsamer atomarer Produktionsstand
ist nicht garantiert. Es werden keine Archivdaten angehängt und keine Daten
automatisch dedupliziert: identische Zähler können legitime Produktionsabschnitte sein.

DeviceTrace liefert DeviceKey, McID, ModuleNo, StageNo, GroupKey, Class, SlotNo,
SubSlotNo, Fidl, Did, DeviceComment und die fünf Zähler. NozzleTrace liefert Nid,
PickupCount und die vier Fehlerzähler. Zusätzliche Gerätemerkmale aus DeviceTrace
werden bislang nicht für Filter oder Ursachenbewertung verwendet.

## Kennzahlen und fachliche Grenzen

Zuerst Zähler je Kennung summieren, danach Index berechnen. Keine Mittelung von
Einzelquoten. Alle Fehlerzähler werden zusätzlich ungewichtet in der Tabelle gezeigt.

| Kategorie | Kennung | Nenner | RejectParts | NoPickupCount | PickupErrors | VisionErrors |
|---|---|---|---:|---:|---:|---:|
| Bauteile | DeviceComment | FeedCount | 3 | 1 | 2 | 1 |
| Feeder | Fidl | FeedCount | 0 | 1 | 2 | 0 |
| Saugdüsen | Nid | PickupCount | 3 | 2 | 3 | 1 |

`WeightedErrors = Summe(Fehlerzähler × Gewicht)`.
`ErrorIndex = WeightedErrors / Nenner`; Darstellung als Dezimalwert, keine Prozentquote.
`UnweightedErrors` summiert die Fehlerarten mit Gewicht grösser null ohne Gewichtung.
Eine Überschneidung der Fehlerkategorien ist fachlich nicht geklärt; diese Summe
ist deshalb keine nachgewiesene Anzahl eindeutig fehlgeschlagener Aufnahmen.

Die Herkunft der historischen Gewichte ist laut Anwender nicht mehr nachvollziehbar.
Sie sind vorläufig und müssen fachlich neu beurteilt werden. Der Index kann über 1
liegen. Er erlaubt keine sichere Ursachenzuordnung zwischen Bauteil, Feeder und Düse.
Keine automatische Wartungsempfehlung, keine Ausfallwahrscheinlichkeit oder Restlebensdauer.

Nenner null ergibt einen fehlenden Index und Status „Nicht bewertbar“.
Fehlende/leere Kennungen werden mit ausgewiesener Zeilenanzahl ausgeschlossen.
Fehlende, negative, unendliche oder nicht numerische Zähler brechen die Aktualisierung ab.
Keine Mindeststichprobe: kleine Mengen können die Top 10 dominieren. Keine garantierte
Sortierung bei gleichen Indizes. Vollständige Tabellen erlauben die fachliche Prüfung.

## Installation und Start

Git Bash unter Windows, im Projektordner:

```bash
py -3.11 -m venv .venv
./.venv/Scripts/python.exe -m pip install -r requirements.txt
[[ -f .streamlit/settings.toml ]] || cp .streamlit/settings.example.toml .streamlit/settings.toml
[[ -f .streamlit/credentials.json ]] || cp .streamlit/credentials.example.json .streamlit/credentials.json
bash start.sh
```

Bei der lokalen Ausgliederung werden Umgebung und Credentials bereits eingerichtet.
Danach genügt `bash start.sh`. Alternativ `./.venv/Scripts/python.exe -m streamlit run main.py`.
PowerShell: `.\start.ps1`. Beenden mit Strg+C. WSL benötigt eine eigene Linux-Umgebung.
Erforderlich sind Netzwerk/VPN, SQL-Leserechte und Microsoft ODBC Driver 18 for SQL Server.
Die direkten Paketversionen einschliesslich numpy stehen in requirements.txt.

`.streamlit/settings.toml` verweist auf credentials.json; relative Pfade beziehen sich
auf den Settings-Ordner. `SMT_PICKUP_SETTINGS` kann eine andere TOML-Datei auswählen.
Credentials benötigen nur `nexim_database` mit server, user und password. Die Datenbank
ist bewusst fest auf profiler begrenzt. Verbindung: Encrypt=yes, TrustServerCertificate=yes,
Login-Timeout 15 Sekunden, Abfrage-Timeout 120 Sekunden. Die Zertifikatskonfiguration
entspricht dem bisherigen lokalen Betrieb.

## Oberfläche und Betrieb

„Daten laden / aktualisieren“ liest beide Tabellen neu. Kein automatisches Nachladen
bei Streamlit-Reruns. Ergebnisse bleiben nur im Arbeitsspeicher der Sitzung.
Je Kategorie: Top-10-Streudiagramm, x=FeedCount bzw. PickupCount, y=Fehlerindex,
Blasengrösse=WeightedErrors, Beschriftung=Kennung; darunter vollständige Tabelle.
Der Abrufzeitpunkt ist kein Produktionszeitraum. Bei Ladefehlern bleibt der letzte
erfolgreiche Stand mit Warnung sichtbar. Technische Fehlermeldungen enthalten keine
Verbindungszeichenfolge. Bei Fehlern Netzwerk, Treiber und lokale Konfiguration prüfen.

## Prüfung und offene Weiterentwicklung

```bash
./.venv/Scripts/python.exe -m unittest discover -s tests -v
./.venv/Scripts/python.exe -m pip check
./.venv/Scripts/python.exe tools/check_live.py
```

Der letzte Befehl liest echte Produktionsdaten und schreibt nur lokale aggregierte
Diagnostik unter diagnostics/ (von Git ausgeschlossen). Keine Produktionsdaten ändern.
Tests prüfen Gewichtung, Aggregation, Nullnenner, ungültige Zähler, fehlende Kennungen
sowie Laden und fehlgeschlagenes Aktualisieren der Oberfläche.

Offen: fachliche Neubeurteilung der Gewichte, Bedeutung/Überschneidung der Fehlerzähler,
geeignete Mindeststichprobe, tatsächlicher Datenzeitraum und mögliche Doppelzählungen
innerhalb profiler. Zeitreihen, Wartungshistorie und Prognosen sind spätere Erweiterungen
und gehören nicht zum aktuellen Ausgliederungsumfang.

## Erkenntnisse und empfohlene Massnahmen

Stand 02.11.2026: Der Anwender bestätigt, dass die Anwendung funktioniert und die
Ladezeit deutlich kürzer ist. Als wahrscheinliche Ursachen gelten der Wegfall der
profback-Abfragen und das Laden nur auf Knopfdruck statt bei jedem Streamlit-Rerun.
Ein gemessener Vorher-nachher-Vergleich liegt nicht vor; die Anteile dieser Ursachen
an der Beschleunigung sind deshalb nicht belegt.

Die folgende Liste ist ein priorisierter Massnahmenplan, noch keine implementierte
Funktionalität. Der aktuelle Funktionsumfang bleibt bestehen.

| Priorität | Massnahme | Zweck und Umsetzungshinweis | Status |
|---|---|---|---|
| 1 | Zählersemantik und identische Quellzeilen klären | Prüfen, ob Fehlerkategorien überlappen und welche Produktionsabschnitte die Zeilen repräsentieren. Identische Zeilen bis zur Klärung nicht automatisch entfernen. Befund und fachliche Entscheidung dokumentieren. | Offen |
| 1 | Einstellbaren Mindestmengenfilter ergänzen | FeedCount bzw. PickupCount als Mindeststichprobe verwenden, damit kleine Mengen die Top 10 nicht dominieren. Grenzwert fachlich festlegen; ausgeschlossene Einheiten weiterhin in der Gesamttabelle zeigen. | Empfohlen |
| 1 | Zusätzliche Rangliste nach absoluten Fehlerzahlen | Neben dem Index die grössten Verlustverursacher sichtbar machen. Ungewichtete Fehlerzahlen bzw. einzelne Fehlerarten verwenden; eine Summe nicht als eindeutig fehlgeschlagene Aufnahmen ausgeben, solange Überschneidungen ungeklärt sind. | Empfohlen |
| 1 | Fehlerarten getrennt visualisieren | RejectParts, NoPickupCount, PickupErrors und VisionErrors vergleichbar darstellen. Ursachenprüfung unterstützen und Abhängigkeit von vorläufigen Gewichten reduzieren. | Empfohlen |
| 2 | Detailansicht je Bauteil oder Feeder | Bereits geladene Maschinen-, Modul- und Slotinformationen zur Eingrenzung nutzen. Dafür Rohdaten gezielt in der Sitzung behalten; aktuell bleiben nur aggregierte Ergebnisse erhalten. Keine zusätzliche SQL-Abfrage erforderlich. | Vorgemerkt |
| 2 | CSV-Export gefilterter Tabellen | Befunde an Produktion und Instandhaltung weitergeben und Massnahmen dokumentieren. Kennungen beim Export erhalten; Filter und Abrufzeitpunkt nachvollziehbar machen. | Vorgemerkt |
| 3 | Zeitliche Entwicklung und Wartungsbezug prüfen | Verfügbarkeit von Zeitstempeln, Produktionsabschnittskennungen und Wartungsereignissen untersuchen. Erst danach Trends vor/nach Wartung oder Prognosen planen. | Datenbasis ungeklärt |

Empfohlener nächster Ausbau: Mindestmengenfilter, zusätzliche Rangliste nach
Fehleranzahl und getrennte Fehlerarten. Diese Auswertungen können mit bereits
geladenen Daten erfolgen und benötigen keine zusätzlichen Datenbankabfragen.
Vorläufige Gewichte weiterhin ausdrücklich kennzeichnen und fachlich neu beurteilen.
Ein hoher Index allein weist weder die wirtschaftlich wichtigste Einheit noch eine
bestimmte Fehlerursache nach. Eine Wartungsprognose benötigt zusätzliche fachliche
und zeitliche Grundlagen.

## Revision-History

| Revision | Datum | Änderung und Grund | Prüfung |
|---|---|---|---|
| 0.1 | 02.11.2026 | Eigenständige Anwendung; nur profiler gemäss Anwenderentscheidung; historischer Index offengelegt, Nullnenner korrigiert, Tabellen und sichere Aktualisierung ergänzt. Architektur, Anforderungen und Übergabe dokumentiert. | Fünf Tests, Paketprüfung, HTTP-Start und lesender Praxistest einschliesslich Oberfläche erfolgreich. |
| 0.2 | 02.11.2026 | Ergebnisse des Praxistests und identische Quellzeilen dokumentiert; aktuelle Streamlit-Breitenoption verwendet; numpy direkt gepinnt. | Oberflächentest nach Anpassung erneut geprüft. |
| 0.3 | 02.11.2026 | Anwenderbestätigung zur Funktion und verkürzten Ladezeit aufgenommen; priorisierten Massnahmenplan mit fachlichen Voraussetzungen, Status und empfohlenem nächstem Ausbau ergänzt. | Dokumentation gegen aktuellen Funktionsumfang geprüft; keine Codeänderung. |

## Aktueller Prüfstand: 02.11.2026

Die eigene Python-3.11-Umgebung und lokale Nexim-Konfiguration sind eingerichtet.
Fünf automatisierte Tests erfolgreich; `pip check` ohne Konflikte. Tatsächlicher
Streamlit-Prozess mit HTTP-Healthprüfung erfolgreich (tools/smoke_server.py);
der Test beendet nur seinen eigenen Prozess.

Lesender Praxistest auf profiler mit anschliessender AppTest-Oberflächenprüfung:

| Quelle / Kategorie | Ergebnis |
|---|---:|
| DeviceTrace | 141.952 Zeilen |
| NozzleTrace | 90 Zeilen |
| Bauteile | 2.957 Kennungen |
| Feeder | 502 Kennungen |
| Saugdüsen | 43 Kennungen |
| Fehlende Kennungen / Nullnenner | jeweils 0 |

Alle verwendeten Zähler bestanden die Prüfung auf numerische, endliche und nicht
negative Werte. Drei Diagramme und vollständige Tabellen wurden ohne App-Fehler
erstellt. Ein Fehler beim Nachladen wird zusätzlich mit synthetischen Daten geprüft.

DeviceTrace enthielt eine identische zusätzliche Zeile in den abgefragten Spalten,
NozzleTrace 17. Das ist kein Nachweis fehlerhafter Doppelzählung: insbesondere die
Nozzle-Abfrage enthält keine Produktionsabschnittskennung. Keine Zeilen entfernt.
Diese fachliche Klärung bleibt offen und kann die Interpretation der Summen beeinflussen.
Produktionsdaten wurden nicht verändert; keine Verbindung zu profback aufgebaut.
Aggregierter Bericht: diagnostics/live_check.json (lokal, von Git ausgeschlossen).

Lokales Git-Repository initialisiert; kein Commit, Remote oder Push erstellt.
