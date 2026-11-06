# Firmware/Python – vorab festgelegter Prüfplan

Auftrag 3, 6. November 2026. Ausschließlich synthetische Eingaben; keine Aufnahmen.
Geschützte Quellen und Firmware bleiben unverändert. Mutation ausschließlich in
wegwerfbaren Kopien. Tests werden vom jeweiligen Laborordner gestartet.

## Vergleich vor der Rechnung

- Vier Regeln zeit/kontext/erbe/startwert; jeder Blick 1 bis 600.
- Zwei deterministische Seeds 730001 und 730002 pro Regel/Blick; 48 neue
  Beobachtungen pro Fall: insgesamt 4800 Fälle und 230400 Beobachtungen.
- Zufällige Zustände sowie obligatorische Lücken, ungültige Zeilen, zufällig
  platzierte SICHERN/LADEN und NEUER_LAUF mitten im Fall. Nach NEUER_LAUF wird
  zuerst der zurückgesetzte Blick 1 geprüft, anschließend der Fallblick gesetzt.
- Jede Ausgabezeile wird mit einem unabhängig geführten Python-Knoten und
  explizitem Befehlszustand verglichen. Kein bloßer Vergleich von Endständen.
- Zusätzliche Körperproben für Blick 1/2/30/600 und beide Seeds: 32 Fälle,
  je 40 Messwerte, Prozesswechsel mit LADEN und 12 Fortsetzungswerte; automatisches
  Sichern mit Intervall 3/5/7. Nach LADEN ist der erste Körpermesstakt Standtakt+2
  (ein zusätzlicher Takt Pause); direkte Replay-Zeilen behalten ihren expliziten Takt.
- Gesicherte Header, CRC und Matrizen werden separat mit Python verglichen.
  Entscheidungen und Protokollzeilen exakt; Matrixwerte mit absoluter Toleranz
  2e-12 (keine Warnentscheidung wird über eine Toleranz passend gemacht).
- AG01 aller drei alten Regeln wird in Startwert-Firmware angeboten: erwartete
  Ablehnung ohne Zustandsänderung. Randtakte, Fehlzeilen und Reset gesondert.
- Fehlerbericht: Regel/Blick/Seed/Fall und erste abweichende Zeile sowie gesamte
  Zahl abweichender/fehlender/zusätzlicher Zeilen. Keine privaten Pfade.

## Mutation vor der Rechnung

16 einzeln angewandte Mutanten, vier je kern.py, vokabular.py, neustart.py,
esp32/Lernknoten/Knoten.h. Exakte Ersetzungen stehen im Skript. Jede Kopie enthält
nur Projektquellen, keine Messungen, Git-Metadaten, Artefakte oder Kontaktdaten.
Pro Mutant wird die vollständige vorhandene test_labor-Suite ausgeführt.
Gezielte neue Regressionen laufen danach; nur Assertion-Fehlschläge gelten als
getötet. Kompilierungsfehler, Laufzeitfehler und Timeouts sind getrennte Klassen.
Originaltests müssen grün sein. Überlebende Mutanten werden je mit einem neuen
am Original grünen, am Mutanten roten Regressionstest dokumentiert.

Quellenhashes vor/nach Ausführung, Compilerflags und neutrale Compilerkennung,
Seeds, Zähler, Exitcodes und Fehlerklassen werden im JSON-Bericht festgehalten.
Dies ist eine begrenzte deterministische Last- und Vertragsprüfung, kein Beweis
für alle Spuren, keine Millionenspuren-Behauptung und kein ESP32-Hardwaretest.
Warnleistungs-Vergleichstabellen werden hier nicht erstellt; „Immer warnen“ ist
kein Firmware-Paritätsoracle und wird nicht als zusätzliche Lernregel ausgegeben.
Bei echten Originalfehlern nur reproduzierbarer Test und Bericht, keine Reparatur.

## Entwicklungskorrektur vor dem verbindlichen Mutationslauf

Der erste isolierte Mutationslauf hatte eine fehlende Testfixture und ist als
Infrastrukturprobe verworfen. Die bestehende Suite erwartet 12 Loopbackzeilen.
Der Runner erzeugt dafuer ausschliesslich synthetisch sechs erfolgreiche und
sechs abgelehnte Verbindungen; keine Messaufnahme wird gelesen/kopiert. Eine
unveraenderte Quellkopie mit derselben Fixture muss vor Mutationen gruen sein.
Der erste vollstaendige Paritaetslauf war ohne Abweichung; nach Ergaenzung der
Nichtendlichkeitspruefung fuer NVS-Matrixwerte und der Skripthashes wird er
unveraendert erneut ausgefuehrt. Seeds und Verfahren bleiben gleich.
