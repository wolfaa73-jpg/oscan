# Empfinden v2: zwei Entscheidungen von Alex, 11. November 2026

Nach der Durchsicht von v1 (PR #10) und der Nachrechnung an der Fahrt. v1 bleibt in EMPFINDEN-PLAN.md und in
`beispiele/` stehen. Eingebaut von Alex mit Claude auf dem Zweig `alex/empfinden-v2`, weil das Gesicht am selben
Abend aufs Gerät sollte. Noch nicht an den vier Aufnahmen neu nachgerechnet.

| Was | v1 | v2 | Warum |
| --- | --- | --- | --- |
| Halbwertszeit des langsamen Normals L | 86.400 Takte | 3.600 Takte | Alex: eine Stunde. Mit einem Tag blieb L nahe der ersten Messung, „woanders“ war auf der Fahrt in rund 90 % der Takte aktiv. |
| Stumme Takte nach geladenem Neustart | 600 | 0 | Alex: Er soll das Einschalten spüren. Auf der Fahrt fielen sonst 208 von 676 überraschten Takten weg. |
| Maßband lernt nach einem Neustart | erst nach 600 Takten | unverändert | Der Kälteschock des Einschaltens soll das Maß nicht verlängern. |
| Halbwertszeit des Maßbands von „woanders“ | 86.400 (gleich L) | 86.400, jetzt eigene Konstante | Mit einer Stunde lernte es jeden langsamen Wechsel mit: Ein Sprung von 37 auf 29 °C ergab nach 20 Minuten nur noch Stufe 1. Vorläufig, gesetzt. |
| Sendefehler des Funks | hält den Körpermodus an | nur noch im festgelegten Funkversuch | Unterwegs endete sonst das Protokoll des Tages. Sonst steht er als Reizbit 32 in der Körperzeile. |
| Sendeleistung des Funks | Vorgabe des Kerns, 20 dBm | 2 dBm | Gemessen am 11.11.: Bei 5 cm Abstand und 20 dBm kam am Display kein einziges Paket an, der Empfänger übersteuerte. Mit 2 dBm kamen sie mit −50 dBm an. Die Reichweite ist nicht gemessen. |
| Schalter „empfinden“ und „funk“ im Einstellungsspeicher | ohne Prüfung gelesen | erst `isKey` | Sonst schreibt der Kern beim Start eine Fehlerzeile. |

Die Kennung der Konstanten ist 2, das Gerät meldet `EMPFINDEN,ok,2,600,3600,3600,1800,0,600,200,500,1500`.
Das Format des gesicherten Stands ist unverändert.

Am Gerät gesehen am 11.11. abends: Knoten (S3) und Gesicht (Guition-C3) aufgespielt, das Display empfängt, die
Gesichter für eingespielte Messwerte (Pusten, Fön, Kühlpack) erscheinen. Mit eingeschaltetem Funk meldet der
Chip 52 bis 56 °C statt etwa 39 °C; das ist noch keine Messung nach FUNK-VORAB.md.

Offen: v2 an den vier Aufnahmen neben v1 nachrechnen. Ob das Maßband von „woanders“ ein eigenes werden kann,
ohne mitzuwachsen.
