"""Körpersignale des Knotens aufzeichnen und prüfen: Chiptemperatur, freier Speicher, Schleifenlücke."""
import argparse
import csv
import json
import signal
import statistics
import sys
import time
from contextlib import ExitStack
from dataclasses import asdict, astuple, dataclass
from pathlib import Path

import selbsterkundung
from boardprobe import antwort, bereit
from kern import Knoten, MAX_BLICK, REGELN, ZUSTAENDE

KOPF = ("takt", "zeit_ms", "temp_dc", "heap", "luecke_us", "zustand", "sofort", "vorwarnung", "reiz")
# Ältere Aufnahmen bleiben lesbar. Am 5. November hieß die letzte Spalte zuerst "last" und
# kannte nur die Last, die ersten Aufnahmen hatten sie noch gar nicht.
KOPF_LAST = KOPF[:-1] + ("last",)
KOPF_ALT = KOPF[:-1]
# Bits der Spalte reiz, wie reize() im Sketch.
LAST, LECK, BREMSE = 1, 2, 4
MAX_TEMP = 100000  # Zehntelgrad, wie maxTemp im Sketch


@dataclass(frozen=True)
class Grenzen:
    """Temperatur in Zehntelgrad, freier Speicher in Byte, Schleifenlücke in Mikrosekunden."""
    temp_schwach: int
    temp_ausfall: int
    heap_schwach: int
    heap_ausfall: int
    luecke_schwach: int
    luecke_ausfall: int

    def __post_init__(self):
        if not (all(type(w) is int and 0 <= w < 2**32 for w in astuple(self))
                and self.temp_schwach < self.temp_ausfall <= MAX_TEMP
                and self.heap_schwach > self.heap_ausfall
                and self.luecke_schwach < self.luecke_ausfall):
            raise ValueError("Grenzen müssen ganzzahlig und geordnet sein, SCHWACH vor AUSFALL.")

    def befehl(self):
        return ("GRENZEN " + " ".join(map(str, astuple(self)))).encode("ascii")


# Vorläufige Werte für eine erste Erkundung, nicht aus Datenblättern abgeleitet.
# Die Rohwerte bleiben erhalten, mit `spur --grenzen` lassen sie sich neu einstufen.
ERKUNDUNG = Grenzen(500, 600, 65536, 16384, 20000, 200000)


def einstufen(temp_dc, heap, luecke_us, g):
    """Wie einstufen in Koerper.h: der schlechteste Wert zählt, eine fehlende Temperatur nicht."""
    if (temp_dc is not None and temp_dc >= g.temp_ausfall) or heap <= g.heap_ausfall \
            or luecke_us >= g.luecke_ausfall:
        return "AUSFALL"
    if (temp_dc is not None and temp_dc >= g.temp_schwach) or heap <= g.heap_schwach \
            or luecke_us >= g.luecke_schwach:
        return "SCHWACH"
    return "OK"


def lies_koerperzeile(zeile):
    """K,takt,zustand,sofort,vorwarnung,temp_dc,heap,luecke_us,reiz"""
    teile = zeile.decode("ascii", "replace").split(",")
    if len(teile) != 9 or teile[0] != "K" or teile[2] not in ZUSTAENDE:
        raise ValueError(f"Unerwartete Körperzeile {zeile!r}.")
    takt, sofort, warnung, heap, luecke, reiz = (int(teile[i]) for i in (1, 3, 4, 6, 7, 8))
    temp = None if teile[5] == "-" else int(teile[5])
    return dict(takt=takt, temp_dc=temp, heap=heap, luecke_us=luecke, zustand=teile[2],
                sofort=sofort, vorwarnung=warnung, reiz=reiz)


# Speicherlage des Lecks, wie meldeSpeicher() im Sketch: am Boden, nach der Freigabe und wenn ein
# ganzer Block in kein freies Stück mehr passte (KLEIN).
SPEICHER_KOPF = ("takt", "ereignis", "versucht", "frei", "frei8", "groesster", "freie_bloecke",
                 "belegte_bloecke", "leckbloecke")
SPEICHER_EREIGNISSE = ("BODEN", "FREI", "KLEIN")


def lies_speicherzeile(zeile):
    """SPEICHER,takt,ereignis,versucht,frei,frei8,groesster,freie_bloecke,belegte_bloecke,leckbloecke"""
    teile = zeile.decode("ascii", "replace").split(",")
    if (len(teile) != 10 or teile[0] != "SPEICHER" or teile[2] not in SPEICHER_EREIGNISSE
            or teile[3] not in ("0", "1") or not all(t.isdigit() for t in teile[1:2] + teile[4:])):
        raise ValueError(f"Unerwartete Speicherzeile {zeile!r}.")
    return {f: w if f == "ereignis" else int(w) for f, w in zip(SPEICHER_KOPF, teile[1:])}


# Selbsterkundung wie Erkundung.h: Schalten eines Pins und Ergebnis eines Versuchs. Temperaturen in
# Hundertstelgrad, "-" bei einem Versuch, in dem ein Messwert fehlte.
PIN_KOPF = ("takt", "pin", "an", "grund")
VERSUCH_KOPF = ("takt", "pin", "art", "vor_hg", "nach_hg", "wirkung_hg", "mittel_hg", "streuung_hg", "anzahl",
                "urteil")
ERKUNDUNG_FELDER = ("ruhe", "an", "mittel", "schwelle", "fenster", "pruefe", "saat")


def _ganzzahl(text, vorzeichen=False):
    ziffern = text[1:] if vorzeichen and text.startswith("-") else text
    if not ziffern.isascii() or not ziffern.isdigit():
        raise ValueError
    return int(text)


def lies_pinzeile(zeile):
    """PIN,takt,pin,an,grund"""
    teile = zeile.decode("ascii", "replace").split(",")
    try:
        if len(teile) != 5 or teile[0] != "PIN" or teile[3] not in ("0", "1") \
                or teile[4] not in selbsterkundung.GRUENDE:
            raise ValueError
        return dict(takt=_ganzzahl(teile[1]), pin=_ganzzahl(teile[2]), an=int(teile[3]), grund=teile[4])
    except ValueError:
        raise ValueError(f"Unerwartete Pinzeile {zeile!r}.") from None


def lies_versuchszeile(zeile):
    """VERSUCH,takt,pin,art,vor_hg,nach_hg,wirkung_hg,mittel_hg,streuung_hg,anzahl,urteil"""
    teile = zeile.decode("ascii", "replace").split(",")
    try:
        if len(teile) != 11 or teile[0] != "VERSUCH" or teile[3] not in ("AN", "AUS") \
                or teile[10] not in selbsterkundung.URTEILE:
            raise ValueError
        ohne = teile[4:7] == ["-", "-", "-"]
        return dict(takt=_ganzzahl(teile[1]), pin=_ganzzahl(teile[2]), art=teile[3],
                    vor_hg=None if ohne else _ganzzahl(teile[4]), nach_hg=None if ohne else _ganzzahl(teile[5]),
                    wirkung_hg=None if ohne else _ganzzahl(teile[6], True), mittel_hg=_ganzzahl(teile[7], True),
                    streuung_hg=_ganzzahl(teile[8]), anzahl=_ganzzahl(teile[9]), urteil=teile[10])
    except ValueError:
        raise ValueError(f"Unerwartete Versuchszeile {zeile!r}.") from None


def lies_pinklassen(zeile, kopf):
    """kopf,1F,2F,4M,… wie meldePins() im Sketch: jeder erlaubte Pin in seiner Reihenfolge mit seiner Klasse.
    Gibt {pin: klasse} zurück, None, wenn die Zeile nicht so aussieht."""
    teile, n = zeile.split(b","), kopf.count(b",") + 1
    if b",".join(teile[:n]) != kopf or len(teile) != n + len(selbsterkundung.ERLAUBTE_PINS):
        return None
    klassen = {}
    for pin, eintrag in zip(selbsterkundung.ERLAUBTE_PINS, teile[n:]):
        text = eintrag.decode("ascii", "replace")
        if text[:-1] != str(pin) or len(text[-1:]) != 1 or text[-1] not in selbsterkundung.KLASSEN:
            return None
        klassen[pin] = text[-1]
    return klassen


# Zeilen, die der Körperzeile eines Takts folgen können, und die Datei neben der Aufnahme, in die sie gehen.
# Selbstvorhersage wie Vorhersage.h: Vorhersagen für in 10 und 60 Takten, Fehler der vor 10 Takten abgegebenen,
# sein Mittel, die Grenze und ob der Knoten überrascht ist. Temperaturen in Tausendstelgrad (mg).
VORHERSAGE_KOPF = ("takt", "v10_mg", "v60_mg", "fehler_mg", "mittel_mg", "grenze_mg", "ueberrascht")
VORHERSAGE_FELDER = ("kurz", "lang", "vergessen_e4", "deckel", "mittel", "norm_halbwert", "norm_ab", "anlauf",
                     "faktor_e1")
VORHERSAGE_TOLERANZ_MG = 2


def lies_vorhersagezeile(zeile):
    """VORHERSAGE,takt,v10_mg,v60_mg,fehler_mg,mittel_mg,grenze_mg,ueberrascht"""
    try:
        teile = zeile.decode("ascii").split(",")
        if len(teile) != 8 or teile[0] != "VORHERSAGE" or teile[7] not in ("0", "1") \
                or (teile[4] == "-") != (teile[5] == "-") or (teile[4] == "-") != (teile[6] == "-"):
            raise ValueError
        werte = [_ganzzahl(teile[1]), _ganzzahl(teile[2], True), _ganzzahl(teile[3], True)]
        werte += [None if t == "-" else _ganzzahl(t, True) for t in teile[4:7]]
    except (ValueError, UnicodeDecodeError):
        raise ValueError(f"Unerwartete Vorhersagezeile {zeile!r}.") from None
    return dict(zip(VORHERSAGE_KOPF, werte + [int(teile[7])]))


def lies_vorhersagestart(zeile):
    """VORHERSAGE,ok und die neun Konstanten des Geräts als dict, sonst None."""
    teile = (zeile or b"").split(b",")
    if teile[:2] != [b"VORHERSAGE", b"ok"] or len(teile) != 2 + len(VORHERSAGE_FELDER) \
            or not all(t.isdigit() for t in teile[2:]):
        return None
    return dict(zip(VORHERSAGE_FELDER, map(int, teile[2:])))


EMPFINDEN_KOPF = ("takt", "gerade", "woanders", "anlauf", "gueltig", "mass_gerade_mg", "mass_woanders_mg", "mittel_mg", "langsam_mg")
EMPFINDEN_FELDER_V1 = ("version", "mittel_halbwert", "langsam_halbwert", "mass_gerade_halbwert", "anlauf", "wiederanlauf", "norm_ab", "boden_gerade_mg", "boden_woanders_mg", "hysterese_e3")

EMPFINDEN_FELDER = EMPFINDEN_FELDER_V1 + ("mass_woanders_halbwert", "start_woanders_mg")


def lies_empfindenstart(zeile):
    teile = (zeile or b"").split(b",")
    if len(teile) < 3 or teile[:2] != [b"EMPFINDEN", b"ok"] or teile[2] not in (b"1", b"2"):
        return None
    felder = EMPFINDEN_FELDER_V1 if teile[2] == b"1" else EMPFINDEN_FELDER
    if len(teile) != 2 + len(felder) or not all(t.isdigit() for t in teile[2:]):
        return None
    return dict(zip(felder, map(int, teile[2:])))


def lies_empfindenzeile(zeile):
    try:
        teile = zeile.decode("ascii").split(",")
        if len(teile) != 10 or teile[0] != "EMPFINDEN":
            raise ValueError
        werte = [_ganzzahl(t, True) for t in teile[1:]]
        if werte[0] < 1 or any(abs(x) > 30 for x in werte[1:3]) or any(x not in (0, 1) for x in werte[3:5]) or any(x < 0 for x in werte[5:7]):
            raise ValueError
    except (ValueError, UnicodeDecodeError):
        raise ValueError("Ungültige Empfinden-Zeile") from None
    return dict(zip(EMPFINDEN_KOPF, werte))


NEBENZEILEN = ((b"EMPFINDEN,", ".empfinden.csv", EMPFINDEN_KOPF, lies_empfindenzeile),
               (b"SPEICHER,", ".speicher.csv", SPEICHER_KOPF, lies_speicherzeile),
               (b"VORHERSAGE,", ".vorhersage.csv", VORHERSAGE_KOPF, lies_vorhersagezeile),
               (b"PIN,", ".pin.csv", PIN_KOPF, lies_pinzeile),
               (b"VERSUCH,", ".versuch.csv", VERSUCH_KOPF, lies_versuchszeile))


def exklusiv(port):
    """Belegt den seriellen Port für diesen Prozess allein, bis er geschlossen wird. Jedes weitere
    Öffnen scheitert dann mit EBUSY, auch das eines fremden Programms, das sonst über DTR/RTS das
    Gerät mitten in der Aufnahme zurücksetzen könnte. So geschah es am 5. November."""
    import fcntl
    import termios
    fcntl.ioctl(port.fileno(), termios.TIOCEXCL)


def nachlese(port, leer=4, hoechstens=8.0):
    """Was nach einer unerwarteten Zeile noch kommt, etwa die Startmeldungen nach einem Neustart.
    Liest, bis leer Lesefristen in Folge nichts brachten (am Gerät je 0,6 s), höchstens hoechstens s."""
    zeilen, stumm, ende = [], 0, time.monotonic() + hoechstens
    while stumm < leer and time.monotonic() < ende:
        zeile = port.readline().strip()
        if zeile:
            zeilen.append(zeile)
            stumm = 0
        else:
            stumm += 1
    return zeilen


def lastdauern(saat, an_s, aus_s, anzahl):
    """Die ersten anzahl Phasendauern in Sekunden, abwechselnd Arbeit und Ruhe, wie Lastplan in Reize.h."""
    zufall, dauern = saat, []
    for i in range(anzahl):
        hoechstens = aus_s if i % 2 else an_s
        if not zufall or not hoechstens:
            dauern.append(hoechstens)
            continue
        zufall ^= (zufall << 13) & 0xFFFFFFFF
        zufall ^= zufall >> 17
        zufall ^= (zufall << 5) & 0xFFFFFFFF
        unten = hoechstens // 4 or 1
        dauern.append(unten + zufall % (hoechstens - unten + 1))
    return dauern


def aufnehmen(port, regel, grenzen, intervall_ms, takte, ziel, last=None, blick=1, leck=None, bremse=None,
              fortsetzen=None, sichern_alle=0, melder=None, erkundung=None, vorhersage=False, empfinden=False):
    """Körpermodus starten und jede Zeile mitschreiben. Gibt die Zahl der Takte zurück.

    last=(an_s, aus_s) lässt Kern 0 in diesem Rhythmus arbeiten. Mit einer Saat als drittem Wert
    dauert jede Phase zufällig lang, von einem Viertel bis zum vollen Wert (lastdauern). leck=(byte, boden, halten,
    pause), wahlweise mit flachem Boden und Muster, belegt Speicher, bremse=(start, schritt, bis,
    halten, pause) hält die Hauptschleife an, beide wie LECK und BREMSE im Sketch. Der Knoten spürt alle Reize nur über seine
    Messwerte. blick sind die Takte, die seine Vorwarnung vorausdenkt.

    Weiterlernen über Läufe: fortsetzen ist die vorige Aufnahme im selben Ordner. Das Gerät lädt
    dann seinen gesicherten Stand, statt bei null zu beginnen, und lässt einen Takt Lücke.
    sichern_alle lässt es jeden n-ten Takt selbst sichern und am Ende noch einmal. Takte, die nach
    STOP noch kommen, werden dafür mitgeschrieben, sonst passte der Endstand nicht zur Datei.

    melder (aus melder.py) bekommt jede Körperzeile und meldet Warnungen weiter, etwa per MQTT.

    Meldet die Firmware die Speicherlage des Lecks (SPEICHER,…), landen diese Zeilen in
    <name>.speicher.csv. Ohne solche Zeilen entsteht die Datei nicht.

    erkundung=(ruhe, an, mittel, schwelle, fenster, pruefe, saat) startet die Selbsterkundung wie
    ERKUNDUNG im Sketch. Die Klassen der passiven Pinprobe stehen danach in der JSON, die Zeilen PIN,…
    und VERSUCH,… in <name>.pin.csv und <name>.versuch.csv.

    vorhersage=True startet die Selbstvorhersage wie VORHERSAGE 1 im Sketch, bei null. Die Konstanten, die
    das Gerät dazu meldet, stehen danach in der JSON, die Zeilen VORHERSAGE,… in <name>.vorhersage.csv.

    Kommt statt einer Körperzeile etwas anderes, etwa das Startbanner nach einem Neustart,
    hebt <name>.abbruch.txt diese Zeile und alles danach auf, mit dem Grund des Neustarts."""
    if empfinden:
        if intervall_ms != 1000 or fortsetzen is not None:
            raise ValueError("Empfinden-Aufnahme braucht 1000 ms und einen frischen Lauf")
        vorhersage = True
    if not 100 <= intervall_ms < 2**32:
        raise ValueError("Das Intervall muss mindestens 100 ms betragen.")
    if last is not None and not (len(last) in (2, 3) and all(type(s) is int and 0 <= s <= 3600 for s in last[:2])
                                 and all(type(s) is int and 0 <= s < 2**32 for s in last[2:])):
        raise ValueError("Last und Pause in ganzen Sekunden bis 3600, wahlweise eine Saat ab null.")
    if type(blick) is not int or not 1 <= blick <= MAX_BLICK:
        raise ValueError(f"Der Blick muss 1 bis {MAX_BLICK} Takte betragen.")
    # Die Bereiche von Leck und Bremse prüft das Gerät, hier nur die Form.
    for name, werte, anzahl in (("Leck", leck, (4, 6)), ("Bremse", bremse, (5,))):
        if werte is not None and (len(werte) not in anzahl or not all(type(w) is int and 0 <= w < 2**32 for w in werte)):
            raise ValueError(f"{name} braucht {' oder '.join(map(str, anzahl))} ganze Zahlen ab null.")
    if type(sichern_alle) is not int or not 0 <= sichern_alle < 2**32:
        raise ValueError("Sichern alle n Takte braucht eine ganze Zahl ab null.")
    if erkundung is not None:
        # Dieselben Regeln wie im Gerät, geprüft an einem Platzhalter-Pin.
        if len(erkundung) != len(ERKUNDUNG_FELDER):
            raise ValueError(f"Die Erkundung braucht {len(ERKUNDUNG_FELDER)} ganze Zahlen.")
        selbsterkundung.Erkundung([1], *erkundung, warm=grenzen.temp_schwach)
    if fortsetzen is not None:
        # pruefen findet die vorige Aufnahme über ihren Namen neben dieser.
        if fortsetzen.parent.resolve() != ziel.parent.resolve():
            raise ValueError("Die fortgesetzte Aufnahme muss im selben Ordner liegen.")
        if lies_aufnahme(fortsetzen)[0]["regel"] != regel:
            raise ValueError("Fortgesetzt wird nur mit derselben Lernregel.")
    abbruch = ziel.with_name(ziel.stem + ".abbruch.txt")
    nebenziele = {praefix: ziel.with_name(ziel.stem + endung) for praefix, endung, _, _ in NEBENZEILEN}
    if ziel.exists() or ziel.with_suffix(".json").exists() or abbruch.exists() \
            or any(p.exists() for p in nebenziele.values()):
        raise ValueError(f"{ziel} oder eine zugehörige .json, .abbruch.txt oder Nebendatei "
                         f"({', '.join(e for _, e, _, _ in NEBENZEILEN)}) gibt es schon.")
    bereit(port, regel)
    anzahl = 0
    stille = 3 * intervall_ms / 1000 + 1
    gestoppt = False
    try:
        port.write(grenzen.befehl() + b"\n")
        if (erhalten := antwort(port, nach_handschlag=True, frist=3.0)) != b"GRENZEN,ok":
            raise ValueError(f"Grenzen nicht übernommen, erhalten {erhalten!r}.")
        # Blick und Reize vor dem Körpermodus, damit keine Körperzeile vor einer Bestätigung kommt.
        befehle = [(f"BLICK {blick}", b"BLICK,ok", "Blick nicht übernommen")]
        if sichern_alle:
            befehle.append((f"SICHERN_ALLE {sichern_alle}", b"SICHERN_ALLE,ok", "Sichern nicht eingestellt"))
        if last is not None:
            befehle.append(("LAST " + " ".join(map(str, last)), b"LAST,ok", "Last nicht gestartet"))
        if leck is not None:
            befehle.append(("LECK " + " ".join(map(str, leck)), b"LECK,ok", "Leck nicht gestartet"))
        if bremse is not None:
            befehle.append(("BREMSE " + " ".join(map(str, bremse)), b"BREMSE,ok", "Bremse nicht gestartet"))
        if erkundung is not None:
            # Die Bestätigung trägt das Ergebnis der Pinprobe, deshalb keine feste Antwort.
            befehle.append(("ERKUNDUNG " + " ".join(map(str, erkundung)), None, "Erkundung nicht gestartet"))
        if vorhersage:
            befehle.append(("VORHERSAGE 1", lies_vorhersagestart, "Vorhersage nicht gestartet"))
        if empfinden:
            befehle.append(("EMPFINDEN 1", lies_empfindenstart, "Empfinden nicht gestartet"))
        if fortsetzen is not None:
            befehle.append(("LADEN", b"GELADEN", "Kein gesicherter Stand geladen"))
        befehle.append((f"KOERPER {intervall_ms}", b"KOERPER,an", "Körpermodus nicht gestartet"))
        klassen = konstanten = empfindenkonstanten = None
        for befehl, bestaetigung, fehler in befehle:
            port.write(befehl.encode("ascii") + b"\n")
            erhalten = antwort(port, frist=3.0)
            if bestaetigung is None:
                klassen = lies_pinklassen(erhalten, b"ERKUNDUNG,ok")
                if klassen is None:
                    raise ValueError(f"{fehler}, erhalten {erhalten!r}.")
            elif callable(bestaetigung):
                gelesen = bestaetigung(erhalten)
                if bestaetigung is lies_empfindenstart:
                    empfindenkonstanten = gelesen
                else:
                    konstanten = gelesen
                if gelesen is None:
                    raise ValueError(f"{fehler}, erhalten {erhalten!r}.")
            elif erhalten != bestaetigung:
                raise ValueError(f"{fehler}, erhalten {erhalten!r}.")
        meta = dict(regel=regel, intervall_ms=intervall_ms, grenzen=asdict(grenzen), blick=blick,
                    last=None if last is None else list(last), leck=None if leck is None else list(leck),
                    bremse=None if bremse is None else list(bremse), beginn=time.strftime("%Y-%m-%d %H:%M"),
                    fortsetzung=None if fortsetzen is None else fortsetzen.name, sichern_alle=sichern_alle)
        # Nur mit Erkundung, damit die JSON älterer Versuchsaufbauten Feld für Feld gleich bleibt.
        if erkundung is not None:
            meta["erkundung"] = dict(zip(ERKUNDUNG_FELDER, erkundung), pins={str(p): k for p, k in klassen.items()})
        if vorhersage:
            meta["vorhersage"] = konstanten
        if empfinden:
            meta["empfinden"] = empfindenkonstanten
        with ziel.with_suffix(".json").open("x", encoding="utf-8") as datei:
            json.dump(meta, datei, ensure_ascii=False, indent=1)
        with ziel.open("x", encoding="utf-8", newline="") as datei, ExitStack() as nebendateien:
            schreiber = csv.writer(datei)
            schreiber.writerow(KOPF)
            beginn = letzte = time.monotonic()
            neben = {}  # Datei und Schreiber je Art, sobald die erste Zeile dieser Art kommt

            def schreibe(zeile):
                nonlocal anzahl, letzte
                for praefix, _, kopf, lies in NEBENZEILEN:
                    if not zeile.startswith(praefix):
                        continue
                    try:
                        werte = lies(zeile)
                    except ValueError:
                        break  # bricht unten ab wie jede andere unerwartete Zeile
                    if praefix not in neben:
                        aus = nebendateien.enter_context(nebenziele[praefix].open("x", encoding="utf-8", newline=""))
                        neben[praefix] = (aus, csv.writer(aus))
                        neben[praefix][1].writerow(kopf)
                    neben[praefix][1].writerow(["-" if werte[feld] is None else werte[feld] for feld in kopf])
                    neben[praefix][0].flush()
                    return
                try:
                    k = lies_koerperzeile(zeile)
                except ValueError:
                    text = [z.decode("ascii", "replace") for z in [zeile] + nachlese(port)]
                    with abbruch.open("x", encoding="utf-8") as aus:
                        aus.write("\n".join(text) + "\n")
                    grund = [z for z in text if z.startswith(("rst:", "NEUSTART,"))]
                    raise ValueError(f"Unerwartete Zeile nach {anzahl} Takten: {text[0]!r}"
                                     + "".join(f", {z}" for z in grund) + f". Alles Weitere in {abbruch.name}.")
                letzte = time.monotonic()
                k["zeit_ms"] = round((letzte - beginn) * 1000)
                k["temp_dc"] = "-" if k["temp_dc"] is None else k["temp_dc"]
                schreiber.writerow([k[feld] for feld in KOPF])
                datei.flush()
                anzahl += 1
                if melder is not None:
                    melder.takt(k)

            try:
                while takte is None or anzahl < takte:
                    zeile = port.readline().strip()
                    if not zeile:
                        if time.monotonic() - letzte > stille:
                            raise ValueError(f"Seit {stille:.0f} s keine Körperzeile mehr.")
                        continue
                    schreibe(zeile)
            except KeyboardInterrupt:
                pass
            if sichern_alle:
                port.write(b"STOP\n")
                gestoppt = True
                while (zeile := port.readline().strip()) != b"KOERPER,aus":
                    if not zeile:
                        if time.monotonic() - letzte > stille:
                            raise ValueError("Nach STOP kam kein KOERPER,aus.")
                        continue
                    schreibe(zeile)
                port.write(b"SICHERN\n")
                if (erhalten := antwort(port, frist=3.0)) != b"GESICHERT":
                    raise ValueError(f"Endstand nicht gesichert, erhalten {erhalten!r}.")
    except KeyboardInterrupt:
        pass
    finally:
        if not gestoppt:
            port.write(b"STOP\n")
        if melder is not None:
            melder.ende()
    return anzahl


def pins_lesen(port, regel):
    """Was an den erlaubten Pins hängt, als {pin: klasse}, über PINS. Das Gerät treibt dabei keinen Pin."""
    bereit(port, regel)
    port.write(b"PINS\n")
    erhalten = antwort(port, nach_handschlag=True, frist=3.0)
    if (klassen := lies_pinklassen(erhalten, b"PINS")) is None:
        raise ValueError(f"Keine Pinübersicht erhalten, sondern {erhalten!r}.")
    return klassen


def lies_aufnahme(pfad):
    meta = json.loads(pfad.with_suffix(".json").read_text(encoding="utf-8"))
    with pfad.open(encoding="utf-8", newline="") as datei:
        zeilen = csv.reader(datei, strict=True)
        kopf = next(zeilen, None)
        if kopf not in (list(KOPF), list(KOPF_LAST), list(KOPF_ALT)):
            raise ValueError("Kopf der Aufnahme ist ungültig.")
        werte = []
        for nummer, zeile in enumerate(zeilen, start=2):
            if len(zeile) != len(kopf):
                raise ValueError(f"Zeile {nummer} ist unvollständig.")
            z = dict(zip(kopf, zeile))
            # "last" kannte nur die Last, also Bit 1. Ganz alte Aufnahmen hatten keine Reize.
            z.setdefault("reiz", z.pop("last", "0"))
            w = {f: int(z[f]) for f in KOPF if f not in ("temp_dc", "zustand")}
            w["temp_dc"] = None if z["temp_dc"] == "-" else int(z["temp_dc"])
            w["zustand"] = z["zustand"]
            werte.append(w)
    return meta, werte


def neu_einstufen(werte, g):
    return [(w["takt"], einstufen(w["temp_dc"], w["heap"], w["luecke_us"], g)) for w in werte]


def gelernt_bis(pfad, bis, kette=()):
    """Der Knoten einer Aufnahme nach ihrem Takt bis, samt allem, was sie fortsetzt. So stand er
    im Gerät, wenn es diesen Takt gesichert hat. bis muss ein Sicherungspunkt sein: ein Vielfaches
    von sichern_alle oder der letzte Takt."""
    if pfad.resolve() in kette:
        raise ValueError(f"{pfad.name} setzt sich selbst fort.")
    meta, werte = lies_aufnahme(pfad)
    alle = meta.get("sichern_alle") or 0
    if not werte or not alle or not (bis == werte[-1]["takt"] or werte[0]["takt"] <= bis < werte[-1]["takt"]
                                     and bis % alle == 0):
        raise ValueError(f"Takt {bis} ist kein Sicherungspunkt von {pfad.name}.")
    knoten = anfang(pfad, meta, werte, kette + (pfad.resolve(),))
    g = Grenzen(**meta["grenzen"])
    for w in werte:
        if w["takt"] > bis:
            break
        knoten.schritt(w["takt"], einstufen(w["temp_dc"], w["heap"], w["luecke_us"], g))
    return knoten


def anfang(pfad, meta, werte, kette=()):
    """Der Knoten vor dem ersten Takt einer Aufnahme. Eine Fortsetzung beginnt mit dem Stand, den das
    Gerät geladen hat, zwei Takte vor ihrem ersten. Dazwischen liegt die Lücke der Pause."""
    knoten = Knoten(REGELN[meta["regel"]](), blick=meta.get("blick", 1))
    if not meta.get("fortsetzung"):
        return knoten
    if not werte or werte[0]["takt"] < 3:
        raise ValueError(f"{pfad.name} setzt fort, beginnt aber nicht nach einer Lücke.")
    vorher = gelernt_bis(pfad.with_name(meta["fortsetzung"]), werte[0]["takt"] - 2, kette)
    if type(vorher.gedaechtnis) is not type(knoten.gedaechtnis):
        raise ValueError("Die fortgesetzte Aufnahme hat eine andere Lernregel.")
    knoten.gedaechtnis, knoten.takt, knoten.zustand = vorher.gedaechtnis, vorher.takt, vorher.zustand
    return knoten


def pruefen(pfad):
    """Jede Einstufung und jede Entscheidung des Geräts mit Python nachrechnen."""
    meta, werte = lies_aufnahme(pfad)
    g = Grenzen(**meta["grenzen"])
    knoten = anfang(pfad, meta, werte)
    for nummer, w in enumerate(werte, start=2):
        if einstufen(w["temp_dc"], w["heap"], w["luecke_us"], g) != w["zustand"]:
            raise ValueError(f"Zeile {nummer}: Einstufung {w['zustand']} passt nicht zu den Rohwerten.")
        s = knoten.schritt(w["takt"], w["zustand"])
        if (int(s.sofort), int(s.vorwarnung)) != (w["sofort"], w["vorwarnung"]):
            raise ValueError(f"Zeile {nummer}: Entscheidung weicht von Python ab.")
    erkundung_pruefen(pfad, meta, werte)
    vorhersage_pruefen(pfad, meta, werte)
    empfinden_pruefen(pfad, meta, werte)
    return meta, werte


def empfinden_pruefen(pfad, meta, werte):
    """Exakt jede Zeile nachrechnen, einschließlich Anlauf, Fehlwert und Normalmaß."""
    geraet = nebendatei(pfad, ".empfinden.csv", EMPFINDEN_KOPF)
    konstanten = meta.get("empfinden")
    if konstanten is None:
        if geraet:
            raise ValueError("Empfinden-Datei ohne Konstanten in der JSON")
        return None
    import empfinden as em
    felder = EMPFINDEN_FELDER
    if konstanten.get("version") == 1:
        from referenzen import empfinden_v1 as em
        felder = EMPFINDEN_FELDER_V1
    import selbstvorhersage as sv
    if tuple(konstanten.get(f) for f in felder) != em.KONSTANTEN:
        raise ValueError("Empfinden-Konstanten passen nicht zur Referenz")
    if meta.get("intervall_ms") != 1000 or meta.get("fortsetzung"):
        raise ValueError("Empfinden-Aufnahme muss frisch und im Sekundentakt sein")
    modell, v, soll = em.Empfinden(), sv.Selbstvorhersage(), []
    for w in werte:
        z = v.takt(w["temp_dc"], w["reiz"] & 1)
        soll.append(em.zeile(w["takt"], modell.takt(w["temp_dc"], None if z is None else z["mittel"])))
    if len(geraet) != len(soll):
        raise ValueError("Empfinden-Zeilenzahl stimmt nicht")
    for nr, (ist, erwartet) in enumerate(zip(geraet, soll), 1):
        if ist != erwartet:
            raise ValueError(f"Empfinden weicht in Zeile {nr} ab: {ist} statt {erwartet}")
    return len(soll)


def vorhersage_pruefen(pfad, meta, werte):
    """Jede Vorhersagezeile des Geräts mit selbstvorhersage.py nachrechnen, aus Temperatur und Last der
    Körperzeilen. Liefert None ohne Vorhersage, sonst (Zeilen, davon gleich, größte Abweichung in mg,
    Strecken mit Überraschung). Zahlen dürfen um VORHERSAGE_TOLERANZ_MG abweichen, weil Gerät und Rechner
    nicht jede Rundung gleich machen müssen; ob er überrascht ist, muss stimmen."""
    geraet = nebendatei(pfad, ".vorhersage.csv", VORHERSAGE_KOPF)
    konstanten = meta.get("vorhersage")
    if konstanten is None:
        if geraet:
            raise ValueError(f"{pfad.stem}.vorhersage.csv gibt es, aber die JSON nennt keine Vorhersage.")
        return None
    import selbstvorhersage  # braucht numpy, das der Aufnahme mit dem Python von PlatformIO fehlt
    if tuple(konstanten.get(f) for f in VORHERSAGE_FELDER) != selbstvorhersage.KONSTANTEN:
        raise ValueError(f"Die Konstanten des Geräts {konstanten} passen nicht zu selbstvorhersage.py "
                         f"{selbstvorhersage.KONSTANTEN}.")
    modell, soll = selbstvorhersage.Selbstvorhersage(), []
    for w in werte:
        z = selbstvorhersage.zeile(w["takt"], modell.takt(w["temp_dc"], w["reiz"] & 1))
        if z is not None:
            soll.append(z)
    if len(soll) != len(geraet):
        raise ValueError(f"{pfad.stem}.vorhersage.csv hat {len(geraet)} Zeilen, erwartet sind {len(soll)}.")
    gleich = groesste = 0
    for nummer, (a, b) in enumerate(zip(geraet, soll), start=2):
        if a == b:
            gleich += 1
            continue
        fa, fb = a.split(","), b.split(",")
        if fa[1] != fb[1] or fa[7] != fb[7] or any((x == "-") != (y == "-") for x, y in zip(fa[2:7], fb[2:7])):
            raise ValueError(f"{pfad.stem}.vorhersage.csv, Zeile {nummer}: weicht von selbstvorhersage.py ab "
                             f"({a} statt {b}).")
        abstand = max(abs(int(x) - int(y)) for x, y in zip(fa[2:7], fb[2:7]) if x != "-")
        if abstand > VORHERSAGE_TOLERANZ_MG:
            raise ValueError(f"{pfad.stem}.vorhersage.csv, Zeile {nummer}: weicht um {abstand} mg von "
                             f"selbstvorhersage.py ab ({a} statt {b}).")
        groesste = max(groesste, abstand)
    strecken = selbstvorhersage.ereignisse([z.endswith(",1") for z in soll])
    return len(soll), gleich, groesste, strecken


def nebendatei(pfad, endung, kopf):
    """Die Zeilen einer Nebendatei so, wie das Gerät sie gesendet hat, ohne Kopf. Fehlt sie, keine."""
    datei = pfad.with_name(pfad.stem + endung)
    if not datei.exists():
        return []
    praefix = next(p for p, e, _, _ in NEBENZEILEN if e == endung).decode("ascii")
    with datei.open(encoding="utf-8", newline="") as d:
        zeilen = csv.reader(d, strict=True)
        if next(zeilen, None) != list(kopf):
            raise ValueError(f"Kopf von {datei.name} ist ungültig.")
        return [praefix + ",".join(z) for z in zeilen]


def erkundung_pruefen(pfad, meta, werte):
    """Jede Pin- und Versuchszeile des Geräts mit selbsterkundung.py nachrechnen, aus den Temperaturen der
    Körperzeilen. Die Zeilen des letzten Takts darf die Aufnahme verpasst haben: Sie endet mit seiner
    Körperzeile. Gibt die nachgerechneten Zeilen je Art zurück, ohne Erkundung None."""
    geraet = {e: nebendatei(pfad, e, k) for e, k in ((".pin.csv", PIN_KOPF), (".versuch.csv", VERSUCH_KOPF))}
    e = meta.get("erkundung")
    if e is None:
        if any(geraet.values()):
            raise ValueError("Pin- oder Versuchszeilen, aber keine Erkundung in der JSON.")
        return None
    klassen = {int(p): k for p, k in e["pins"].items()}
    knoten = selbsterkundung.Erkundung(selbsterkundung.kandidaten(klassen), *(e[f] for f in ERKUNDUNG_FELDER),
                                       warm=meta["grenzen"]["temp_schwach"])
    soll = {".pin.csv": [], ".versuch.csv": []}
    for w in werte:
        for z in knoten.takt(w["takt"], w["temp_dc"]):
            soll[".pin.csv" if z.startswith("PIN,") else ".versuch.csv"].append(z)
    letzter = werte[-1]["takt"] if werte else 0
    for endung, zeilen in soll.items():
        da = geraet[endung]
        if da != zeilen[:len(da)] or any(int(z.split(",")[1]) != letzter for z in zeilen[len(da):]):
            erste = next((i for i, (a, b) in enumerate(zip(da, zeilen)) if a != b), min(len(da), len(zeilen)))
            raise ValueError(f"{pfad.stem}{endung}, Zeile {erste + 2}: weicht von selbsterkundung.py ab "
                             f"(Gerät {da[erste] if erste < len(da) else 'nichts'!r}, "
                             f"Python {zeilen[erste] if erste < len(zeilen) else 'nichts'!r}).")
    return soll


def erkundung_bericht(meta, soll):
    """Kurz, was die Erkundung gefunden hat, aus den geprüften Zeilen."""
    if soll is None:
        return ""
    versuche = [z.split(",") for z in soll[".versuch.csv"]]
    schalten = [z.split(",") for z in soll[".pin.csv"]]
    klassen = meta["erkundung"]["pins"]
    teile = [f"Erkundung: {len(selbsterkundung.kandidaten({int(p): k for p, k in klassen.items()}))} Kandidaten "
             f"({', '.join(f'{p}{k}' for p, k in klassen.items() if k in selbsterkundung.KANDIDATEN)}), "
             f"{len(versuche)} Versuche."]
    erste = {}
    for v in versuche:
        if v[10] == "KUEHLT":
            erste.setdefault(v[2], v[1])
    for pin, takt in erste.items():
        letzte = [v for v in versuche if v[2] == pin][-1]
        teile.append(f"Pin {pin} kühlt ab Takt {takt}, zuletzt {letzte[10]}, Wirkung im Mittel "
                     f"{int(letzte[7]) / 100:+.2f} °C über {letzte[9]} Versuche.")
    if not erste:
        teile.append("Kein Pin kühlt.")
    einsaetze = sum(1 for z in schalten if z[4] == "EINSATZ" and z[3] == "1")
    teile.append(f"Eingeschaltet zum Kühlen: {einsaetze} Mal.")
    return "\n".join(teile)


def tausender(zahl):
    return f"{zahl:,.0f}".replace(",", ".")


def grad(zehntel):
    return f"{zehntel / 10:.1f}".replace(".", ",")


def bericht(meta, werte):
    temps = [w["temp_dc"] for w in werte if w["temp_dc"] is not None]
    heaps = [w["heap"] for w in werte]
    luecken = [w["luecke_us"] for w in werte]
    blick = f", Blick {meta['blick']} Takte" if meta.get("blick", 1) > 1 else ""
    zeilen = [f"{len(werte)} Takte à {meta['intervall_ms']} ms, Regel {meta['regel']}{blick}, Beginn {meta['beginn']}."]
    if meta.get("fortsetzung") and werte:
        zeilen.append(f"Setzt {meta['fortsetzung']} fort, mit dem Stand nach Takt {werte[0]['takt'] - 2}.")
    if meta.get("sichern_alle"):
        zeilen.append(f"Das Gerät sicherte jeden {meta['sichern_alle']}. Takt und am Ende.")
    if temps:
        zeilen.append(f"Chiptemperatur {grad(min(temps))} bis {grad(max(temps))} °C, "
                      f"Median {grad(statistics.median(temps))} °C"
                      + (f", {len(werte) - len(temps)} Takte ohne Messwert." if len(temps) < len(werte) else "."))
    if heaps:
        zeilen.append(f"Freier Speicher {tausender(min(heaps))} bis {tausender(max(heaps))} Byte.")
        zeilen.append(f"Schleifenlücke Median {tausender(statistics.median(luecken))} µs, "
                      f"größte {tausender(max(luecken))} µs.")
    if any(w["reiz"] for w in werte):
        for name, teil in (("Unter Last", [w for w in werte if w["reiz"] & LAST]),
                           ("Mit Leck", [w for w in werte if w["reiz"] & LECK]),
                           ("Mit Bremse", [w for w in werte if w["reiz"] & BREMSE]),
                           ("In Ruhe", [w for w in werte if not w["reiz"]])):
            t = [w["temp_dc"] for w in teil if w["temp_dc"] is not None]
            if not teil:
                continue
            zeilen.append(f"{name} ({len(teil)} Takte): "
                          + (f"Temperatur Median {grad(statistics.median(t))} °C, höchstens {grad(max(t))} °C, "
                             if t else "")
                          + f"Speicher ab {tausender(min(w['heap'] for w in teil))} Byte, Lücke Median "
                          f"{tausender(statistics.median(w['luecke_us'] for w in teil))} µs, größte "
                          f"{tausender(max(w['luecke_us'] for w in teil))} µs.")
    zustaende = {z: sum(w["zustand"] == z for w in werte) for z in ZUSTAENDE}
    zeilen.append("Zustände: " + ", ".join(f"{z} {n}" for z, n in zustaende.items())
                  + f". Vorwarnungen: {sum(w['vorwarnung'] for w in werte)}.")
    return "\n".join(zeilen)


def abbrechen(signum, frame):
    # SIGTERM wie Strg-C behandeln, damit STOP gesendet und die Datei geschlossen wird.
    raise KeyboardInterrupt


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="aktion", required=True)
    a = sub.add_parser("aufnahme", help="Körpermodus starten und mitschreiben, Strg-C oder SIGTERM beendet")
    a.add_argument("datei", type=Path)
    a.add_argument("--port", required=True)
    a.add_argument("--regel", choices=list(REGELN), default="erbe")
    a.add_argument("--intervall-ms", type=int, default=1000)
    a.add_argument("--takte", type=int, help="Ohne Angabe bis zum Abbruch")
    a.add_argument("--grenzen", type=int, nargs=6, metavar="N", help="Temperatur schwach ausfall (Zehntelgrad), "
                   "Speicher schwach ausfall (Byte), Lücke schwach ausfall (µs)")
    a.add_argument("--last", type=int, nargs="+", metavar="N",
                   help="Last AN AUS [SAAT]: Kern 0 arbeitet AN s, ruht AUS s. Mit SAAT dauert jede Phase "
                        "zufällig lang, von einem Viertel bis zum vollen Wert")
    a.add_argument("--blick", type=int, default=1, help=f"Takte, die die Vorwarnung vorausdenkt, 1 bis {MAX_BLICK}")
    a.add_argument("--leck", type=int, nargs="+", metavar="N",
                   help="Speicherleck BYTE BODEN HALTEN PAUSE [FLACH MUSTER]: BYTE je Takt, bis nur noch BODEN Byte "
                        "frei sind, HALTEN Takte am Boden, dann PAUSE Takte frei. Durchgänge, deren Bit im MUSTER "
                        "gesetzt ist, halten schon bei FLACH Byte an")
    a.add_argument("--bremse", type=int, nargs=5, metavar=("START", "SCHRITT", "BIS", "HALTEN", "PAUSE"),
                   help="Hauptschleife steht je Takt START, START+SCHRITT … bis BIS ms still, HALTEN Takte bei BIS, "
                        "dann PAUSE Takte nicht")
    a.add_argument("--fortsetzen", type=Path, metavar="VORIGE",
                   help="Mit dem gesicherten Stand weiterlernen, den die vorige Aufnahme im selben Ordner hinterließ")
    a.add_argument("--sichern-alle", type=int, default=0, metavar="N",
                   help="Das Gerät sichert jeden N-ten Takt und am Ende, damit eine spätere Aufnahme fortsetzen kann")
    a.add_argument("--mqtt", metavar="HOST",
                   help="Zustand und Vorwarnung per MQTT an diesen Broker melden, Thema oscan/warnung")
    a.add_argument("--erkundung", type=int, nargs=7,
                   metavar=("RUHE", "AN", "MITTEL", "SCHWELLE", "FENSTER", "PRUEFE", "SAAT"),
                   help="Selbsterkundung: freie Pins passiv prüfen, dann je Versuch RUHE Takte unverändert und AN "
                        "Takte mit einem umgeschalteten Pin, verglichen über je die letzten MITTEL Takte. Ein Pin "
                        "kühlt, wenn er über seine letzten FENSTER Versuche sicher um mehr als SCHWELLE Zehntelgrad "
                        "kühlt. Mit Kühler regelt der Knoten selbst und prüft nach je PRUEFE Takten nach. SAAT "
                        "bestimmt die zufällige Reihenfolge")
    a.add_argument("--empfinden", action="store_true", help="Beide Empfindungsschichten samt Selbstvorhersage aufzeichnen")
    a.add_argument("--vorhersage", action="store_true",
                   help="Selbstvorhersage: Der Knoten sagt seine Temperatur 10 und 60 Takte voraus, lernt dabei und "
                        "meldet, wenn er sich verschätzt. Beginnt bei null")
    k = sub.add_parser("pruefen", help="Einstufungen und Entscheidungen nachrechnen")
    k.add_argument("datei", type=Path)
    q = sub.add_parser("pins", help="Nachsehen, was an den erlaubten Pins hängt, ohne einen zu treiben")
    q.add_argument("--port", required=True)
    q.add_argument("--regel", choices=list(REGELN), default="startwert",
                   help="Lernregel der Firmware, nur für den Handschlag")
    s = sub.add_parser("spur", help="takt,zustand für versuch.py, wahlweise neu eingestuft")
    s.add_argument("datei", type=Path)
    s.add_argument("--grenzen", type=int, nargs=6, metavar="N")
    arg = p.parse_args()
    try:
        if arg.aktion == "aufnahme":
            try:
                import serial
            except ImportError:
                p.exit(2, "Für eine Aufnahme wird pyserial benötigt (in PlatformIO enthalten).\n")
            signal.signal(signal.SIGTERM, abbrechen)
            grenzen = Grenzen(*arg.grenzen) if arg.grenzen else ERKUNDUNG
            melder = None
            if arg.mqtt:
                from melder import Melder, sender
                melder = Melder(sender(arg.mqtt))
            with serial.Serial(arg.port, 115200, timeout=0.6, write_timeout=2) as port:
                exklusiv(port)
                anzahl = aufnehmen(port, arg.regel, grenzen, arg.intervall_ms, arg.takte, arg.datei,
                                   tuple(arg.last) if arg.last else None, arg.blick,
                                   tuple(arg.leck) if arg.leck else None, tuple(arg.bremse) if arg.bremse else None,
                                   arg.fortsetzen, arg.sichern_alle, melder,
                                   tuple(arg.erkundung) if arg.erkundung else None, arg.vorhersage, arg.empfinden)
            print(f"{anzahl} Takte aufgezeichnet in {arg.datei}.")
        elif arg.aktion == "pruefen":
            meta, werte = pruefen(arg.datei)
            print(bericht(meta, werte))
            print(f"Alle {len(werte)} Einstufungen und Entscheidungen des Geräts stimmen mit Python überein.")
            soll = erkundung_pruefen(arg.datei, meta, werte)
            if soll is not None:
                print(erkundung_bericht(meta, soll))
                print("Alle Pin- und Versuchszeilen stimmen mit selbsterkundung.py überein.")
            e = empfinden_pruefen(arg.datei, meta, werte)
            if e is not None:
                print(f"Empfinden: alle {e} Zeilen exakt gleich wie die Referenz.")
            v = vorhersage_pruefen(arg.datei, meta, werte)
            if v is not None:
                zeilen, gleich, groesste, strecken = v
                print(f"Vorhersage: {zeilen} Zeilen, {gleich} gleich wie selbstvorhersage.py, größte Abweichung "
                      f"{groesste} mg (erlaubt {VORHERSAGE_TOLERANZ_MG}). Überrascht in {len(strecken)} Strecken"
                      + (": " + ", ".join(f"Takt {b} ({l})" for b, l in strecken[:20]) if strecken else "") + ".")
        elif arg.aktion == "pins":
            try:
                import serial
            except ImportError:
                p.exit(2, "Dafür wird pyserial benötigt (in PlatformIO enthalten).\n")
            with serial.Serial(arg.port, 115200, timeout=0.6, write_timeout=2) as port:
                exklusiv(port)
                klassen = pins_lesen(port, arg.regel)
            namen = {"F": "frei", "M": "gegen Masse", "P": "gegen Plus", "U": "verkehrt"}
            for klasse, name in namen.items():
                print(f"{name}: {' '.join(str(p) for p, k in klassen.items() if k == klasse) or '-'}")
        else:
            meta, werte = lies_aufnahme(arg.datei)
            g = Grenzen(*arg.grenzen) if arg.grenzen else Grenzen(**meta["grenzen"])
            w = csv.writer(sys.stdout, lineterminator="\n")
            w.writerow(("takt", "zustand"))
            w.writerows(neu_einstufen(werte, g))
    except (OSError, ValueError, KeyError, TypeError, csv.Error) as fehler:
        p.exit(2, f"Körpersignale: {fehler}\n")


if __name__ == "__main__":
    main()
