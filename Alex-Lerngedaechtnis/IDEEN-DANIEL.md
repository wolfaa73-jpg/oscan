# OSCan: 24 mögliche Richtungen und ihre Gegenproben

6. November 2026 · Ideen für Alex und Claude · keine Umsetzung

Antwort auf den [Ideenauftrag](IDEEN-AUFTRAG.md), gelesen am bereinigten
Stand `6b5af19975b8c6c9fd0fc27c216887c28bcc94a2`. Diese Sammlung schlägt
Hypothesen vor. Die Versuche sind **nicht ausgeführt**, die Wirkungen nicht
nachgewiesen. Die 24-Stunden-Prüfaufnahme vom 6. November bleibt unangetastet.

Mein interessantestes Zielbild: **OSCan ist ein System, das aus Erfahrungen
kleine, widerrufbare Erwartungen bildet und damit entscheidet, was es behalten,
nachfragen, übertragen oder ausführen soll.** Es wächst, wenn neue Hardware
nützliche Fähigkeiten beiträgt; es wird reifer, wenn es für dieselbe Aufgabe
weniger erinnern und abstimmen muss. Das ist eine mögliche Richtung aus
[Alex’ Ideensammlung](../Ideensammlung%20Lernendes%20Betriebssystem%20mit%20verblassendem%20Ged%C3%A4chtnis.md), keine Behauptung über den heutigen Kern.

Aus [START-HIER](START-HIER.md), den angeforderten Abschnitten der
[Übergabe](UEBERGABE.md), den [Signalergebnissen](SIGNAL-ERGEBNISSE.md) und der
[Kostenuntersuchung](KOSTEN-UEBERGABE.md) nehme ich vier Stolpersteine mit:
Ein Erbe kann neue Erfahrung überstimmen; ein gemeinsames Zustandswort kann
gleichzeitige Signale verdecken; einfache Regeln bleiben starke Gegner;
ein günstigerer Kostenwert kann sehr viel mehr verpasste Ausfälle bedeuten.
Die synthetischen Ergebnisse belegen bislang keinen allgemeinen Nutzen am Gerät.

Die Reihenfolge folgt meiner Neugier. **Tragfähig** heißt: eine hinreichend
klare nächste Laborhypothese, nicht bereits bewiesen. **Offen** heißt: ein
entscheidender Mechanismus oder Nutzen ist unklar. **Spekulativ** heißt:
ein reizvolles Zielbild, dessen kleinste prüfbare Behauptung hier herausgelöst wird.
Manches schärft Alex’ vorhandene Ideen; eine Neuheitsbehauptung ist das nicht.

Für alle Gegenproben gilt: zunächst Papierfolgen oder neue künstliche Miniwelten,
keine Eingriffe in laufende Geräte. Methoden sehen nur rechtzeitig verfügbare
Informationen; verborgene Ursachen und zukünftige Ausgänge gehören allein zur
Prüfung. Wo ein Vorteil behauptet wird, zählen dieselben Aufgaben und Budgets,
einschließlich Metadaten, Kommunikation und abgelehnter Aufgaben. Ein einzelner
Widerspruch kann eine zugesagte Eigenschaft widerlegen; ein bestandener Spielzeugtest
belegt noch keinen Alltagsnutzen. Die bestehenden Kontrollberichte sind keine
unberührte Bestätigung für neue, daraus abgeleitete Ideen.

## 1. Das Gerät merkt, dass ihm ein Wort fehlt — offen

**Kern:** Ein Wort sollte sich teilen dürfen, wenn es zwei unterschiedliche
Folgen zusammenwirft: etwa „knapp bei wachsender Warteschlange“ und „knapp bei
bereits sinkender Warteschlange“. OSCan würde einen Begriff durch seinen Nutzen für Entscheidungen
bilden; ein menschenlesbarer Name käme erst danach.

**Billige Gegenprobe:** Zwei erfundene Kontexte bekommen dasselbe Zustandswort,
aber unterschiedliche Ausgänge; nur ein vorher sichtbares Merkmal unterscheidet
sie. Gegen eine feste Kontextaufteilung und „letzter Durchgang“ prüfen, außerdem
eine Welt ohne brauchbares Trennmerkmal und eine mit vertauschten Bedeutungen.
Verwerfen, wenn die automatische Teilung nur Vergangenes sortiert, in neuen
Folgen keinen zusätzlichen Entscheidungsnutzen bringt oder bei zufälligen
Merkmalen unbegrenzt Wörter erfindet; Wörter und ihr Verwaltungsaufwand zählen mit.
Die Teilungsregel wird vor den Prüffolgen eingefroren; alle Gegner erhalten dieselben Merkmale.

**Falls es trägt:** Das Vokabular würde an erlebten Unterschieden wachsen.
Verdeckte Ursachen bleiben trotzdem verdeckt; Wortwachstum erzeugt keine fehlende Information.

## 2. Das Gedächtnis schützt seine Gegenbeispiele — tragfähig

**Kern:** Neben „meistens gilt X“ bewahrt das Gedächtnis wenige kostspielige
Fehlentscheidungen oder Fälle, in denen eine angenommene Gültigkeitsbedingung
nicht trug. Eine Ausnahme widerlegt noch keine Wahrscheinlichkeitsaussage;
solche Gegenbeispiele hätten dennoch einen eigenen
Platz, ohne als immer gültiges Verbot die Rolle eines neuen starren Erbes zu übernehmen.

**Billige Gegenprobe:** Bei gleichem Speicherbudget eine häufig richtige Regel
mit einer seltenen Ausnahme, einem einmaligen Messfehler und späterem Bedeutungswechsel
füttern; Gegner sind ein reiner Häufigkeitszähler und ein einfacher Ringpuffer.
Die Idee fällt, wenn echte Ausnahmen beim Wiederkehren nicht besser erkannt werden
oder der geschützte Messfehler dauerhaft mehr Schaden anrichtet, als die Ausnahme spart.
Welche Beobachtung ein Messfehler ist, wird dem Lerner nicht vom Prüfer verraten.

**Falls es trägt:** Vergessen hieße, Wiederholungen stärker zu reduzieren als
Widersprüche. Eine Erinnerung dürfte lauten: „Das klappt meistens; in diesem Fall nicht.“

## 3. Schlaf macht aus Erlebnissen ein kleines Programm — offen

**Kern:** Verdichtung ersetzt ähnliche Episoden durch eine Regel, ihre
Gültigkeitsbedingungen und wenige Gegenbeispiele. Der Speicher würde nicht bloß
verblassen, sondern eine kürzere Beschreibung dessen finden, was für seine Aufgaben zählt.

**Billige Gegenprobe:** Eine handgebaute Folge mit Wiederholungen, Ausnahmen und
einem späteren Regelwechsel in ein festes Bytebudget packen; vergleichen mit
Ringpuffer und Übergangszählern bei gleichem Gesamtbudget. Auf vorher festgelegten
neuen Abfragen muss die Kurzform Entscheidungen und Ausnahmen innerhalb einer
festgelegten Fehlertoleranz erhalten; spart sie einschließlich Regel und Herkunft
keinen Platz oder glättet die entscheidende Ausnahme weg, ist diese Verdichtung verworfen.
Die Aufgabenart darf bekannt sein; konkrete Prüfabfragen und ihre Antworten
bleiben beim Verdichten verborgen, bei gleichen Entwicklungsinformationen für alle Verfahren.

**Falls es trägt:** „Schlafen“ hätte einen messbaren Ertrag: weniger Speicher
für erhaltene Fähigkeiten. Keine Behauptung verlustfreier Verdichtung beliebiger Erfahrungen.

## 4. Ein verhinderter Ausfall darf kein falscher Lehrmeister werden — tragfähig

**Kern:** Sobald eine Warnung eine Handlung auslöst, verändert OSCan seine
eigenen Lerndaten. Bleibt nach einer wirksamen Entlastung der Ausfall aus, ist
das allein weder Beweis für einen Fehlalarm noch für einen geretteten Auftrag.

**Billige Gegenprobe:** In einer kleinen künstlichen Welt führt Überlast ohne
Entlastung zum Abbruch, mit Entlastung nicht; in einer zweiten Welt ist dieselbe
Warnung grundlos. Der Prüfer kennt beide möglichen Ausgänge, der Lerner sieht
nur den tatsächlich entstandenen Verlauf samt Handlung. Verglichen werden
naives Nachlernen, markierte Eingriffe und eine feste Regel; fällt die Warnfähigkeit
wegen erfolgreicher Eingriffe zusammen oder werden alle Eingriffe unprüfbar zu
Erfolgen erklärt, ist das jeweilige Lernverfahren durchgefallen. Mindestens zwei
Fälle liefern trotz unterschiedlicher Alternativausgänge denselben beobachtbaren
Verlauf: Hier muss die Wirkung unbestimmt bleiben. Für einen Nutzentest darf
allein der Prüfer Eingriffe in der Modellwelt nach vorab festgelegtem Plan variieren.

**Falls es trägt:** Beobachtung, Eingriff und Ergebnis würden getrennte
Gedächtnisinhalte. Reine Aufzeichnungen erlauben nicht automatisch zu wissen,
was ohne Eingriff passiert wäre.

## 5. Knoten senden nur noch, worin sie sich irren — offen

**Kern:** Sender und Empfänger teilen eine kleine Erwartung; übertragen werden
Abweichungen, gelegentliche Vollzustände sowie Wörterbuch-, Sitzungs- und
Basiszustandskennungen, damit eine Lücke in der Folge erkennbar wird.
Das prüft Alex’ Leitgedanken direkt: Spart gemeinsames Gedächtnis tatsächlich Abstimmung?

**Billige Gegenprobe:** Eine kurze Nachrichtenfolge auf Papier mit verlorenem
Delta, Empfängerneustart und unterschiedlichen Wörterbuchständen durchspielen;
Gegner sind Vollmeldungen sowie Zustandswechsel mit periodischer Vollmeldung.
Ein falsch als bestätigt ausgegebener Zustand verwirft das Protokoll; ohne geringere
Gesamtbytes bei gleichem Aktualitätsziel gibt es keinen Kommunikationsgewinn.
Bestätigungen, Versionsaushandlung und Wiederabgleich zählen mit, Rechenaufwand separat.

**Falls es trägt:** Eine gemeinsame Erinnerung würde zur nutzbaren
Kommunikationsressource. Sie ersetzt keine Leitung; bei unklarem gemeinsamen
Stand braucht es einen verständlichen Vollzustand oder ausdrücklich „unbekannt“.

## 6. Das System überlebt seinen ersten Körper — spekulativ

**Kern:** OSCan könnte seine Kontinuität über Regeln, Erinnerungen und gültige
Auftragsrechte definieren, während der ursprüngliche ESP32 austauschbar wird.
Eine Kopie des Gedächtnisses dürfte dabei nicht automatisch eine zweite
Ausführungsberechtigung erzeugen.

**Billige Gegenprobe:** Zwei Papierknoten übernehmen nacheinander eine Rolle;
dann kommen Netztrennung, Aktorneustart und ein verspäteter alter Auftrag hinzu.
Die bestätigte Berechtigungsgeneration muss am Aktor erhalten bleiben oder die
Autorität zunächst als unklar gelten; dagegen steht ein einfacher fester Koordinator.
Akzeptiert der Aktor nach bestätigtem Wechsel noch einen Auftrag der alten
Generation, scheitert die Übergabe; verweigert sie bei jeder Störung
dauerhaft Arbeit, fehlt der behauptete praktische Gewinn.

**Falls es trägt:** Wachstum wäre ein überprüfbarer Rollenwechsel. Bei unklarer
Autorität darf Verfügbarkeit sinken; vollständige Erreichbarkeit und eindeutige
Aktionsrechte werden für eine Netztrennung hier nicht zugleich versprochen.

## 7. Erbe reist, ohne sich unterwegs zu vermehren — tragfähig

**Kern:** Knoten geben Erfahrungen weiter, behalten aber deren Ursprung und
Geltungsbereich. Ein Beleg, der über drei Nachbarn zurückkehrt, wird dadurch
nicht zu drei unabhängigen Bestätigungen.

**Billige Gegenprobe:** Ein einziger Beobachtungsbeleg läuft mehrfach im Kreis
A–B–C–A; danach kommen zwei tatsächlich neue Belege sowie ein Knoten mit
abweichendem Kontext dazu. Gegen bloßes Addieren und rein lokales Lernen prüfen:
Wächst die Belegzahl allein durch Umlauf oder überstimmt fremde Erfahrung lokale
Gegenbelege dauerhaft, ist die Übertragungsregel widerlegt; ohne Nutzen gegenüber
lokalem Lernen rechtfertigt sie ihren Metadatenaufwand nicht.

**Falls es trägt:** Ein Verbund könnte gemeinsam lernen, ohne aus Gerüchten
Gewissheiten zu machen. Herkunftskennungen lösen noch nicht das Problem absichtlich
gefälschter Quellen.

## 8. Träume versuchen, das eigene Wissen kaputtzumachen — spekulativ

**Kern:** Eine „Traumphase“ kombiniert bekannte Situationen absichtlich zu
Gegenbeispielen: Was wäre, wenn eine vertraute Reihenfolge anders endet?
Ihr Ergebnis sind Prüfaufträge, niemals zusätzliche Beobachtungsbelege.

**Billige Gegenprobe:** Für eine kleine, festgelegte Regelwelt dieselbe Zahl
Prüfversuche mit gezielter Rekombination, Zufall und einer einfachen Liste von
Randfällen erzeugen. Die Idee verliert, wenn sie weniger echte Regelbrüche findet,
nur unmögliche Abläufe produziert oder synthetische Geschichten unmarkiert das
Vertrauen in eine Regel erhöhen; Erzeugungs- und Prüfaufwand gehören ins Budget.

**Falls es trägt:** Innere Simulation wäre ein Werkzeug zum Zweifeln.
Das wäre eine technische Funktion, kein Nachweis menschlichen Träumens.

## 9. Alte Welten schlafen, statt vollständig zu verschwinden — offen

**Kern:** Wenn ein früherer Betriebszustand wiederkehrt, könnte OSCan einen
kleinen passenden Erinnerungsrest reaktivieren. Das unterscheidet „nicht mehr
aktuell“ von „endgültig ungültig“.

**Billige Gegenprobe:** Folgen A–B–A und A–B–C mit einem vorher sichtbaren
Kontextmerkmal vergleichen, zusätzlich einen irreführend ähnlichen Kontext.
Die Kürzel A/B/C kennt nur der Prüfer; sie sind keine Eingaben des Lerners.
Gegner sind ein einziges verblassendes Gedächtnis und feste Tabellen je Kontext,
alle unter demselben Speicherlimit. Verwerfen, wenn Wiedererkennen nicht schneller
hilft oder alte Regeln in neuen Situationen mehr Fehler verursachen als das Archiv spart.

**Falls es trägt:** OSCan bekäme mehrere kleine Erfahrungsräume, ohne sämtliche
Vergangenheit dauerhaft aktiv halten zu müssen. Ohne erkennbaren Kontext ist
eine passende Wiederkehr nicht vorhersagbar.

## 10. Ein Gedanke endet, wenn weiteres Denken nichts mehr ändert — spekulativ

**Kern:** Für ungefährliche Planung könnte „fertig“ bedeuten, dass sich die
gewählte Handlung durch zusätzliche Gedächtnisabrufe nicht mehr ändert.
Die mutige These ist ein Abschluss über Stabilität; eine feste Frist bleibt der Rückhalt.

**Billige Gegenprobe:** Ein winziges Netz widersprechender Erinnerungen erzeugt
stabile, pendelnde und vorübergehend ruhige Entscheidungen; Gegner ist eine feste
Zahl Abrufschritte. Verwerfen, wenn das Verfahren zu früh bei einer falschen
Entscheidung stehen bleibt, pendelt, die Frist reißt oder keine Arbeit spart.

**Falls es trägt:** Ein Teil der Rechenzeit ließe sich nach tatsächlichem
Änderungsbedarf vergeben. Ruhe ist keine Wahrheit und hebt eine Schutzgrenze nicht auf.

## 11. Die Erinnerung holt sich ihren Rechner — spekulativ

**Kern:** Nicht jede Anfrage geht zu einem zentralen großen Modell.
Gedächtnisbereiche melden, ob sie eine Aufgabe beantworten können, und ziehen
nur bei Bedarf einen stärkeren Knoten hinzu: Rechenleistung besucht relevantes Wissen.

**Billige Gegenprobe:** Drei simulierte Knoten besitzen unterschiedliche kleine
Erfahrungsbestände; prüfen mit lokalen Treffern, verteiltem Wissen und unbekannten
Anfragen. Gegner sind zentrale Abfrage und eine feste Routingtabelle.
Verwerfen, wenn Suchmeldungen, notwendige Fernzugriffe und Zusammenführung den
Kommunikationsvorteil auffressen oder bei gleichem Zeitlimit schlechtere Antworten liefern.

**Falls es trägt:** Alte kleine Geräte könnten sinnvolle Spezialisten bleiben.
Ein gemeinsames Dateisystem allein spart noch keine übertragenen Bytes.

## 12. Gelungenes Lernen schafft sich selbst ab — tragfähig

**Kern:** Wo eine einfache Regel dauerhaft genügt, könnte OSCan den aufwendigen
Lerner ruhen lassen. Es behält eine begrenzte Kontrollstichprobe, um eine spätere
Änderung bemerken zu können.

**Billige Gegenprobe:** Einen stabilen Abschnitt, einen abrupten Wechsel und
eine seltene Ausnahme gegen „immer lernen“, „feste Regel“ und „letzter Durchgang“
stellen. Verwerfen, wenn die eingesparte Arbeit durch verspätete Wiederaktivierung
und verpasste Ereignisse teurer wird; Kontrollbeobachtungen und deren Lücken müssen mitgezählt werden.

**Falls es trägt:** Fortschritt wäre auch weniger Modell, weniger Rechnen und
weniger Abhängigkeit. Einfache Sieger wären ein erwünschtes Ergebnis des Systems.

## 13. Die nächste gute Frage wird ein Scheduler-Auftrag — offen

**Kern:** Freie Rechenzeit könnte an die Beobachtung gehen, die eine anstehende
Entscheidung am ehesten ändert. Neugier hätte einen Preis und einen Zweck, statt
einfach besonders überraschende Signale zu sammeln.

**Billige Gegenprobe:** Zwei abfragbare Spielzeugsensoren: einer auffällig und
belanglos, der andere selten entscheidend; pro Runde ist nur eine Zusatzabfrage
erlaubt. Gegen reihum Abfragen und einen festen bevorzugten Sensor prüfen.
Kein geringerer Aufgabenverlust bei gleichem Abfragebudget widerlegt den
Mehrwert; zugeloste Fehlstellen prüfen, ob das Verfahren seine eigene Blindheit bemerkt.

**Falls es trägt:** Beobachten, Nachfragen und Lernen wären planbare Arbeit
des Betriebssystems. Unbeobachtete Zustände dürfen dabei nicht als „alles gut“ gelten.

## 14. „Ich weiß es nicht“ bekommt einen ausführbaren Vertrag — tragfähig

**Kern:** Unbekannt ist mehr als eine niedrige Warnwahrscheinlichkeit:
fehlende Beobachtung, widersprüchliche Belege und ein nie gesehener Kontext
brauchen unterscheidbare Gründe. Eine unbekannte Lage führt zu einer vorher
festgelegten Rückfrage oder Rückfallregel.

**Billige Gegenprobe:** Messlücke, echter Normalzustand und neuer Kontext werden
absichtlich ähnlich dargestellt. Gegen eine feste Rückfallregel prüfen;
Nachfragen, Wartezeit und abgelehnte Aufgaben sind nicht kostenlos.
Verwerfen, wenn „unbekannt“ die Statistik nur durch Auslassen schwieriger Fälle
verschönert oder ein veralteter Zustand als frische Entwarnung benutzt wird.

**Falls es trägt:** Geräte und Mensch könnten belastbar unterscheiden, ob
OSCan wenig Risiko sieht oder gerade keine verlässliche Sicht hat.

## 15. Das System lebt nach mehreren Uhren — tragfähig

**Kern:** Zeit seit einer Nachricht, Dauer eines Zustands und Zahl tatsächlich
beobachteter Ausgänge sind verschiedene Größen. Eine alte Messung kann unbrauchbar
sein, während eine seltene Erfahrung weiterhin nützlich ist.

**Billige Gegenprobe:** Zwei bis auf eingefügte Ruhezeiten gleiche Ereignisfolgen
und zwei Folgen mit gleicher Ausgangsfolge, aber verschiedener Verweildauer prüfen;
dazu eine Pause mit unbekannter Dauer. Gegen reine Taktalterung und reine
Ausgangsalterung vergleichen; Horizont und Kosten bleiben auf dieselbe physische
Zeit bezogen. Die Trennung scheitert, wenn bloßes Duplizieren oder Unterteilen
desselben zeitgestempelten Verlaufs ohne neue Beobachtung die Zahl belegter
Ausgänge erhöht, alte Live-Daten gültig bleiben oder die zusätzliche
Dauerinformation gegenüber der einfacheren Regel keinen Nutzen bringt;
reale Dauerunterschiede dürfen dagegen die Dauerschätzung verändern.

**Falls es trägt:** „Wann gilt etwas noch?“ würde eine ausdrückliche
Systemfrage. Die heutige Fortsetzungslücke wäre nicht mit gemessener Pausenzeit zu verwechseln.

## 16. Abrufen darf erhalten, aber nicht recht geben — tragfähig

**Kern:** Eine oft gebrauchte Erinnerung erhält mehr Platz oder bleibt leichter
zugänglich; ihre Beweiskraft wächst nur durch neue passende Beobachtung.
Das schärft den in START-HIER bereits genannten Unterschied zwischen Beleg und Behalten.

**Billige Gegenprobe:** Eine falsche Erinnerung tausendmal lesen, ohne eine
neue Beobachtung hinzuzufügen; danach echte Gegenbelege einspielen.
Gegen folgenlosen Abruf, einen gemeinsam verstärkten Wert und eine gewöhnliche
Speicherverwaltung nach letzter Nutzung prüfen:
Steigt bei identischem abgerufenem Belegsatz durch bloßes Lesen die
vorhergesagte Wahrscheinlichkeit oder blockiert
der beliebte Irrtum neue Belege bei gleichem Speicherbudget, ist die Trennung misslungen.

**Falls es trägt:** Das Gedächtnis könnte durch Nutzung geformt werden,
ohne die eigene Anzeige, Warnung oder Erklärung als Bestätigung zu missverstehen.

## 17. Ein Sprachmodell vererbt Fragen statt Gewissheiten — offen

**Kern:** Der Lehrer liefert einen prüfbaren Vorschlag mit Geltungsbereich,
Gegenbeispiel und erwarteter Beobachtung. Er darf einen Suchraum eröffnen;
Bestätigung kommt aus einer davon unabhängigen Prüfung.

**Billige Gegenprobe:** Handgeschriebene plausible, falsche und widersprüchliche
Lehreraussagen genügen zunächst; ein Modellaufruf ist dafür unnötig.
Gegen kein Erbe und eine kleine feste Ausgangsregel prüfen, mit neuen Fällen,
deren Ausgänge der Lehrer nicht festlegt. Verwerfen, wenn Formulierungswechsel
oder wiederholte Behauptung mehr Gewicht bringen, Fehler nicht revidiert werden
oder das Erbe netto mehr Prüfaufwand erzeugt, als es spart.

**Falls es trägt:** Ein späteres Sprachmodell könnte den Aufbau beschleunigen,
ohne dass sprachliche Sicherheit zu Geräteautorität wird.

## 18. Eine Erklärung muss die Entscheidung tatsächlich tragen — tragfähig

**Kern:** „Warum?“ verweist auf den verwendeten Zustand, passende Belege,
Erbanteil und die konkrete Entscheidungsregel. Eine zweite Antwort lautet:
Welche kleinste Änderung hätte zu einer anderen Entscheidung geführt?

**Billige Gegenprobe:** Entscheidungen eines winzigen Modells samt Beleglage
einfrieren, dann den genannten Grund entfernen oder gezielt ändern.
Gegen die bloße Ausgabe der Regel und Gewichte prüfen: Nennt die Erklärung
unbenutzte Belege oder stimmt die behauptete Entscheidungsänderung nicht,
ist sie widerlegt; ein dekorativer Fließtext wäre kein Gewinn.

**Falls es trägt:** Fehler würden prüfbar und diskutierbar. Erklärt wird zunächst
der Rechenweg, nicht automatisch die physische Ursache eines Ausfalls.

## 19. Denken muss sich sein Budget verdienen — offen

**Kern:** Vor einer Vertiefung könnte OSCan abschätzen, ob der erwartete Nutzen
zusätzliche Rechenzeit, Funk oder Speicherarbeit rechtfertigt. Ein kleiner Knoten
dürfte ausdrücklich bei einer einfachen Antwort bleiben.

**Billige Gegenprobe:** Eine Miniwelt mit einfachen und schwierigen Aufgaben
bekommt ein festes Gesamtbudget; vergleichen mit immer flach und immer tief rechnen.
Verwerfen, wenn Auswahlkosten, verpasste Fristen und schlechte Antworten die
Einsparung aufzehren oder schwierige Aufgaben nur aus der Wertung verschwinden.
Zunächst getrennte Arbeitszähler nutzen; ohne Messung heißen diese nicht Joule.

**Falls es trägt:** Ressourcenverbrauch würde das Verhalten mitbestimmen.
Ein biologisches Bild wie „Hunger“ wäre dafür nicht als Erklärung nötig.

## 20. Eine Erinnerung muss noch rechtzeitig handeln können — tragfähig

**Kern:** Statt nur „Ausfall bald?“ zu fragen, könnte OSCan fragen:
„Reicht die Zeit noch, um diesen Auftrag zu retten?“ Eine Reserve braucht
Anlaufzeit; ein als richtig gezählter Hinweis kann praktisch bereits zu spät sein.

**Billige Gegenprobe:** Eine erfundene Auftragsfolge auf zwei virtuellen
Pi-Arbeitern mit festgelegten Fristen und Reserveanlaufzeiten durchspielen;
Gegner sind immer bereite Reserve, nie bereite Reserve und feste Warnregel.
Verwerfen, wenn zusätzliche Vorwarnzeit weder rechtzeitig fertige Aufgaben
ermöglicht noch bei gleicher Aufgabenerfüllung Gesamtaufwand spart; Bereitschaft,
Wechsel und abgebrochene Arbeit zählen mit.

**Falls es trägt:** Die Vorhersagezeit bekäme einen Zweck. Eine WLED-Anzeige
könnte später die Entscheidung sichtbar machen; die eigentliche Erfolgsgröße
bliebe die erledigte Arbeit. Das belegt noch keine Eignung für Klipper-Eingriffe.

## 21. Drei Warnungen können dieselbe Handlung meinen — tragfähig

**Kern:** Temperatur, Speicher und Schleife bleiben als Beobachtungen getrennt,
werden aber vor der Aktion auf gemeinsame Folgen geprüft. Eine einzige Entlastung
kann mehrere Risiken beeinflussen und sollte nicht dreimal bezahlt werden.

**Billige Gegenprobe:** Zwei Spielzeugsignale mit gemeinsamer Ursache und ein
unabhängiges drittes gegen getrennte Ausführung und eine einfache Oder-Regel
stellen; auch einen Fall aufnehmen, in dem die Maßnahmen einander behindern.
Verwerfen, wenn Zusammenfassung eine notwendige andere Aktion verschluckt oder
bei gleichen Aufgaben keinen Vorteil gegenüber der Oder-Regel bringt.

Aufwand zählt einmal pro ausgeführter Aktion; Schäden beziehen sich auf vorher
abgegrenzte Aufgaben oder Folgen, nicht automatisch auf die Zahl ihrer Signalwarnungen.

**Falls es trägt:** Kosten würden an tatsächlichen Handlungen hängen.
Die vorhandenen Kosten pro Signal dürften weiterhin nicht ungeprüft als
Gesamtkosten eines Geräts addiert werden.

## 22. Neue Hardware bewirbt sich um eine Rolle — offen

**Kern:** Ein Knoten behauptet Fähigkeiten; OSCan vergibt eine kleine
Probeaufgabe und lernt, unter welchen Bedingungen die Fähigkeit brauchbar ist.
Eine Selbstauskunft oder Identitätsprüfung ersetzt dabei keine Leistungsprobe.

**Billige Gegenprobe:** Drei simulierte Arbeiter melden dieselbe Fähigkeit,
einer wird unter Last langsam, einer liefert falsche Ergebnisse; Gegner ist eine
feste Fähigkeitsliste mit Zeitlimit. Mit einer unabhängig prüfbaren Aufgabe testen:
Werden schlechte Ergebnisse übernommen oder ist die Eignungsprüfung teurer als
ihr Gewinn bei neuen Aufträgen, trägt diese Rollenvergabe nicht.

**Falls es trägt:** Wachstum könnte auf nachgewiesenen Beiträgen beruhen.
Das erfindet weder elektrische Gerätespezifikationen noch unbekannte Treiber.

## 23. Vergessen muss auch einen Widerruf überleben lassen — tragfähig

**Kern:** Natürliches Verblassen und ausdrücklich angeordnetes Löschen sind
verschiedene Dinge. Ein alter Knoten oder ein Backup darf gelöschte Inhalte und
daraus abgeleitete Zusammenfassungen nicht unbemerkt wieder einführen.

**Billige Gegenprobe:** Ausschließlich erfundene Einträge auf zwei Papierknoten
verteilen, einen trennen, auf dem anderen löschen und verdichtete Ableitungen
einbeziehen; danach alten Stand zurückspielen. Gegen bloße Alterslöschung prüfen:
Tauchen Inhalt oder erkennbare Ableitung wieder auf, scheitert das Verfahren;
unbegrenzte dauerhafte Speicherung des gelöschten Inhalts als Löschbeweis wäre ebenfalls ein Fehlschlag.

**Falls es trägt:** Das System bräuchte einen inhaltsarmen Widerrufsmechanismus
und Regeln für alte Sicherungen. Physisch unerreichbare Kopien kann der laufende
Verbund nicht nachträglich löschen; diese Grenze müsste sichtbar bleiben.

## 24. Das System bemerkt, dass sein Beobachten den Körper verändert — tragfähig

**Kern:** Messen, Protokollieren und Erklären verbrauchen selbst Ressourcen.
OSCan könnte seinen Beobachtungsaufwand als mögliche Ursache einer auffälligen
Temperatur oder Schleifenzeit mitführen, statt jeden eigenen Effekt als äußere Störung zu lernen.

**Billige Gegenprobe:** Einer künstlichen Grundlast einen bekannten Aufschlag
für Abfragen und Berichte hinzufügen; gleiches Ereignisszenario mit sparsamer,
häufiger und zeitweise abgeschalteter Zusatzbeobachtung vergleichen.
Gegner ist eine feste niedrige Abfragerate. Verwerfen, wenn das Verfahren eine
selbst erzeugte Belastung nicht erkennt oder echte Störungen vorschnell als
Beobachtungseffekt weg erklärt; erkannte Ausfälle und Fristverletzungen zählen mit.

**Falls es trägt:** „Körperwahrnehmung“ würde die eigene Tätigkeit einschließen.
Ein späterer Gerätetest müsste diesen Aufwand tatsächlich messen.

## Was ich zuerst prüfen würde — höchstens drei Versuche

**1. Verhinderte Ausfälle, Idee 4.** Zuerst klären, was eine richtige Entscheidung
ist, sobald sie Folgen hat. Ein kleines Tabellenmodell mit wirksamer, wirkungsloser
und unnötiger Entlastung reicht als erste Gegenprobe; es kann einen grundlegenden
Lernfehler sichtbar machen, bevor wir weitere Warnschwellen verbessern.
Prüfgröße: tatsächlicher Aufgabenverlust plus Aufwand der Aktion, nicht bloß
die nachträgliche Trefferquote der Warnung. Die verborgenen Alternativausgänge
bleiben beim Prüfer; bei identischen beobachtbaren Verläufen ist eine unbestimmte
Wirkung die richtige Antwort. Das wäre eine methodische Voraussetzung für spätere echte Aktionen.

**2. Fehlende Wörter, Idee 1.** Das ist der größte unmittelbare Hebel zwischen
dem heutigen kleinen Zustandsraum und Alex’ wachsender interner Sprache.
Zuerst nur einen automatisch vorgeschlagenen Split zulassen und mit einer
einfachen festen Kontexttabelle vergleichen. Drei neue Miniwelten vorsehen:
brauchbares Merkmal, bedeutungsloses Merkmal, späterer Bedeutungswechsel.
Ein Split zählt nur, wenn er auf neuen Folgen einen vorher festgelegten
Entscheidungsverlust senkt und sein zusätzlicher Speicher im Budget bleibt.
Ohne diesen Gewinn bleibt die feste Tabelle die bessere Lösung.

**3. Verdichten im Schlaf, Idee 3.** Das prüft am direktesten, ob verblassendes
Gedächtnis mehr sein kann als eine andere Alterungsformel. Als Start genügen
wenige von Hand konstruierte Episoden, eine vorgeschlagene Regel und geschützte
Gegenbeispiele; noch kein lernender Compiler. Erst prüfen, ob diese Darstellung
bei festem Bytebudget relevante Antworten besser erhält als Zähler und Ringpuffer.
Scheitert diese handgebaute Kurzform, sollte genau diese Darstellung zunächst
nicht automatisiert werden; andere Verdichtungsformen bleiben dadurch offen.

Vor einem späteren Lauf jeweils schriftlich einfrieren: **beobachtbare Eingaben,
Handlung und Ziel, Vergleichsregeln, Speicher-/Rechenbudget, Fehlerkosten,
Abbruch-/Ablehnungskriterium und getrennte Entwicklungs- und Prüffälle**.
Konkrete Zahlen werden vor der Durchführung gewählt, nicht nach dem Ergebnis;
dieses Ideenpapier ist noch kein fertiger Versuchsplan. Die reservierte
24-Stunden-Aufnahme wird durch keinen dieser Vorschläge zur Spielwiese.

Für alle drei reicht zunächst ein vom laufenden System getrenntes Gedanken-
beziehungsweise Labormodell. Ein eigener Kernel wäre dafür noch kein Erkenntnisgewinn.
Wenn diese kleinen Verträge tragen, könnten daraus später Betriebssystemfunktionen
entstehen: **Beobachtung annehmen, passende Erfahrung abrufen, Geltung prüfen,
Aufmerksamkeit vergeben, Handlung erlauben und Wissen gezielt vergessen.**
