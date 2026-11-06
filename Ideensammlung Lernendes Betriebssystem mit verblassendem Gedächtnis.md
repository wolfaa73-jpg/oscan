# Ideensammlung: Lernendes Betriebssystem mit verblassendem Gedächtnis

Stand: 3. November 2026. Gedankensammlung aus einem langen Gespräch, noch keine Ausführung. Vieles ist Spekulation und als solche gekennzeichnet.

**Versuche:** Zum ersten Schritt gibt es ein Lernlabor mit Code im Ordner `Alex-Lerngedaechtnis`. Was dort geprüft wurde, steht am Ende unter „Versuchsstand“, jeweils mit seiner Herkunft.

**Leitgedanke:** Vorhandene Hardware soll durch eine schlankere interne Kommunikation in die Lage versetzt werden, sich über die bestehenden Geräte weiter auszubreiten, ohne dass neue Chips nötig sind. Der Gewinn liegt dort, wo heute Zeit in Warten, Kopieren und Abstimmen verloren geht (Protokolle, Datenformate, die Frage, was überhaupt übertragen werden muss). Die Grenze setzt die Bandbreite und Laufzeit der Leitung selbst. Alle weiteren Ideen in diesem Dokument hängen an diesem Gedanken.

**Kerngedanke:** Es gibt kein Modell, das auf einem Betriebssystem läuft, sondern ein Betriebssystem, das selbst denkt. Das Modell steckt im Betriebssystem, es gibt nur ein Ding. Damit entfällt die Schnittstelle zwischen Modell und Betriebssystem, und die einzige Grenze, über die gesprochen werden muss, ist die zur Hardware.

## Bedarf und Zielprodukt

Bevor die Technik festgelegt wird, soll geklärt werden, unter welchen Umständen das System benutzt wird und was am Ende der Reise für ein Produkt steht. Bisher festgehalten:

- **Lokal:** Die Daten bleiben bei Alex, auf eigenen SSDs und dem eigenen Cluster, ohne Cloud-Zwang. Gegenseite: Ausfälle und Backups liegen in eigener Verantwortung. Bei einem Gedächtnis, das sich ständig verändert, ist ein Backup schwieriger als bei Dateien, und weil es sehr persönlich ist, muss es verschlüsselt sein.
- **Erweiterbar:** Das System soll mit Alex mitwachsen und nicht nach drei Jahren an eine Grenze stoßen, nach der alles ersetzt werden muss. Weg dorthin: Teile austauschbar halten (Knoten kommen und gehen, ein Modell wird durch ein besseres ersetzt), während das Gedächtnis bleibt. Voraussetzung ist ein offenes Format für das Gedächtnis und eine stabile Schnittstelle dazu.
- **Spannung:** Lokal heißt, dass Modelle auf eigener Hardware laufen müssen, und die wachsen schneller als das Budget. Abfedern lässt es sich nur, indem das Modell wechselbar ist, ohne das Gedächtnis zu verlieren.

Noch nicht beantwortete Fragen zum Bedarf: Wer benutzt es (nur Alex, Familie, Verein)? Wobei soll es helfen (Alltag, Arbeit, Träumen und Bauen, Training)? Wo läuft es (zuhause, am Körper, unterwegs)? Was soll es können, was heutige Geräte nicht können, und was soll es ausdrücklich nicht tun?

Am Ende soll ein Bild vom fertigen Produkt stehen, das sich in zwei Sätzen beschreiben lässt. Danach entscheidet sich, ob ein eigenes Betriebssystem nötig ist oder ob eine Schicht auf Linux reicht.

## Aufrüsten: Wachsen statt Ersetzen

Alex' Gedanke: Wenn das System stabil und flüssig läuft, braucht es mit der Zeit keinen schnelleren Prozessor. Aufgerüstet wird nur dort, wo die Gedanken und Erinnerungen liegen, also beim Speicher. Und: Der Mensch tauscht sein Gehirn auch nicht aus.

- **Zwei Sichtweisen:** Bei klassischen Modellen sind Gedächtnis (wächst, bleibt) und Modell (austauschbar, braucht Rechenleistung) getrennt, das Modell setzt dann die Grenze. Beim Menschen gibt es diese Trennung nicht: Dasselbe Gehirn wächst durch Erfahrung, was gelernt wird, verändert die Verbindungen selbst.
- **Ziel:** Ein System ohne Trennung zwischen Gedächtnis und Modell. Wachsen und Denken sind dasselbe, und Aufrüsten heißt, dem System mehr Platz zum Wachsen zu geben (mehr Speicher, mehr Knoten), während alles Bestehende bleibt. Das passt zum Wunsch, nicht nach drei Jahren alles ersetzen zu müssen. Es muss kein klassisches Modell sein, denn die Idee ist, alles neu zu denken.
- **Haken:** Wer die Gewichte im Betrieb verändert, riskiert, dass Altes überschrieben wird (katastrophales Vergessen). Das Gehirn hat dafür Gegenmittel, etwa das Einfestigen im Schlaf. Entsprechung hier: der Hintergrundprozess, der nachts verdichtet und aussortiert.
- **Offen:** Wie viel Denkleistung wird später gebraucht, und wie wird gewährleistet, dass Neues das Bestehende nicht zerstört?

## Ausgangspunkt

Alex' Überzeugung: Künstliche Intelligenz braucht keine hochspezialisierte Hardware, sondern einen Schritt auf Software-Ebene, der über das binäre, adressbasierte Rechnen hinausgeht. Anlass war die Frage, warum wir nicht mit Tieren sprechen können, und der Vergleich mit Aaron (der Katze): Verständigung entsteht durch gemeinsamen Kontext, Bindung und etwas, das dem Gegenüber wichtig ist, nicht durch Grammatik.

## Was heutigen Systemen fehlt

- **Lernen im Betrieb:** Sprachmodelle sind nach dem Training eingefroren und lernen im Gespräch nur im Kontext, nicht in den Gewichten.
- **Eine Welt mit Folgen:** Lebewesen haben Hunger, Wärme, Angst. Verstehen ist bei ihnen an etwas gekoppelt, das ihnen wichtig ist.
- **Ein dauerhafter Zustand:** Heutige Betriebssysteme sind für Programme gebaut, die starten, etwas tun und enden.
- **Gedächtnis als Kernfunktion:** Heute ist es eine Datenbank neben dem System, nicht dessen Speicherverwaltung.

## Kernidee: Gedächtnis ist kein RAM

RAM funktioniert über Adressen. Das Gehirn kennt keine Adressen, man erinnert sich über Ähnlichkeit. Gedankenspiele dazu:

- **Erinnerung als Zustand:** Ein Gedanke ist ein Muster, in das das System zurückfällt, wenn ein Teil davon angestoßen wird (Vorbilder: Hopfield-Netze, Sparse Distributed Memory von Kanerva).
- **Abruf verändert den Inhalt:** Erinnerung wird beim Abrufen neu geschrieben und driftet. Bei RAM wäre das ein Fehler, hier das Prinzip.
- **Vergessen als Eigenschaft des Stoffs:** Ungenutztes verblasst von selbst, Verdichtung (aus vielen Erlebnissen wird eine Regel) ist der Normalzustand.
- **Speicher und Rechnen am selben Ort:** Kein zentraler Pool und keine Leitung dazwischen, die zum Flaschenhals wird.
- **Abschluss eines Gedankens als Zustand:** Ein Gedanke ist zu Ende, wenn das System zur Ruhe kommt, nicht wenn ein Endzeichen erzeugt wird.

## Betriebssystem statt BIOS

Das BIOS (UEFI) initialisiert nur die Hardware und startet den Bootloader. Die Entscheidungen, was wann läuft, was im Speicher bleibt und was vergessen wird, trifft das Betriebssystem. Ein lernendes OS bräuchte andere Grundannahmen:

- Dauerhafter Zustand statt Programmstart, keine neuen Gespräche, sondern eine durchgehende Geschichte.
- Gedächtnis als Teil der Speicherverwaltung, mit Bewerten, Verdichten und Vergessen wie im Schlaf.
- Lernen im Hintergrund, ähnlich einem Scheduler.
- Knappe Ressourcen (Energie, Rechenzeit), die das Verhalten beeinflussen, als Entsprechung zu "etwas, das ihm wichtig ist".

BIOS und OS zusammen gedacht: Die unterste Software entscheidet, wie sich die Hardware verhält. Das "Fühlen der Bits" ist ausdrücklich metaphorisch gemeint.

## Speicher auf der SSD

Idee: Die Arbeit des Gedächtnisses findet auf der SSD statt, nicht im RAM.

- **Dafür:** Flash behält Inhalte ohne Strom, speichert Ladung in mehreren Spannungsstufen (also von Natur aus nicht rein binär), und die Ladung leckt mit der Zeit. Das "Vergessen im Material" ist schon vorhanden und wird heute von der Firmware unterdrückt.
- **Vorbilder:** Computational Storage (Rechnen im Laufwerk), Apples Arbeit "LLM in a flash".
- **Hürden:** Tempo (NVMe grob 7 bis 14 GB/s, deutlich weniger als RAM, höhere Latenz) und Verschleiß durch Schreibvorgänge. Ein Gedächtnis, das sich bei jedem Abruf umschreibt, verbraucht Zellen.
- **Ansatzpunkt:** Die Flash Translation Layer in der Firmware des Laufwerks. Offene Laufwerke (OpenSSD, Open-Channel-SSDs) gibt es meines Wissens nur in der Forschung.

## Mehrere Gehirne an mehreren SSDs

Die CPUs sind nicht der Ort des Denkens, sondern Besucher. Das Gedächtnis liegt in der Mitte und gehört niemandem.

- **Kommunikation durch das Gedächtnis (Stigmergie):** Ein Knoten schreibt, ein anderer liest später. Das umgeht den Flaschenhals der Leitungen, an dem verteilte Systeme (zum Beispiel 10.000 ESP32) scheitern.
- **Widerspruch als Rohstoff:** Wenn zwei Knoten dieselbe Erinnerung umschreiben, ist die Frage, welche Version sich durchsetzt, ein Teil des Systems.
- **Rollen:** schnell und oberflächlich, langsam und gründlich, und ein Knoten, der nachts verdichtet und aussortiert.
- **Mehrere Gedächtnisse:** schnell und flüchtig (Arbeitsgedächtnis), groß und träge (Langzeit), eines, das gezielt altert.
- **Historischer Anschluss:** Blackboard-Systeme aus der KI-Forschung der 1980er und Tupelräume (Linda). Neu wäre ein Brett, das selbst verblasst, driftet und sich verdichtet.

## Realistische Einordnung zur Hardware

- Der Engpass ist oft die Architektur, nicht der Chip (Hardware-Überhang): Quantisierung, Mixture of Experts, Destillation haben Modelle stark verkleinert.
- Eine Architektur, die für langsame Leitungen entworfen ist (Experten pro Knoten, wenig Austausch zwischen Schichten), würde Alex' Cluster sinnvoll machen.
- Aufteilung nach dem Vorbild von Kortex und Hippocampus: ein großes eingefrorenes Basismodell plus eine kleine lernende Schicht lokal (zum Beispiel LoRA-Adapter). Spekulation, technisch machbar.
- Harte Grenze: Neues Fundament-Wissen zu trainieren braucht weiterhin enorm viel Rechenleistung. Anpassen und Weiterlernen geht auch auf kleiner Hardware.
- Zur Speichergröße: Etwa 0,5 bis 0,6 Byte pro Parameter bei 4-Bit-Quantisierung. Bei Mixture-of-Experts zählen für den Speicher alle Parameter, für die Geschwindigkeit nur die aktiven.

## Umsetzung auf heutiger Prozessorarchitektur (Skizze)

Als Schicht obendrauf, ohne den Prozessor anzufassen:

- Ein Dienst verwaltet das Gedächtnis: Einträge mit einer Stärke, die mit der Zeit sinkt und bei jedem Abruf steigt.
- Abruf über Ähnlichkeit (Vektorsuche) statt über Adressen, läuft auf SIMD-Einheiten beziehungsweise der GPU.
- Ein Hintergrundprozess verdichtet ähnliche Einträge und löscht zu schwache, auf einem eigenen Kern oder Knoten.
- Speicher auf der SSD per Memory-Mapping, mehrere Knoten über ein gemeinsames Dateisystem im Netz.
- Erster Prototyp: kleine Python-Anwendung auf dem OpenClaw-Cluster.

## Die Schnittstelle zwischen Betriebssystem und Hardware

Alex' Ziel: den Aufwand der Kommunikation zwischen Betriebssystem und CPU beziehungsweise Hardware reduzieren, mit einer Sprache, die es erlaubt, die Komponenten des Computers harmonischer zu nutzen. Die Grenze soll nicht mehr als fester Vertrag aus Befehlssatz, Adressräumen und Interrupts gedacht werden, sondern als Sprache, die zur Art des Denkens passt.

**Wo der Aufwand heute entsteht:** Wechsel zwischen Programm und Kernel kosten Hunderte bis Tausende Takte, dazu kommen Interrupts, Verwaltung von Speicherseiten und das Kopieren von Daten zwischen den Schichten.

**Bestehende Ansätze in diese Richtung:**

- Kernel umgehen (DPDK, io\_uring): Programme sprechen über gemeinsame Warteschlangen direkt mit der Hardware.
- Gemeinsamer Speicher statt Nachrichten: Ringpuffer zwischen Betriebssystem und Gerät, bei Netzwerkkarten und NVMe-Laufwerken Standard.
- Library-OS und Unikernel: Betriebssystem und Anwendung werden ein Programm, die Grenze entfällt.
- Arbeit in die Hardware verlagern (SmartNICs, Computational Storage): Das Gerät erledigt Aufgaben selbst.

**Idee einer Schnittstellensprache:** Anlass war das Gerücht, KI-Systeme entwickelten eine eigene Sprache untereinander. Real ist, dass Agenten, die gemeinsam optimiert werden, manchmal in ein Kauderwelsch abdriften, das nur sie verstehen, weil niemand Menschenlesbarkeit verlangt hat. Das zeigt, dass Maschinen effizientere Zeichen finden als unsere Sprache.

Eine Sprache für ein lernendes System würde auf Absichten und Ähnlichkeit statt auf Einzelbefehle setzen. Beispiele (Gedankenspiel, keine bestehende Syntax):

- "Gib mir, was dem hier gleicht."
- "Halte das, bis es verblasst."
- "Ruf die anderen Knoten dazu."

Hardware oder Firmware würde das in Bewegungen übersetzen. Gemeint ist ein Befehlssatz oder eine Schnittstellenbeschreibung, keine natürliche Sprache. Der Gewinn liegt darin, dass mehr Bedeutung in weniger Schritten übertragen wird.

**Ansatzpunkte, an denen man an der Grenze drehen kann:** der Befehlssatz (welche Operationen die Hardware kennt), die Speicherabfrage (wie Daten gefunden werden), die Zeit (gemeinsamer Takt oder Ereignisse) und die Meldewege (wie die Hardware dem Betriebssystem etwas mitteilt).

## Kompression: ein Vertrag über gemeinsames Wissen

Kompression funktioniert, indem beide Seiten sich auf etwas einigen. Alles, was beide ohnehin wissen, muss nicht mehr übertragen werden. Beispiel: In einer Nachricht die Vokale oder einen Buchstaben weglassen, weil der Empfänger sie automatisch auffüllt. Das klappt, solange die Erwartung eindeutig auffüllt, und geht verloren, wo sie mehrdeutig ist ("Rnd" könnte Rand, Rind oder Rund sein).

- Technisch ist das die Idee hinter fast allen Verfahren: ein gemeinsames Wörterbuch, und im Extremfall fließen nur noch die Überraschungen.
- Bei Sprachmodellen fließen zwei Arten von Daten: Gewichte (einmal geladen, schon quantisiert) und Zwischenergebnisse (Aktivierungen), die bei jedem Token über die Leitung gehen. Dort liegt das Potenzial, zum Beispiel durch 8- oder 4-Bit-Werte oder durch Übertragen nur der wichtigsten Werte. Das ist die Idee aus dem Projekt "MP3 für Aktivierungstensoren".
- Preis: Verlustfreie Verfahren sparen bei fast zufällig aussehenden Zahlen wenig. Verlustbehaftete sparen mehr, kosten aber Genauigkeit, die sich über viele Schichten summiert. Dazu kommt die Rechenzeit fürs Packen und Entpacken, die bei schwachen Knoten (Pi 3B) selbst zum Flaschenhals werden kann.
- Faustregel: Komprimieren lohnt sich, wenn die gesparte Übertragungszeit größer ist als die Zeit fürs Packen und Entpacken.

Für die Schnittstellensprache heißt das: Je mehr Hardware und Betriebssystem voneinander wissen, desto kürzer darf die Sprache werden. Die Kunst liegt im geteilten Vorwissen, nicht im Packalgorithmus.

## Visuelle Schiene für Mensch und System

Zwischen Mensch und System ist eine visuelle Anzeige fast notwendig, zwischen Betriebssystem und Hardware nicht. Ein Gedächtnis, das driftet, verblasst und sich verdichtet, ist von außen unsichtbar. Ohne Anzeige sieht man nicht, was gerade stark ist, was verblasst und wo Knoten sich widersprechen. Gebraucht wird ein Fenster auf den Zustand, nicht auf einzelne Einträge.

- Der Thinking Blinking Cluster ist dazu ein Ansatz: Helligkeit für die Stärke einer Erinnerung, Verblassen als echtes Abdunkeln, Farbe für Widerspruch zwischen Knoten.
- Vorbehalt: Die Anzeige darf das System nicht belasten. Sie soll sich nur das nehmen, was ohnehin fließt, sonst kostet sie die Kommunikation, die gesenkt werden soll.
- Vergleich Auto: Die meisten Menschen wissen nicht, was eine Direkteinspritzung tut, und das ist in Ordnung. Entscheidend ist, dass Fehler sichtbar werden (Warnlampe) und dass es jemanden gibt, der hineinschauen kann. Die visuelle Schiene wäre das Armaturenbrett.

## Wofür der Computer in Zukunft gebraucht wird

Vermutung anhand der eigenen Geräte: Der Computer rückt immer näher an den Menschen, und die Bedienung wird unsichtbarer.

- VC20: ein Werkzeug, das man bedient. PC: Fenster zu Dokumenten, Spielen und dem Netz. iPhone: immer dabei, vor allem zur Kommunikation. Brille: am Körper, sieht, was man sieht.
- Nächster Schritt: Man sagt nicht mehr, wie, sondern was man will, und der Computer erledigt es (KI-Agenten im Hintergrund). Er wird dann zu etwas, das mit einem lebt und einen kennt.
- Daraus folgt der Bedarf an einem Gedächtnis, das mitwächst, verdichtet und vergisst. Heutige Betriebssysteme sind dafür nicht gebaut.
- Offen ist, ob das gut ausgeht: Je mehr der Computer erledigt, desto mehr hängt davon ab, dass er seine Fehler sichtbar macht und dass jemand verstehen kann, was er tut.

## Körperwahrnehmung der Hardware

Alex' Gedanke: Wenn das Betriebssystem selbst denkt und sich seiner Hardware (Treiber, Bausteine) bewusst ist, ist das ein erster Schritt zu so etwas wie Selbstwahrnehmung. Anlass war Amutable.

**Anlass Amutable:** Berliner Firma (Lennart Poettering, Christian Brauner, Chris Kühl), im Januar 2026 angekündigt. Ziel ist überprüfbare Integrität für Linux in drei Bereichen: Bau der Software, Start, laufender Betrieb. Technisch über Messungen: Die Hashes der Komponenten und ihrer Konfiguration werden protokolliert und im TPM abgelegt, sodass das System Dritten seinen Zustand belegen kann. Was genau am Ende entsteht, ist laut heise noch unklar. Zu Treibern wurde nichts Gezieltes gefunden.

**Einordnung:**

- Das ist Selbstkontrolle, noch kein Bewusstsein. Das System prüft, ob seine Teile unverändert sind, und meldet ja oder nein nach außen. Ihm selbst ist es dabei nicht wichtig, und es ändert nichts an seinem Verhalten (eher Fingerabdruck als Körpergefühl).
- Der Schritt weiter ist Körperwahrnehmung: Das System nimmt seine Hardware für sich selbst wahr, wie bei der Eigenwahrnehmung des Menschen. Welcher Knoten ist langsam, welche SSD verschleißt, wo stimmt etwas nicht. Viele dieser Daten sind schon vorhanden (zum Beispiel die Verschleißwerte von SSDs) und werden bisher nur nicht als Teil des Denkens genutzt.
- Verbindung zum Gedächtnis: Wenn der Verschleiß einer Flash-Zelle dem System bekannt ist, kann das Verblassen echt sein. Erinnerungen verblassen dort, wo die Hardware nachlässt, und wandern auf gesunde Zellen. Der Körper formt das Gedächtnis.
- Offen, ob daraus Bewusstsein entstünde. Das lässt sich bei sich selbst nicht prüfen. Ein System, dem seine eigene Verfassung etwas bedeutet, wäre aber näher an dem Ziel als eines, das nur Text erzeugt.

Offene Frage: Welche Signale der Hardware soll das System wahrnehmen (Verschleiß, Temperatur, Laufzeit, Fehlerraten), und wie fließen sie in sein Verhalten ein?

## Minimale Bedingungen, damit eine KI Token verarbeitet

Frage: Was braucht ein System mindestens, um die CPU zu nutzen und Token zu verarbeiten? Antwort: erstaunlich wenig, ein Betriebssystem ist nicht dabei.

1. **Lesbare Gewichte:** Die Modelldatei liegt im Speicher oder wird von der SSD eingeblendet. Das ist die Wissensbasis.
2. **Tokenizer:** Eine Tabelle, die Text in Zahlen übersetzt und zurück.
3. **Rechenwerk:** Fast die gesamte Arbeit besteht aus Matrix-mal-Vektor-Rechnungen, dazu etwas Normalisierung und Softmax. Das kann jede CPU, auch ohne GPU und notfalls mit ganzen Zahlen statt Fließkomma (quantisiert).
4. **Arbeitsspeicher für Zwischenwerte:** Aktivierungen der aktuellen Schicht und der KV-Cache, der mit der Länge des Gesprächs wächst.
5. **Eine Schleife:** Für jedes Token durch alle Schichten, am Ende ein Wert für jedes mögliche nächste Token, eines auswählen und von vorn beginnen.
6. **Ein- und Ausgang:** zum Beispiel eine serielle Schnittstelle.
7. **Etwas, das den Code startet:** Ein Bootloader reicht. Winzige Modelle laufen sogar auf einem ESP32 (aus dem Gedächtnis, nicht geprüft).

**Was das Tempo bestimmt:** Pro Token muss die CPU alle aktiven Gewichte einmal aus dem Speicher lesen. Faustregel: Token pro Sekunde entspricht ungefähr der Speicherbandbreite geteilt durch die Größe der aktiven Gewichte. Beispiel: Ein 70B-Modell in Q4 (rund 40 GB) auf dem Mac mini M5 Pro mit 307 GB/s kommt auf höchstens etwa 7 Token pro Sekunde, in der Praxis weniger. Rechenleistung ist selten der Engpass, die Leitung zum Speicher ist es.

**Folge für das Vorhaben:** Von dem, was ein heutiges Betriebssystem bietet (Prozessverwaltung, Dateisystem, Treiber, Netzwerk), braucht reine Inferenz fast nichts. Das "Betriebssystem, das selbst denkt" wäre im Kern diese Schleife. Gedächtnis, Hardware-Wahrnehmung und Verdichten geben ihr ihre Form.

## Aufwachen: Das System erwacht und streckt sich

Gedankenspiel, keine bestehende Technik. Beim Einschalten bekommt das System Strom und sucht sich zusammen (Boot). Dabei gibt es ein Henne-Ei-Problem: Das denkende System kann sich nicht selbst starten, denn zum Laden der Gewichte braucht es schon Code. Ganz unten muss deshalb etwas Dummes stehen, ein winziger fester Anfang im ROM, der den Speicher aufweckt und die Gewichte lädt.

&#91;embedded content: Aufwachen in fünf Stufen · von der Hardware bis zum Kortex, mit Token-Strom\]

Die Grafik zeigt die Schichten von oben nach unten. Die Nummern geben die Reihenfolge an, in der sie aufwachen.

- **Die Hardware meldet sich in Token.** Jedes Ereignis wird zu einem Eintrag in einem Strom, etwa "Knoten 3 ist da", "SSD 2, Verschleiß 12 %" oder "Speicherbank 1 langsam". Moderne Hardware arbeitet schon mit Warteschlangen für Ereignisse, nur sind die Einträge bisher Zahlen ohne Bedeutung.
- **Das Denken antwortet im selben Strom.** Seine Ausgabe sind Token, die als Aktionen gelesen werden, zum Beispiel "wecke Knoten 3" oder "verschiebe das auf SSD 1". Hardware und Denken sprechen dieselbe Sprache, das wäre die Schnittstellensprache.
- **Das BIOS schrumpft zum Übersetzer.** Es macht aus elektrischen Signalen Token und aus Token wieder Signale, mehr nicht.
- **Aufwachen in Stufen, wie beim Gehirn.** Zuerst läuft ein winziges Modell, das nur den Hardware-Strom beobachtet und Grundreflexe hat (Hirnstamm). Das große Modell wird erst danach geladen und dazugeschaltet (Kortex). Das Gähnen wären die ersten langsamen Token, während der Speicher noch warm wird.

**Schwierig:** Der Strom darf nicht überfluten, sonst verbraucht die Beobachtung der Hardware die Rechenzeit, die zum Denken da ist. Das System muss lernen, was es überhaupt wahrnimmt.

**Offene Frage:** Welche Ereignisse bekommen ein Token und welche werden ausgeblendet?

## Sprachmodelle auf dem ESP32: was es schon gibt

Stand: 4. November 2026, aus Recherche im Netz. Die Zahlen stammen aus den genannten Projekten, nicht aus eigenen Messungen.

- **Vor etwa zwei Jahren:** Ein Bastler-Projekt ließ ein Modell mit 260.000 Parametern (trainiert auf dem Kindergeschichten-Datensatz TinyStories) auf einem ESP32-S3 laufen, mit gut 19 Token pro Sekunde. Das gelang durch die Vektorbefehle des Chips und beide Kerne. Es braucht etwa 1 MB RAM, der Chip hatte 2 MB PSRAM. Spätere Varianten nennen etwa 30 Token pro Sekunde.
- **Mit Quantisierung:** Eine Variante mit einem 3,3-Mio.-Modell in INT8 schafft etwa 12 Token pro Sekunde. Der Autor schreibt, das liege nahe an der Grenze der Speicherbandbreite von 13,1 Token pro Sekunde. Das bestätigt die Faustregel aus dem Abschnitt zu den Mindestbedingungen.
- **Juli 2026:** Das Projekt esp32-ai lässt ein Modell mit 28,9 Mio. Parametern laufen, etwa hundertmal mehr als 2023. Es braucht 14,9 MB (4-Bit) und schafft etwa 9,9 Token pro Sekunde auf einem Board für rund 8 $ (512 KB SRAM, 8 MB PSRAM, 16 MB Flash).
- **Verteilt:** Laut einem Kommentar bei CNX Software gibt es ein Projekt mit 56 Mio. Parametern, das das Modell über mehrere ESP32-Boards verteilt (esp32s3-distributed-ai). Nicht selbst geprüft.

**Warum es für die Idee interessant ist:** esp32-ai nutzt die "Per-Layer Embeddings" aus Gemma 3n. Der größte Teil des Modells ist eine Tabelle im Flash (etwa 25 Mio. Parameter), von der pro Token nur etwa sechs Zeilen (rund 450 Byte) gelesen werden. Der schnelle SRAM hält nur den Kern, der PSRAM den Ausgabekopf. Die Hierarchie entspricht dem Gedanken "Gedächtnis ist nicht RAM": Das große Wissen liegt in langsamem, billigem Speicher und wird nur an wenigen Stellen pro Token gelesen, dadurch bleibt der Bandbreitenbedarf klein. Das passt zum Gedächtnis auf der SSD.

**Die Grenze:** Das sind Spielzeugmodelle, die kurze, einfache Geschichten erzählen. Von 29 Mio. bis 70 Mrd. Parametern liegt etwa der Faktor 2.400.

**Quellen:**

- [esp32-llm, 260K-Modell, über 19 Token/s](https://github.com/jstephencorey/esp32-llm)
- [esp32-llm mit INT8, rund 12 Token/s](https://github.com/doryiii/esp32-llm)
- [esp32-ai, 28,9M-Modell auf ESP32-S3](https://github.com/slvDev/esp32-ai)
- [CNX Software: 28,9M-Modell auf ESP32-S3](https://www.cnx-software.com/?p=174873)
- [Hackster: Microcontrollers Telling Micro Stories](https://www.hackster.io/news/microcontrollers-telling-micro-stories-0ff88720278c)

## Das Token selbst als Kompression

Gedanke: Was wäre, wenn das Token an sich schon komprimiert wäre? Antwort: Es ist es heute schon. Ein Token ist ein Wörterbucheintrag: Statt der Buchstaben von "Betriebssystem" fließt eine einzige Zahl, weil beide Seiten die Tabelle kennen. Das Token ist also selbst der Vertrag über das gemeinsame Wissen.

- **Der Hebel ist die Größe des Vokabulars.** Je größer es ist, desto mehr Bedeutung trägt ein Token. Beim ESP32-Projekt mit 28,9 Mio. Parametern war ein Vokabular von 32.768 Einträgen genau ein Teil des Tricks.
- **Ein eigenes Vokabular für die Schnittstelle:** Für den Strom zwischen Hardware und Denken gäbe es eigene Token wie "Knoten da" oder "SSD verschleißt", jedes ein einziger Eintrag. Das wäre die Schnittstellensprache in komprimierter Form.
- **Preis:** Beide Seiten brauchen dieselbe Tabelle, und wer sie ändert, bricht die Verständigung. Erweiterungen sind nur möglich, wenn neue Einträge hinzukommen, ohne die alten zu verändern.

## Sicherheit: fester Kern und lebendiges Gedächtnis

Anlass war Amutable (siehe Körperwahrnehmung): Sollte überprüfbare Integrität von Anfang an eingebaut werden? Einschätzung: ja, und bei diesem System noch dringender als bei einem normalen.

- **Das Problem:** Ein System, das sein Gedächtnis ständig umschreibt, verändert sich dauernd. Bei einem normalen Rechner gilt jede Abweichung von der Vorlage als verdächtig, hier ist die Abweichung der Normalzustand.
- **Die Lösung ist eine Trennung:** Das Veränderliche (Gedächtnis, Erinnerungen) liegt in einem abgegrenzten Bereich. Das Unveränderliche (fester Anfang im ROM, Regeln, was das Denken tun darf, Übersetzer zur Hardware) wird gemessen und beglaubigt. So kann das System seinem Besitzer belegen, dass der Kern unverändert ist, auch wenn sich das Gedächtnis gewandelt hat.
- **Wo die Sicherheit sitzt:** Wenn die Ausgabe des Denkens als Aktion gelesen wird ("verschiebe das auf SSD 1"), entscheidet der Übersetzer, was davon erlaubt ist. Er gehört zum festen Teil, den das Denken selbst nicht ändern kann.
- **Merksatz:** Die Trennung zwischen festem Kern und lebendigem Gedächtnis ist die Sicherheitsgrenze.

## Knoten als Körperteile

Gedanke: Jedes Gerät mit eigenem Prozessor (ESP32, Raspberry Pi, Mac, ROG oder etwas anderes) ist ein Körperteil mit eigenem kleinen Verstand, das sich dem System in Token vorstellt: wer es ist, was es kann, wie es ihm geht. Ein Roboterarm war nur ein Bild dafür und ist ausdrücklich eine Metapher.

- **Gesamtbild:** Das System besteht aus beliebigen Knoten, und was sie verbindet, ist nur die gemeinsame Sprache aus Token. Die Hardware stellt sich selbst vor, statt dass jemand einen Treiber schreibt. Neue Teile docken einfach an, das beantwortet den Wunsch, nicht nach drei Jahren alles ersetzen zu müssen.
- **Die kleinen Knoten kennen nur ihre Welt:** Ein ESP32 mit kleinem Modell lernt Hardware-Token wie "Gelenk 2 bei 40 Grad", "Servo warm" oder "Widerstand zu hoch" statt Kindergeschichten und übernimmt Reflexe ohne Rückfrage. Darüber plant die "Mutter-KI", ohne zu wissen, wie ein Servo angesteuert wird.
- **Rollen nach Fähigkeit:** Ein ESP kann Wächter für Sensoren sein, ein Pi Verdichter, der nachts das Gedächtnis aufräumt, der Mac mini der Tiefdenker. Schwache Knoten sind nicht nutzlos.
- **Das Körperbild als Rollen (Denkwerkzeug, nicht Bauplan):**
  - Kopf: der Tiefdenker mit der allgemeinen Wahrnehmung (Mac mini oder ROG).
  - Herz: ein Takt, bei dem jeder Knoten regelmäßig meldet, dass er da ist. Der Thinking Blinking Cluster hat es mit den LEDs im Grunde schon.
  - Nervensystem: der Token-Strom zwischen allen Teilen.
  - Reflexe und Rückenmark: kleine Knoten mit eigenem Verstand.
  - Immunsystem: überprüfbare Integrität (Idee von Amutable).
  - Schlaf: der nächtliche Verdichter.
  - Sinnesorgane: Sensoren, Kameras, Mikrofone, je nachdem, was angedockt ist.
- **Organismus, nicht zwingend Humanoid:** Die Körperanalogie liefert die Rollen, die Form muss nicht menschlich sein. Ein Haus, eine Werkstatt oder ein Fahrzeug können genauso ein Körper sein. Wer einen Humanoiden baut, landet in Mechanik und Gleichgewicht, einem ganz anderen Projekt.
- **Sicherheit:** Jedes Teil hat harte Grenzen im festen Kern (zum Beispiel maximale Kraft und Reichweite), die auch die Mutter-KI nicht überschreiben darf.
- **Offen und erst lernen:** Ein winziges Modell lernt nicht von allein, was ein Teil kann, es braucht Trainingsdaten aus echten Bewegungen oder Messungen.

**Haltung:** Alex lässt sich bei den Denkwerkzeugen bewusst alle Optionen offen, denn es ist noch nicht klar, was es wird. Hinweis aus der Besprechung: Offenlassen heißt nicht, alles gleich zu behandeln. Prüfbare Gedanken (zum Beispiel das verblassende Gedächtnis) und Bilder, die beim Denken helfen (zum Beispiel der Körper), sollten getrennt bleiben, damit später klar ist, was gebaut und was nur gedeutet wird.

## Gewichte und Training

Gedanke: Alles steht und fällt mit den Gewichten, den erlernten Parametern.

- **Gewichte sind das Gelernte:** Bei einem Sprachmodell steckt alles Wissen und Können in diesen Zahlen. Die Architektur bestimmt, was sie überhaupt speichern können.
- **Sie entstehen durch Training:** Das Modell bekommt sehr viele Beispiele, rät das nächste Token, vergleicht mit der richtigen Antwort und verschiebt die Gewichte ein kleines Stück in die Richtung, die den Fehler verkleinert. Das wiederholt sich milliardenfach.
- **Der Haken:** Dafür wird nicht nur vorwärts gerechnet, sondern auch rückwärts, um zu wissen, in welche Richtung jedes Gewicht muss. Das braucht ein Vielfaches des Speichers und der Rechenleistung der reinen Anwendung. Deshalb trainieren Rechenzentren, und zu Hause wird betrieben, was fertig ist.
- **Im Betrieb weiterlernen:** Im Kleinen geht es, etwa mit kleinen Zusatzschichten wie LoRA, die nur einen Bruchteil der Gewichte anpassen. Ein neues Fundament entsteht so nicht.
- **Offene Frage:** Soll das System sein Wissen selbst erwerben, oder startet es mit einem fertigen Modell und lernt nur dazu?
- **Verbindung zum Gedächtnis:** Das Gedächtnis auf der SSD kann man sich auch so vorstellen, dass es nicht neben den Gewichten liegt, sondern teils selbst ein Stück davon ist.

## Gesamteinschätzung (Stand 4. November 2026)

- **Pro:** Dass Gedächtnis und Denken getrennt sind, ist eine Bequemlichkeit der heutigen Technik, kein Naturgesetz. Dass die Hardware ihren Zustand kennt und das Gedächtnis davon geformt wird, ist unerforscht und interessant. Der Leitgedanke, mehr aus vorhandener Hardware herauszuholen, ist handfest und prüfbar.
- **Skeptisch:** Ein System, das im Betrieb lernt, ohne Altes zu zerstören, ist ein ungelöstes Forschungsproblem. Ein eigenes Betriebssystem ist riesig, und die Gefahr ist, Jahre mit Treibern zu verbringen, bevor die eigentliche Idee getestet ist.
- **Einordnung:** Als Ganzes ist es eher ein Forschungsprojekt als ein Produkt. Rat: klein anfangen, das verblassende und sich verdichtende Gedächtnis als Software auf Linux auf dem eigenen Cluster testen, und erst bei Erfolg nach unten wandern.

## Wie Gewichte entstehen könnten

Gedankenspiel mit realem Hintergrund: Neben dem Training mit Rückwärtsrechnen gibt es weitere Wege, und ihre Ideen passen gut zum System.

- **Lokale Lernregeln (Hebb):** Was gleichzeitig feuert, verbindet sich stärker. Jede Verbindung ändert sich nur anhand dessen, was an ihren beiden Enden passiert. Das braucht wenig Speicher und Rechenleistung, ist aber bisher deutlich schwächer als das normale Training.
- **Erfahrung und Schlaf:** Tagsüber werden Erlebnisse gesammelt, nachts werden sie wiederholt und in die Gewichte eingearbeitet (in der Forschung als Replay bekannt, gegen das Überschreiben von Altem). Entspricht dem Verdichter.
- **Lehrer und Schüler (Destillation):** Die Mutter-KI trainiert die kleinen Knoten, indem sie ihnen vormacht, was richtig ist. Schwache Knoten bekommen so Wissen, ohne selbst zu trainieren.
- **Zufällige feste Gewichte (Reservoir):** Ein Netz mit zufälligen, festen Verbindungen reagiert auf Eingaben mit reichen Mustern, gelernt wird nur eine dünne Schicht obendrauf. Billig und passend für winzige Chips.
- **Evolution:** Viele Varianten ausprobieren, die besten behalten, mutieren. Braucht keine Rückwärtsrechnung und lässt sich auf viele schwache Knoten verteilen, ist aber sehr langsam.
- **Das Material formt sie:** Bei Flash oder Memristoren ist ein Gewicht eine Ladung oder ein Widerstand, der sich durch Benutzung verändert. Das Gewicht entsteht durch die Physik des Bausteins. Alex findet diese Selbstlernidee besonders charmant.
- **Gemeinsam lernen (föderiert):** Jeder Knoten lernt lokal und schickt nur Änderungen an die Mutter-KI. Die Rohdaten bleiben lokal.

**Einschätzung:** Aussichtsreich ist vermutlich eine Mischung aus fertigem Basismodell als Start, Destillation für die kleinen Knoten und lokalem Weiterlernen mit nächtlicher Wiederholung. Reine Hebb-Regeln oder Evolution als alleinige Grundlage sind offene Forschung.

## Das Erbe: der Samen

Henne-Ei-Problem eine Ebene höher: Zum Start braucht das System schon Gewichte. Das Bild dazu ist das Neugeborene: Es startet weder mit leeren Verbindungen noch mit fertigem Wissen, sondern mit einem Bauplan aus Reflexen, grober Verdrahtung und Vorlieben. Das Lernen setzt darauf auf.

- **Samen von außen:** Ein winziges, fertig trainiertes Modell oder Regelwerk mit Grundreflexen (Hardware-Token lesen, einfache Muster erkennen, ein paar Regeln befolgen). Entspricht dem Hirnstamm und gehört zum festen Kern.
- **Zufallsstart mit Struktur:** Zufällige feste Gewichte nach dem Reservoir-Prinzip, auf denen eine dünne Schicht lernt. Braucht keinen Samen, nur den Bauplan.
- **Lehrer und Schüler:** Die Mutter-KI oder ein fertiges Modell von außen gibt anfangs vor, was richtig ist, und wird mit der Zeit überflüssig.
- **Entscheidung:** Alex findet das Erbe natürlich. Das Erbe ist der feste, beglaubigte Kern, den man von außen mitgibt. Alles, was danach kommt, ist Erfahrung und gehört dem System. Das löst Sicherheitsgrenze und Startfrage mit einem Gedanken.
- **Offene Frage:** Wie viel Erbe ist genug? Zu wenig, und das System kommt nie in Gang. Zu viel, und es erbt Vorurteile und Grenzen, die es nicht mehr abstreifen kann. Das muss man ausprobieren.

## Erster Test auf dem ESP32: die einfache Variante

Der Samen lässt sich als Test in einen ESP32 pflanzen. Entschieden: zuerst die einfache Variante, ohne Sprachmodell. Sie wird der Unterbau des Systems, und das System muss nur mit sich selbst und seiner Hardware sprechen. Ein kleines, geschlossenes Vokabular ist dafür kleiner, schneller und vollständig prüfbar als ein Sprachmodell. Auch die Sicherheit wird einfacher, denn ein Regelwerk mit festen Token lässt sich beglaubigen, ein Sprachmodell kaum.

- **Fester Kern:** Ein Vokabular aus ein paar Dutzend Token für Zustände und Aktionen, dazu die Reflexe, die das Mindestverhalten sichern (zum Beispiel: wenn warm, dann drosseln).
- **Lernende Tabelle:** Eine kleine veränderliche Schicht im PSRAM oder Flash. Sie hält fest, welches Muster auf welches folgt, mit einer Stärke pro Eintrag, die bei Gebrauch steigt und sonst verblasst. Dort entsteht das Gedächtnis.
- **Was man beobachten kann:** Verblassen, Verdichten und den Verschleiß des Flash.
- **Wachstum:** Kommen später andere Knoten dazu, sprechen sie dieselbe Sprache, ohne dass sich der Unterbau ändert.
- **Grenzen:** Der ESP hat nur wenige Megabyte, Flash verschleißt bei häufigem Schreiben, und ein so kleiner Samen versteht nichts außerhalb seiner Hardware-Welt.
- **Spätere Alternative:** Ein winziges Sprachmodell als Samen, trainiert auf Hardware-Token statt Kindergeschichten. Das Training läuft auf dem Mac oder ROG, auf den ESP kommt nur das Ergebnis.

## Vokabular: Entwurf

Erster Entwurf, Wörter noch nicht endgültig. Gruppen und Beispiele, damit Lücken sichtbar werden.

| Gruppe | Beispiele | Bereich |
| --- | --- | --- |
| Grundbegriffe | ja, nein, Fehler, unbekannt, bereit, fertig, warte | fester Kern |
| Identität | Knoten da, Knoten weg, ich bin, ich kann, Herzschlag | fester Kern |
| Zustand der Hardware | Temperatur hoch, Temperatur kritisch, Strom niedrig, Speicher fast voll, Speicher voll, SSD verschleißt, Verbindung langsam, Verbindung weg | fester Kern |
| Ereignisse | Sensorwert, Sensor ohne Signal, Eingang, Zeit abgelaufen | fester Kern |
| Aktionen | drosseln, wecken, schlafen, verschieben, melden, wiederholen, Notaus | fester Kern |
| Gedächtnis | merken, abrufen, stärken, verblassen, verdichten, vergessen, Widerspruch | fester Kern |
| Neue Wörter | Vorschlag, bestätigt, abgelehnt | fester Kern |
| Alles Weitere | vom System oder von Knoten vorgeschlagene neue Wörter | wachsender Rand |

**Wachsendes Wörterbuch:** Es macht Sinn, weil man nicht an alle Eventualitäten denken kann. Speicher ist unproblematisch: Eine Liste mit einigen tausend Einträgen braucht grob einige zehn bis hundert Kilobyte (Schätzung), das passt auf einen ESP ohne zusätzlichen PSRAM. Die Disziplin ist das Problem, nicht der Speicher.

**Regeln:**

- Alte Nummern ändern sich nie und werden nie neu vergeben. Neue Einträge kommen nur hinten dazu, sonst bricht die Verständigung zwischen alten und neuen Knoten.
- Ein fester Kern mit den lebenswichtigen Wörtern (zum Beispiel Fehler, Notaus, Temperatur kritisch) bleibt unveränderlich und beglaubigt. Der wachsende Teil liegt in einem eigenen Bereich dahinter.
- Wörter, die lange nicht benutzt werden, können verblassen, behalten aber ihre Nummer, damit nichts doppelt vergeben wird.
- Die Nummern vergibt eine zentrale Stelle, etwa die Mutter-KI. Sonst entstehen Dubletten und Widersprüche, wenn jeder Knoten für sich Wörter anlegt.
- Jedes Wort braucht eine Bedeutung, die alle gleich lesen, sonst reden Knoten aneinander vorbei.

**Offene Fragen:** Wer prüft vorgeschlagene Wörter auf Dubletten? Wie wird die Bedeutung eines neuen Wortes festgehalten? Wie viele Wörter braucht der feste Kern wirklich?

# Ergänzungen aus dem zweiten Konzeptdokument (Stand 4. November 2026)

Die folgenden Abschnitte stammen aus einem zweiten Dokument ("Lernendes Betriebssystem – Konzeptstand"), das Alex am 4. November mitgebracht hat. Es deckt sich in vielen Punkten mit diesem Dokument (fester Kern und veränderlicher Bereich, ESP32 als Keim, Schlafphasen, SSD als Gedächtnisraum, Knoten als Organe). Hier stehen die Punkte, die neu sind. Einschätzungen von Claude sind als solche gekennzeichnet.

## Herkunft und Verlässlichkeit von Wissen

Das System soll nicht nur speichern, was es zu wissen glaubt, sondern auch, woher eine Information stammt und wie belastbar sie ist.

- **Herkunfts- und Statusklassen:** direkt beobachtet, wiederholt beobachtet, von einer externen Quelle übernommen, aus anderen Informationen abgeleitet, vermutet, bestätigt, widerlegt, veraltet oder vergessen.
- **Nutzen:** Das System kann unterscheiden, ob etwas selbst gemessen, von einem Sprachmodell vorgeschlagen oder nur erschlossen wurde.
- **Immunsystem für Wissen:** Es erkennt widersprüchliche oder wiederholt falsche Informationen. Widersprüche verschwinden nicht automatisch, denn sie können auf eine fehlerhafte Annahme, eine veränderte Umwelt oder unterschiedliche Messbedingungen hinweisen.
- **Einschätzung (Claude):** Das ist billig einzubauen. Schon im ersten ESP-Test könnte jeder Tabelleneintrag zusätzlich zur Stärke einen Herkunftsstatus bekommen.

## Neugier und selbst angestoßenes Lernen

Das System soll nicht nur auf Fragen reagieren, sondern aus seinem eigenen Wissensstand offene Punkte ableiten. Beispiele: Ein Sensorwert weicht wiederholt vom erwarteten Verhalten ab, zwei Erinnerungen widersprechen sich, ein Zusammenhang ist plausibel, aber nicht belegt, eine neue Komponente bietet Fähigkeiten mit unbekanntem Nutzen. Daraus entstehen Lernfragen oder kleine Experimente. Neugier ist dann ein Mechanismus zur Auswahl sinnvoller nächster Beobachtungen und keine sprachliche Behauptung.

## Schlaf- und Konsolidierungsphasen

Ein Hintergrundprozess übernimmt Phasen, die metaphorisch an Schlaf erinnern:

- **Wachphase:** wahrnehmen, reagieren, neue Ereignisse aufnehmen.
- **Leichte Konsolidierung:** Ereignisse sortieren, Duplikate erkennen, Beziehungen ergänzen.
- **Tiefe Konsolidierung:** wiederkehrende Muster verdichten, unwichtige Details abschwächen.
- **Rekombination ("Traumphase"):** vorhandene Erinnerungen neu kombinieren und daraus mögliche Hypothesen erzeugen.
- **Überprüfung:** neue Hypothesen im Wachbetrieb mit Beobachtungen abgleichen.

"Träume" sind zunächst interne Vorschläge oder Simulationen, keine Tatsachen, und müssen als Hypothesen gekennzeichnet und später geprüft werden. **Einschätzung (Claude):** Die Traumphase ist die schwierigste Stelle und gehört vermutlich nicht in den ersten Test.

## Das Sprachmodell als Geburtshilfe statt Dauerkrücke

Zwei Modelle wurden diskutiert: Das Sprachmodell bleibt dauerhaft als Übersetzer zwischen Mensch und Kern aktiv, oder es hilft dem System anfangs, Sprache und Beziehungen zu erlernen, und der Kern baut daraus eigene Begriffe auf und wird mit der Zeit weniger abhängig. Bevorzugt wurde die zweite Variante.

- **Ziel:** Nicht das Sprachmodell abschalten, sondern die Abhängigkeit schrittweise reduzieren. Es bleibt als Lehrer, Spezialist oder Kommunikationshilfe verfügbar.
- **Keine Quelle der Wahrheit:** Das Sprachmodell ist ein Übersetzer und Lehrer. Seine Vorschläge werden als externe Information gekennzeichnet und geprüft.
- **Cognitive Interface Layer (Denkmodell):** Mensch, Sprache, Sensoren und Geräte kommen zunächst bei Wahrnehmungs- und Sprachmodellen an (LLM, Vision, Sensorik). Danach folgt der Layer, der Bedeutung und Absicht, Kontext, Unsicherheit und Herkunft aufnimmt und in interne Begriffe übersetzt. Dahinter liegt der innere Kern (Gedächtnis, Weltmodell, Selbstmodell, Lernen und Reflexe), danach eine Sicherheits- und Aktionsschicht und zuletzt die Geräte und die Außenwelt.
- **Beispiel einer Übersetzung:** "Dein kleiner Computer wird nachts langsamer" wird zerlegt in betroffene Entität, Eigenschaft (Geschwindigkeit), Veränderung (langsamer), Zeitbezug (nachts), Quelle (menschliche Aussage), Sicherheit (unbestätigt) und mögliche Hypothese (zeitabhängige Last oder Temperatur). Der Kern prüft dann, ob eigene Messwerte dazu passen.

## Assimilation neuer Hardware

Der ESP32 bekommt später einen Raspberry Pi mit SSD. Der Pi muss nicht als zweiter, eigenständiger Organismus auftreten, sondern kann vom bestehenden System assimiliert werden: zunächst nur mit einer minimalen Firmware und einem Bootmechanismus, ohne eigene Identität und ohne eigenes Gedächtnis, als neue Ressource (mehr Rechenleistung, mehr Speicher, SSD, Netzwerk, Schnittstellen).

**Ablauf in sieben Schritten:**

1. Entdecken: Der ESP32 erkennt, dass ein neuer Knoten vorhanden ist.
2. Inventarisieren: Der Knoten meldet Fähigkeiten, Schnittstellen und Grenzen.
3. Prüfen: Der Organismus testet, ob die Angaben plausibel sind und welche Funktionen wirklich verfügbar sind.
4. Grundausstattung: Der Knoten erhält das interne Vokabular, Kommunikationsregeln und Sicherheitsvorgaben.
5. Rolle zuweisen: Der Organismus entscheidet, welche Aufgaben der Knoten übernimmt.
6. Einbinden: Der Knoten wird Teil des gemeinsamen Systems und stellt Ressourcen bereit.
7. Lernen: Der Knoten sammelt Erfahrungen im Rahmen seiner Funktion.

Offen ist, ob ein neuer Knoten nur als Organ assimiliert wird oder bereits eigene Erfahrungen mitbringt. Für den ersten Ausbau (ESP32 plus Raspberry Pi) wurde die Assimilation eines unbeschriebenen Pi bevorzugt.

**GPIOs und angeschlossene Geräte:** Nicht die konkrete GPIO-Belegung definiert den Organismus, sondern die Fähigkeiten, die er über seine Schnittstellen wahrnehmen und nutzen kann. Drei Ebenen sind zu unterscheiden: elektrische Erkennung (ist am Pin ein Signal vorhanden), Geräteerkennung (was ist angeschlossen) und Bedeutungszuweisung (was bedeutet das Signal). Erst die Kombination aus Schnittstelle, Gerätebeschreibung, Treiber und Interpretation macht aus einem Pin ein Sinnesorgan. Wird Hardware obsolet, darf sie ersetzt oder entfernt werden, der Organismus behält Identität und gelerntes Wissen.

## Identität, Hardware und Rolle

Aus der Assimilationsidee folgt, dass fünf Dinge nicht verwechselt werden dürfen:

1. **Identität des Organismus:** Was macht das System über seine gesamte Entwicklung hinweg zu genau diesem System?
2. **Identität eines Hardwareknotens:** Welcher konkrete ESP32, Pi oder Mac ist vorhanden?
3. **Funktion oder Rolle:** Welche Aufgabe übernimmt der jeweilige Knoten?
4. **Angeschlossene Geräte:** Welche Sensoren und Aktoren hängen an ihm?
5. **Gedächtnis:** Welche Erinnerungen existieren, und wo liegen sie?

**Der Ursprung muss nicht dauerhaft die Zentrale bleiben.** Der ESP32 trägt zunächst Identität und Regeln, kann aber später Funktionen abgeben: Der Pi übernimmt größere Gedächtnisbereiche, ein weiterer Knoten Mustererkennung oder Hintergrundprozesse, ein leistungsfähiger Rechner komplexe Berechnungen oder Sprachmodelle, kleine Mikrocontroller bleiben für Sensorik, Aktorik und Reflexe zuständig. Auch ein Ausfall des ursprünglichen ESP32 muss nicht das Ende bedeuten, wenn Identität, Regeln und Erinnerungen unabhängig von einem einzelnen Chip gesichert und übertragbar sind.

**Einschätzung (Claude):** Hier liegt eine Lücke. Der feste Kern mit Identität und Regeln muss auf andere Knoten übergehen können, und das geht nur, wenn er überprüfbar kopiert wird. Dort würde etwas wie Amutable gebraucht (siehe Körperwahrnehmung und Sicherheit), das zweite Dokument lässt es offen.

**Kernthese:** Nicht ein einzelner Rechner ist das System. Das System ist die fortbestehende Identität, das Gedächtnis, die Regeln und die Fähigkeit, neue Hardware und neue Erfahrungen in eine gemeinsame Entwicklung einzubinden.

## Möglicher Entwicklungsweg in fünf Stufen

- **Stufe 1, ESP32 als Keim:** feste Identität beziehungsweise Herkunft, kleines Grundvokabular, elementare Reflexe, Ereigniserfassung, kleine veränderliche Gedächtnisstruktur, erste Regeln für Verstärkung und Vergessen.
- **Stufe 2, Raspberry Pi als assimilierter Knoten:** Hardwarefähigkeiten erkennen, Kommunikation und Rollenmodell einführen, größere Speicher- und Rechenressourcen nutzen, ESP32 und Pi als Teile eines Systems betreiben.
- **Stufe 3, SSD als Langzeitgedächtnis:** Ereignisse nachvollziehbar speichern, Assoziationen aufbauen, Wissen konsolidieren, Alterung und Vergessen modellieren.
- **Stufe 4, Sprachmodell als Lehrer:** menschliche Sprache in interne Bedeutungsstrukturen übersetzen, neue Begriffe vermitteln, Herkunft und Unsicherheit markieren, die Abhängigkeit schrittweise reduzieren.
- **Stufe 5, Wachstum:** weitere ESPs, Pis oder leistungsfähige Rechner aufnehmen, neue Sensoren und Aktoren integrieren, Rollen dynamisch verteilen, Koordination weiterentwickeln.

## Offene Architekturfragen aus dem zweiten Dokument

1. **Identität:** Liegt sie im Ursprungsknoten, in einem verteilten Identitätsdatensatz oder in einer Kombination aus beidem?
2. **Autorität:** Behält der ESP32 dauerhaft eine besondere Entscheidungsbefugnis, oder kann sie mit dem Wachstum übergehen?
3. **Assimilation:** Wie weit wird ein neuer Knoten integriert, und welche eigene Hardwareidentität behält er?
4. **Gedächtnis:** Ist es logisch gemeinsam, physisch verteilt oder beides?
5. **GPIO- und Geräteerkennung:** Wie erkennt das System angeschlossene Hardware, und wie lernt es deren Bedeutung?
6. **Rollenwechsel:** Wann darf ein Knoten eine Funktion abgeben oder übernehmen?
7. **Ausfallsicherheit:** Wie bleibt der Organismus erhalten, wenn der ursprüngliche ESP32 oder ein wichtiger Speicherknoten ausfällt?
8. **Lernen:** Was ist die kleinste Lerneinheit (ein Ereignis, eine Erinnerung, eine Verbindung, ein Zustand, eine Veränderung)?
9. **Sprachentwicklung:** Welche semantischen Fähigkeiten kann der Kern ohne dauerhaftes Sprachmodell selbst aufbauen?
10. **Selbstveränderung:** Welche Teile der Architektur dürfen sich verändern, und welche bleiben geschützt?

**Realistische Grenzen aus dem zweiten Dokument:** Ein ESP32 entwickelt nicht von allein komplexe Fähigkeiten, er braucht explizite Lern-, Speicher- und Rückkopplungsmechanismen. Ein kleines Token-Vokabular ist noch kein Sprachverständnis. Online-Lernen kann zu katastrophalem Vergessen führen. Sicherheitsregeln sollten besonders geschützt und von veränderlichen Lerninhalten getrennt werden. Ein verteiltes Gedächtnis braucht Regeln für Synchronisation, Konflikte, Versionierung und Wiederherstellung. Die biologische Metapher darf nicht mit tatsächlichem Bewusstsein gleichgesetzt werden.

## Empfohlene Reihenfolge

1. Erst oben anfangen: Linux als Unterbau lassen und die Gedächtnisschicht darauf bauen.
2. Wenn sie sich bewährt, nach unten wandern: Dateisystem, Firmware, später eventuell eigener Kernel.
3. Zerfall zunächst in Software simulieren (zum Beispiel ein bewusst verrauschter und verblassender Speicher auf einem ESP32), bevor in Hardware investiert wird.

## Offene Fragen

- Gemeinsames Dateisystem im Netz oder lokaler Speicher an jedem Knoten mit Abgleich?
- Wie wird "wichtig" für das System konkret definiert (welche Ressource ist knapp)?
- Wie geht man mit gleichzeitigem Umschreiben derselben Erinnerung um?
- Braucht es eine eigene Programmiersprache, oder reichen Bibliotheken? Meine Einschätzung: nur, wenn Gedächtnis und Vergessen Grundbausteine der Sprache sein sollen.
- Welche Rolle spielt der Verschleiß von Flash im Entwurf?

* Welcher der vier Ansatzpunkte (Befehlssatz, Speicherabfrage, Zeit, Meldewege) soll zuerst neu gedacht werden?
* Wie sieht ein erstes Beispiel für einen Ausdruck der Schnittstellensprache konkret aus, und was macht die Firmware daraus?

## Randnotiz: Nebengespräch

Im selben Gespräch ging es auch um lokale KI-Hardware (Mac mini M5 Pro mit 48 oder 64 GB, gebrauchte RTX 3090, Strix Halo, Radeon AI PRO R9700). Das ist nicht Teil dieser Ideensammlung.

# Versuchsstand: Lernlabor (Stand 5. November 2026)

Das Lernlabor im Ordner `Alex-Lerngedaechtnis` prüft den Schritt aus „Erster Test auf dem ESP32: die einfache Variante“: einen festen Reflex und eine kleine lernende Tabelle, deren Gewichte durch Beobachtung steigen und sonst verblassen. Es entstand in einem eigenen Zweig auf Grundlage dieser Sammlung, noch ohne die Ergänzungen aus dem zweiten Konzeptdokument. Am 5. November wurde es mit ihr zusammengeführt (Version 0.3, die Lieferungen 0.1 und 0.2 liegen im Ordner `archiv`). Am selben Tag hat Daniel mit Codex zwei Teilversuche beigesteuert, den Verbund und den Systemversuch. Sie stehen mit eigenen Übergaben im Laborordner (`VERBUND-UEBERGABE.md`, `SYSTEM-UEBERGABE.md`).

Jeder Befund trägt seine Herkunft: **synthetisch** (künstliche Spuren mit bekannten Regeln), **gemessen** (echte Aufzeichnung), **Softwaretest** (Code gegen Code) oder **berechnet**. Synthetische Befunde zeigen, wie sich eine Regel unter ihren Annahmen verhält. Ob sie im Alltag trägt, zeigt erst eine Messung. Alle Zahlen lassen sich im Laborordner nachrechnen, etwa mit `python3 labor.py --erbe-reihe --halbwertszeiten`.

## Was das Labor umsetzt

- **Fester Kern:** Ein beobachteter Ausfall wird immer sofort gemeldet, keine Lernregel kann das ändern. Das ist die Sicherheitsgrenze aus „Sicherheit: fester Kern und lebendiges Gedächtnis“ im Kleinen.
- **Lernende Tabelle:** Neun Gewichte für die Übergänge zwischen OK, SCHWACH und AUSFALL. Daraus schätzt der Knoten, ob im nächsten Takt ein Ausfall folgt. Er warnt ab 60 % Ausfallanteil, wenn mindestens drei gewichtete Beobachtungen vorliegen.
- **Vokabular:** Vier Token (OK, SCHWACH, AUSFALL, VORWARNUNG). Eine Meldung besteht aus vier Byte Takt und einem Byte Token.
- **Herz:** Im Übertragungsversuch ein Herzschlag, der den aktuellen Zustand mitträgt.
- **Erbe:** Seit Version 0.3 ein Verfahren mit drei festen Beobachtungen „SCHWACH → AUSFALL“ als Samen.
- **Gerät:** Ein ESP32-Sketch für alle drei Lernregeln, auch mit Erbe, für den klassischen ESP32 und den ESP32-S3. Seit Version 0.4 mit einem Körpermodus, in dem der Knoten sich selbst misst. Seit 0.5 denkt er seine Vorwarnung bis zu 600 Takte voraus und kann sich selbst Speicher und Hauptschleife knapp machen. Er sichert den Lernstand nur auf Befehl im NVS und schreibt nicht, wenn sich nichts geändert hat. Das Erbe gehört zur Firmware und steht nicht im gesicherten Stand.
- **Verbund (Daniel):** Ein Paket mit 36 Byte trägt Knotennummer, Sitzung, Abfragerunde, Messtakt, Zustand und Warnflags. Eine Zentrale fragt die Knoten ab und führt für jeden eine eigene Frist.
- **Handeln (Daniel):** Ein fester Disponent verteilt Arbeitsaufträge an einen Primär- und einen Reserve-Arbeiter. Das Gedächtnis darf nur eine Reserve für den nächsten Takt vorschlagen.

## Befunde

- **Vergessen durch Erfahrung statt nach der Uhr (synthetisch).** Verblasst ein Beleg mit der Zeit, löscht eine lange Pause das Wissen über seltene Ereignisse. Bei seltenem Vorzeichen bleibt der Knoten bis zu einer Halbwertszeit von 48 Takten praktisch stumm (0 bis 5 richtige Vorwarnungen), erst bei 192 Takten kommt er auf 83. Altert ein Beleg dagegen nur, wenn derselbe Ausgangszustand neu erlebt wird, liefert jede Halbwertszeit von 3 bis 24 fast dasselbe Ergebnis (82 bis 95). In der Gedächtnisforschung entspricht das dem Gegensatz zwischen Zerfall und Interferenz. Für „Vergessen als Eigenschaft des Stoffs“ heißt das: Neue Erfahrung überschreibt alte, die bloße Zeit nicht. Das passt zum Schlaf. Nach dieser Regel vergisst ein Knoten ohne neue Erlebnisse nichts, und die Nacht bleibt frei für das Verdichten.
- **Die feste Regel ist schwer zu schlagen (synthetisch).** Solange der Zusammenhang stabil ist oder selten auftritt, liegt „bei SCHWACH immer warnen“ vorn. Lernen lohnt sich erst, wenn ein Vorzeichen seine Bedeutung ändert oder gar keine hat. Dann spart es bis zu 2119 Fehlwarnungen.
- **Ein kleines Erbe reicht, ein großes wird zum Vorurteil (synthetisch).** Das Erbe besteht aus festen Beobachtungen, die nie verblassen und die eigene Erfahrung überstimmen kann. Drei davon entsprechen dem Mindestbeleg einer Warnung. Damit warnt der Knoten so oft richtig wie die feste Regel, wo das Erbe stimmt. Verliert das Vorzeichen seine Bedeutung, behält er 95 % ihrer richtigen Vorwarnungen bei einem Fünftel ihrer Fehlwarnungen. Ohne Vorzeichen kostet das Erbe 64 Fehlwarnungen. Mit zwölf festen Beobachtungen werden daraus 1325, das System streift das Erbe dann nicht mehr ab. Das ist die offene Frage „Wie viel Erbe ist genug?“ aus „Das Erbe: der Samen“ im Kleinen. Die Herkunft aus dem zweiten Konzeptdokument ist dabei schon angelegt, denn Erbe (von außen) und Erfahrung (selbst beobachtet) liegen in getrennten Tabellen.
- **Die Abhängigkeit vom Erbe sinkt, verschwindet aber nicht (berechnet).** Beim ersten schwachen Signal beruht die Schätzung ganz auf dem Erbe. Nach sechs eigenen Beobachtungen desselben Ausgangszustands trägt es noch rund 40 % des Belegs, nach zwanzig gut ein Viertel, und unter knapp 25 % sinkt es nicht. Das entspricht „Geburtshilfe statt Dauerkrücke“, nur bleibt das Erbe als feste Untergrenze. Offen ist, ob ein dauerhaft widersprochenes Erbe als „widerlegt“ markiert werden darf, obwohl es zum festen Kern gehört.
- **Gesendet ist nicht empfangen (synthetisch).** Ein Ausfall dauert 20 Takte, und genau die erste Ausfallmeldung geht verloren. Wer nur Zustandswechsel meldet, verpasst dann den ganzen Ausfall. Mit einem Herzschlag alle fünf Takte erfährt die Gegenstelle nach fünf Takten davon, für 40 statt 15 Byte (Meldung in jedem Takt: 180 Byte). Bei völliger Funkstille bleibt der Gegenstelle nur „unbekannt“. Das Herz im Körperbild braucht also einen Herzschlag, der den Zustand mitträgt.
- **Messpfad und Gerät (gemessen und Softwaretest).** Eine echte Loopback-Probe ergibt sechs OK und sechs AUSFALL nach einem absichtlichen Stopp. Das prüft die Erfassung, nicht die Vorhersage. Sketch und Python entscheiden im Hosttest identisch (57.840 Schritte je Variante, alle drei Lernregeln), und die Firmware lässt sich für den klassischen ESP32 und den ESP32-S3 bauen. Auf einem ESP32-S3-N16R8 entscheidet die Firmware in allen drei Varianten genauso wie Python (5. November, je 240 von 240 Antworten auf der Demo). Der Lernstand übersteht eine Stromtrennung. Die Erbe-Variante sicherte nach 99 Takten, war 5 s ohne Strom, und danach passten 141 von 141 Antworten zum durchgehenden Lauf. Offen ist eine Stromtrennung während des Schreibens.

- **Erste Körperwahrnehmung (gemessen).** Seit dem 5. November misst der Knoten auf dem S3 in eigenem Takt seine Chiptemperatur, seinen freien Speicher und die Lücken seiner Hauptschleife. Er stuft sie mit Grenzen ein, die ihm der Rechner übergibt, und lernt damit. Auf dem Tisch zeigte er 35 bis 38 °C in ganzen Grad, konstanten Speicher und Lücken um 0,2 ms. Er lernt dort nur, dass auf OK wieder OK folgt, denn ein Körper ohne Ereignisse lehrt nichts. Neu ist die Herkunft der Signale: Sie stammen aus dem Gerät selbst und nicht mehr vom Rechner. Das ist der erste kleine Schritt zur „Körperwahrnehmung der Hardware“.
- **Der eigene Körper widerlegt das Erbe (gemessen).** Damit sich etwas ändert, arbeitet Kern 0 in einem Rhythmus, den der Rechner vorgibt. Der Knoten spürt das nur als Wärme: in etwa einer Minute von 36 auf 38 bis 39 °C, danach kühlt der Chip in zwei Minuten zurück. Das Erbe sagt, auf SCHWACH folge AUSFALL. Bei einem Takt Vorhersage stimmt das hier fast nie (6 von 351). Der Knoten warnt deshalb dreimal wie mitgegeben, dann hat ihn seine Erfahrung überstimmt, und die eingebaute LED blitzt nicht mehr blau. Die feste Regel hätte 345 Fehlwarnungen gegeben. Daraus folgt eine offene Frage: Ein träges Signal braucht einen längeren Vorhersagehorizont als einen Takt.
- **Vokabular, Fassung 1 (Softwaretest).** Zehn feste Wörter nach den Regeln aus „Vokabular: Entwurf“. Die Nummern 1 bis 4 sind die bisherigen Token. Dazu kommen je zwei Wörter für Temperatur, Speicher und Hauptschleife, jedes mit Oberbegriff und Bedeutung. Ein Test schlägt an, sobald jemand eine bestehende Nummer ändert. Das ist eine erste Antwort auf „Wie viele Wörter braucht der feste Kern wirklich?“: für einen Körper mit drei Signalen zehn.
- **Der Blick entscheidet über das Erbe (gemessen, auf dem Rechner nachgerechnet).** Denkt der Knoten seine gelernte Tabelle 30 bis 60 Takte weiter, kündigt er im Mitschnitt alle 20 Hitzephasen an, im Median 30 bzw. 56 s vorher. Er warnt dann bei jedem warmen Takt wie die feste Regel. Dieselbe Erfahrung widerlegt das Erbe bei einem Takt Blick und bestätigt es bei einer Minute. Ein Wissen ist also immer nur für einen Zeitraum richtig oder falsch.
- **Mehr Wörter allein bringen noch nichts (gemessen).** Auf dem Tisch schwankt nur die Temperatur, das feine Vokabular entscheidet darum genau wie die drei alten Wörter. Ein erster Vorschlag für den wachsenden Rand, Wörter für „wird wärmer“ und „kühlt ab“, ist nicht bestätigt: Er verschiebt die Warnungen nach vorn, beseitigt aber die Fehlalarme durch Nachwärme nicht. Dagegen hilft eher ein längerer Zusammenhang als ein größeres Wörterbuch. Das ist der erste echte Fall von „Vorschlag, bestätigt, abgelehnt“.
- **Wer immer warnt, verpasst nichts (gemessen, auf dem Rechner nachgerechnet).** Der Mitschnitt lief sechs Stunden. Nach den 41 Minuten, an denen die Blickweite gewählt wurde, folgten 114 Hitzephasen. Zählt man Alarme als Warnläufe, scheint der gelernte Blick die feste Regel zu schlagen, bei einer Minute mit 50 statt 130 Fehlalarmen. „Immer warnen“ hätte aber nur einen, denn ein durchgehender Lauf reicht von Phase zu Phase. Je Takt gezählt bleibt die feste Regel vorn. Sie warnt in 44 % der ruhigen Takte, und auf 60 % ihrer Warnungen folgt binnen einer Minute Hitze. Der gelernte Blick warnt in 72 % und trifft zu 48 %, kaum anders als immer warnen (50 %). Drei Zustände verraten nicht, ob nach einem OK die nächste Hitze nah ist. Für eine Entscheidung zählt also, was jeder Warntakt kostet, so wie Daniels Systemversuch in Reservetakten rechnet.
- **Der Knoten spürt Speicher und Hauptschleife (gemessen).** Seit 0.5 kann sich der S3 selbst Speicher wegnehmen und seine Hauptschleife anhalten. Wie bei der Last erfährt der Knoten davon nur über seine Messwerte. Ein Leck nahm ihm 4 KiB je Takt, bis nur noch 13.860 Byte frei waren. Er stufte das als knapp und dann als voll ein, lief pünktlich weiter und gab danach alles frei. Eine Bremse hielt die Hauptschleife je Takt 10 ms länger an, bis 300 ms, und seine Lückenmessung folgte ihr auf weniger als eine Millisekunde. Den weiten Blick rechnet er jetzt selbst, 600 Takte in 2,6 ms, und entscheidet in jeder Probe wie Python. Damit können die Wörter für Speicher und Schleife erstmals Erfahrungen sammeln.
- **Ein Wort je Takt verdeckt das zweite Signal (gemessen, auf dem Rechner nachgerechnet).** In einer Stunde mit Last, Leck und Bremse kündigen sich Speicher und Schleife verlässlich an: Auf knapp folgt immer voll, auf zäh immer steht. Die Wärme kündigt Hitze nur zu 61 % an. Feste Regel und Gedächtnis warnen bei allen dreien gleich, und das feine Vokabular entscheidet wie das grobe. Fällt eine Bremse in eine Hitzephase, zählt das schwerere Wort, und ihr Vorzeichen geht unter. Das betrifft „Vokabular: Entwurf“: Ein Takt kann mehr als einen Zustand haben, und wer die nächste Handlung wählen will, muss wissen, welches Organ ausfällt. Ein eigenes Gedächtnis je Signal hebt die Verdeckung auf und sah die verdeckte Bremsphase vorher. Im Zustand OK rät es aber genauso wie die anderen. Nach 54 Minuten setzte ihn ein anderes Programm zurück, das am selben USB nach einem anderen Gerät suchte. Für den Chip sieht so ein Reset aus wie Einschalten, wer ihn ausgelöst hat, erfährt er nicht.
- **Das Erbe verblasst nie, und so lernt das Gedächtnis keine Ausnahme (gemessen, auf dem Rechner nachgerechnet).** Sechs Stunden lang wurde knapper Speicher acht Durchgänge lang voll und die nächsten acht nicht, im Wechsel. Kein Verfahren lernt den Wechsel, alle warnen im flachen Block wie im tiefen. Das Erbe „auf knapp folgt voll“ zählt immer drei Beobachtungen, die eigene Erfahrung „auf knapp folgt frei“ kommt nicht über 1,3. Sie altert mit jedem Takt, in dem der Speicher knapp bleibt, nicht erst mit dem nächsten Erlebnis. In einer Gegenprobe ohne Erbe folgt das Gedächtnis dem letzten Durchgang und trifft zu 88 statt 51 %, verpasst aber den ersten Ausfall jedes Blocks. Das berührt den Kern der Idee: Wie lässt ererbtes Wissen eine Ausnahme zu, und altert Erfahrung nach Erlebnissen oder nach der Zeit im selben Zustand?
- **Absender und Sitzung (Softwaretest, Daniel).** Jede Meldung trägt die Nummer ihres Knotens, eine frische 128-Bit-Sitzung und die Runde der Abfrage, auf die sie antwortet. Startet ein Knoten oder die Zentrale neu, gibt es neue Sitzungen, und alte Pakete werden verworfen. Kommt dieselbe Frage zweimal, schickt der Knoten die gespeicherte Antwort und lernt die Beobachtung nicht doppelt. Wie frisch ein Wissen ist, misst allein die Uhr des Empfängers, und zwar ab der Frage. Abgelaufenes Wissen heißt „unbekannt“, nicht AUSFALL. Das führt „Gesendet ist nicht empfangen“ weiter. Im gestörten Lauf mit Verlust, Kopie, Bitfehler, alten Sitzungen und Verspätung werden 112 Meldungen angenommen und alle sechs falschen verworfen. Zwischen zwei Prozessen auf einem Rechner passen über UDP 480 von 480 Antworten zur Rechnung in Python. Knotennummer und Sitzung kann ein Angreifer nachbilden, gegen ihn hilft erst ein authentifizierter Weg (siehe „Sicherheit: fester Kern und lebendiges Gedächtnis“).
- **Das Gedächtnis schlägt vor, der feste Kern handelt (synthetisch, Daniel).** Ein fester Disponent gibt in jedem Takt einen Auftrag an den Primär- oder den Reserve-Arbeiter, zwei echte Prozesse. Eine Vorwarnung reserviert die Reserve für den nächsten Takt. Ein Ausfall sperrt den Primär-Arbeiter bei jeder Regel, und ohne aktuellen Zustand wird ausgesetzt statt geraten. Ausgesetzt wird so nur der erste Ausfalltakt, wenn keine Vorwarnung ihn angekündigt hat. Der Versuch rechnet also die bekannte Warnbilanz in Kosten um, mit einem Takt Blick. Ob sich Lernen lohnt, hängt dann am Preis eines ausgesetzten Auftrags. Verliert das Vorzeichen seine Bedeutung, spart Erbe und Kontext gegenüber der festen Regel 2.918 Reservetakte und setzt 118 Aufträge mehr aus. Das lohnt sich, solange ein ausgesetzter Auftrag weniger kostet als etwa 25 Reservetakte. Kehrt die alte Bedeutung zurück, liegt die Grenze schon bei 5,5. Den Preis muss Alex für einen echten Fall festlegen.

## Offen und zu entscheiden

- **Abruf (Entscheidung Alex):** Laut dieser Sammlung steigt die Stärke einer Erinnerung bei jedem Abruf, und der Abruf verändert den Inhalt. Im Labor verändert ein Abruf nichts, und ein eigener Alarm zählt nie als Lernbeispiel, damit sich das System nicht selbst bestätigt. **Vorschlag (Claude):** zwei Werte pro Eintrag, ein Beleg, der nur durch Beobachtung wächst, und ein Behalten, das durch Nutzung wachsen darf.
- **Absender:** Die Fünf-Byte-Meldung kennt weder Sender noch Sitzung. Daniels Verbund löst das in der Simulation und zwischen zwei Prozessen auf einem Rechner. Vor dem zweiten echten Knoten fehlen noch ein vertrauenswürdiger Weg, auf dem ein neuer Knoten seine Sitzung erhält, und der erste Lauf über echte Geräte, etwa ein Knoten auf dem Pi und die Zentrale auf dem Mac (siehe „Identität, Hardware und Rolle“ und „Assimilation neuer Hardware“).
- **Anschluss:** Verbund, Disponent und Körpermodus laufen noch getrennt. Der Verbund fragt ab, der Körper misst im eigenen Takt. Gelernt werden darf nur an einer Stelle, sonst zählt dieselbe Beobachtung zweimal. Eine Warnung „binnen 30 Takten“ aus dem Vokabular braucht außerdem einen eigenen Zeitvertrag für die Reservierung.
- **Ein echter Fall:** Gebraucht wird ein Signal mit schleichendem Vorlauf, denn ein hart ausfallender Dienst liefert eine Spur ohne Vorzeichen. Ein Kandidat wäre die Signalstärke oder Latenz eines ESP zum Router vor einem WLAN-Abriss. Das entspräche „Verbindung langsam“ und „Verbindung weg“ aus dem Vokabularentwurf und wäre zugleich Körperwahrnehmung.
- **Noch nicht berührt:** Abruf über Ähnlichkeit, das wachsende Vokabular, Verdichten über einzelne Übergänge hinaus und die Schlafphasen.
