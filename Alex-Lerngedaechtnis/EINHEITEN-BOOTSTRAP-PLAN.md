# Ganze Durchgänge wiederziehen: Plan und Grenze

Aufgabe 5 wird ohne vorliegende echte 6-Stunden-/30-Minuten-Dateien vorbereitet.
Es werden keine Zahlen aus den dokumentierten Prozentwerten rückwärts erfunden.
Die reservierte 24-Stunden-Aufnahme ist ausdrücklich kein Eingang dieses Werkzeugs.

## Feststehende Auswertung

Profil 6h: Horizont 30, Profil 30min: Horizont 60. Quelle muss eine ausdrücklich
als 6h beziehungsweise 30min/30m benannte CSV mit JSON-Sidecar sein. Keine
Fortsetzungskette; keine 24h-Datei. Vor Berechnung muss koerper.pruefen bestehen.
Die bisherigen h=6, Schwelle 0,6, Erbegewicht 3 bleiben unverändert. Die Verfahren
sind Feste Regel, Grob mit festem Erbe, Grob mit Startwert, Je Signal mit festem
Erbe, Je Signal mit Startwert, Immer warnen und Nie warnen. 30min weist zusätzlich
die tatsächlich aufgezeichneten Gerätewarnungen aus; dieses Profil verlangt
Startwert und Blick 60. Der Prototyp aus Aufgabe 4 wird hier nicht ausgewählt.
Die Zeile „Immer warnen (eigene Signalreferenz)“ warnt im eigenen Signalnenner
immer, auch wenn ein fremdes Signal kritisch ist. Das ist ausdrücklich eine
stärkere signalweise Referenz als die grobe Gerätewarnung; die Gesamtwertung
warnt weiterhin nur in global nichtkritischen Takten.

Warnungen werden einmal in chronologischer Reihenfolge über die vollständige
Aufnahme berechnet. Die historische Punktwertung zählt wie vokabular.bewerte
alle nichtkritischen Takte beziehungsweise hohe Takte des eigenen Signals.
Sie kennzeichnet die unvollständige Zukunft am Aufnahmeende ausdrücklich.
Eine zweite, maßgebliche Bootstrapwertung schließt die letzten H Takte aus.
Kein synthetisches Zusammenkleben wiedergezogener Rohdaten, kein erneutes Lernen
an künstlichen Übergängen. Intervalle sind damit bedingt auf die beobachtete
Lerngeschichte und schätzen nicht die Unsicherheit einer neu trainierten Policy.

## Ganze Einheiten, vor Kenntnis der Warnqualität definiert

- Leckdurchgang: Beginn bei beobachteter steigender Flanke des LECK-Bits, bis
  unmittelbar vor der nächsten solchen Flanke, einschließlich Pause.
- Bremsrampe: entsprechend das BREMSE-Bit, einschließlich Pause.
- Hitzephase: zusammengefasster nicht-OK-Temperaturlauf nach laeufe(...,10),
  einschließlich anschließender Abkühl-/Ruhezeit bis zum nächsten Beginn.

Ein bei Aufnahmebeginn bereits aktiver Abschnitt ist linkszensiert und wird
nicht als vollständige Einheit übernommen. Die letzte noch offene Einheit
und Einheiten, deren Ende in der letzten H-Takt-Zukunft liegt, werden ebenfalls
nicht übernommen. Die Grenzen stehen als neutrale Taktzahlen in einheiten.csv.
Fehlende Reizbits oder weniger als zwei ganze Einheiten ergeben keine Intervalle.
Diese Gliederung ist eine explizite Annahme über Durchgänge, keine Entdeckung
physisch unabhängiger Ursachen. Historische Punktwerte und die auf vollständige
Einheiten beschränkte Wertung werden getrennt berichtet, mit Abdeckung.
Der Bericht nennt je Einheitenart die Anzahl ganzer Einheiten, ihre gesamten
Instrumenttakte und ihren Anteil an den L-H Originaltakten mit voller Zukunft.
Diese Zeitabdeckung ist nicht der jeweilige Signalnenner der Warn-/Trefferquote.

## Wiederziehen und Nenner

2000 Ziehungen, Zufallsstart 20261106, gepaart dieselben Einheiten für alle
Verfahren. Primär ganze Einheiten mit Zurücklegen; zusätzlich Sensitivität:
zirkuläre Blöcke von acht aufeinanderfolgenden ganzen Einheiten, gekürzt auf
die ursprüngliche Einheitenzahl. Die Blockvariante verlangt mindestens 16
ganze Einheiten; sonst keine Blockintervalle. Acht entspricht der bekannten
Größenordnung des Leckmusters, keine empirisch optimierte Blocklänge.

Je Wiederziehung zuerst Rohzähler summieren, dann Warnanteil=Warntakte/geeignete
Takte, Trefferquote=Treffertakte/Warntakte, Grundrate=Zieltakte/geeignete Takte.
Nicht Mittelwerte unterschiedlich großer Durchgangsprozente. Jedes Verfahren,
auch Immer warnen, steht in den Vergleichstabellen. Trefferquote bei null
Warntakten ist undefiniert, niemals null. Bei auch nur einer undefinierten
Wiederziehung wird das betreffende Intervall nicht ausgegeben; die Anzahl
definierter Ziehungen bleibt sichtbar. Punktweise 2,5-/97,5-%-Perzentile,
lineare Interpolation an (n-1)*p. Keine Korrektur für zahlreiche Vergleiche.

Je Signal mit Startwert wird zusätzlich zum maßgeblichen Vergleich gegen die
Feste Regel direkt gegen Je Signal mit festem Erbe gepaart, insbesondere für
Speicher 79 gegen 52 Prozent. Im 30min-Profil wird Gerät gegen Grob, Erbe fest
gepaart (dokumentierte 59/73 Prozent Warnanteil und 77/79 Prozent Treffer).
Die übrigen Vergleichsdifferenzen beziehen sich auf Feste Regel.

Das ist eine deskriptive Unsicherheits-/Sensitivitätsrechnung über eine bereits
ausgewertete einzelne Aufnahme. Lernzustand, langsame Erwärmung und acht tiefe/
acht flache Lecks können Einheiten abhängig machen. Ein gewöhnliches
Einheitenintervall allein belegt deshalb keine allgemeine Zuverlässigkeit.
Auch Blockintervalle mit wenigen Blöcken ersetzen keine unabhängigen Geräte-
oder Aufnahmewiederholungen. Die drei Einheitenarten werden nicht gepoolt.

## Ohne echte Daten prüfbar

Künstliche Orakel: identische Paare ergeben exakt null Differenz; bekannte
konstante Differenz bleibt exakt; ungleiche Einheitenlängen werden als Verhältnis
der Summen gewertet; keine Warnungen erzeugen undefinierte Trefferquote;
Einheitengrenzen und Zensierung sind handprüfbar; Fehlpaarung wird abgewiesen.
Integration nutzt ausschließlich künstlich erzeugte Gerätezeilen und Sidecars.
