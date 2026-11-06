# Firmware/Python: vorab begrenzter Langlauf

Neue Ergänzung zur bereits ausgeführten Kurzspurenprüfung, keine Änderung der
bisherigen Prüfer oder Produktionsquellen. Keine Aufnahmen, ausschließlich
künstliche Zustände. Es werden vier lange Lerngeschichten geprüft, nicht eine
Million verschiedener Spuren.

- Genau vier Regeln in Reihenfolge zeit, kontext, erbe, startwert.
- Je 250000 neue Beobachtungen: insgesamt 1000000 Beobachtungen.
- Feste neue Seeds 730101,730102,730103,730104. RNG wie im Runner vorab festgelegt:
  random.Random('OSCAN-FIRMWARE-LANGLAUF-v1:REGEL:SEED').
- Pro Beobachtung eine gleichverteilte Zustandsziehung. An den Positionen
  1,2,3 modulo64 ersetzt das feste Tripel OK,SCHWACH,AUSFALL diese Ziehung;
  dort kein ausgelassener Takt. Damit werden regelmäßige Ausgänge tatsächlich
  erlebt. An anderen durch997 teilbaren Beobachtungsnummern eine Lücke mit
  Schrittweite2..7; die Nummern zählen Beobachtungen, nicht logische Takte.
- BLICK1, bis vor der Beobachtung249489 BLICK600 gesetzt wird: die letzten
  512 Beobachtungen je Regel, insgesamt2048. Keine erneute kurze Rasterreihe.
- Nach Beobachtung62500,125000,187500 SICHERN, NVS vergleichen, eigenen
  Hostprozess neu starten, NEUER_LAUF→BLICK1→LADEN. Danach absolute Taktnummer
  fortsetzen. Dies prüft die geforderte Befehlsfolge zusätzlich über echte
  Prozesswechsel. Keine Neuanlage des gespeicherten Lernstands.
- Nach250000 abschließend SICHERN und NVS prüfen. Insgesamt16 gespeicherte
  Zwischen-/Endstände,12 LADEN. Die letzten512 Beobachtungen liegen vollständig
  nach dem letzten Wiederanlauf.

Verwendet werden unverändert firmwarepruefung.Oracle, compile_hosts, run_host,
difference und check_state. Jede Ausgabezeile einschließlich Warnung exakt.
Header und CRC nach bestehendem Vertrag, alle endlichen Matrixwerte mit der
bereits festgelegten absoluten Toleranz2e-12. Zusätzlich Hashes der erwarteten
und tatsächlichen NVS-Bytes und maximale Matrixabweichung diagnostisch berichten;
keine Warnentscheidung erhält eine Toleranz.

Für Startwert werden beobachtete Ausgänge aus SCHWACH, erste subnormale bzw.
Null-Erbgewichte sowie der gespeicherte Restwert erfasst. Rundung kann einen
positiven subnormalen Rest festhalten; exaktesNull wird nicht vorausgesetzt.
Ein passender Endrest allein ersetzt nicht die Protokollprüfung.

Vor und nach dem Lauf Hashes aller geschützten Quellen, der unveränderten
bisherigen Messskripte und der neuen Langlaufdateien. JSON enthält nur neutrale
Zähler, Seeds, Regel-/Abschnittskennungen, Prüfwerte und Hashes, keine lokalen
Pfade oder Kontaktdaten. Neue Ausgabeordner werden nicht überschrieben.
Bei einem echten Originalfehler: reproduzierbarer Bericht, keine Reparatur.
Kein ESP32-, Stromverlust-, Echtzeit- oder allgemeiner Korrektheitsnachweis.
