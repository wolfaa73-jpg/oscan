#!/usr/bin/env python3
"""Getrenntes Ideenlabor A/B/C. Pruefsatz nur aus identischem Freeze-Commit."""
import argparse
import os
import json
from pathlib import Path
import time
import unittest
from ideenlabor_basis import NAMENSRAUM, Prueffehler, fordere, quellhashes, pruefung_freigeben
import ideenlabor_a as a
import ideenlabor_b as b
import ideenlabor_c as c

TESTMODULE=("test_ideenlabor_pruefer","test_ideenlabor","test_ideenlabor_c")


def selbsttest():
    tests=unittest.defaultTestLoader.loadTestsFromNames(TESTMODULE)
    ergebnis=unittest.TextTestRunner(verbosity=1).run(tests)
    fordere(ergebnis.wasSuccessful(),"Defekt- und Funktionspruefung gescheitert")
    return ergebnis.testsRun


def ausfuehren(satz,freeze=None):
    tests=selbsttest(); hashes=quellhashes()
    if satz=="pruefung": pruefung_freigeben(freeze)
    start=time.perf_counter()
    ergebnis={"schema":1,"planfassung":"0.3","namensraum":NAMENSRAUM,"satz":satz,
              "freeze_commit":freeze if satz=="pruefung" else None,"quellhashes":hashes,
              "tests":tests,"pruefaufnahme_verwendet":False,"kern_importiert":False,
              "b_seeds":list(range(20 if satz=="entwicklung" else 200)),
              "c_seeds":list(range(3 if satz=="entwicklung" else 4))}
    ergebnis["A"]=a.auswerten()
    ergebnis["B"]=b.auswerten(satz,ergebnis["b_seeds"])
    ergebnis["C"]=c.auswerten(satz,ergebnis["c_seeds"])
    ergebnis["laufzeit_sekunden"]=round(time.perf_counter()-start,3)
    fordere(quellhashes()==hashes,"Quellstand hat sich waehrend des Laufs geaendert")
    return ergebnis


def mittel(werte): return sum(werte)/len(werte)


def bericht(daten,dateiname):
    pruefung=daten["satz"]=="pruefung"
    zeilen=["# Ideenlabor A, B und C – Ergebnisse", "",
            "Durchgeführt mit neuen künstlichen Miniwelten; ohne laufenden Kern, Firmware oder Geräteaufnahmen.", "",
            "**"+("Prüfsatz nach Freeze" if pruefung else "Entwicklungsstand – noch keine unabhängige Prüfung")+".**", "",
            "Namensraum: `"+NAMENSRAUM+"`. Planfassung 0.3. "+str(daten["tests"])+" Defekt-/Funktionsprüfungen bestanden.",
            "Freeze-Commit: `"+str(daten["freeze_commit"] or "noch nicht gesetzt; Prüfziehungen gesperrt")+"`.",
            "Rohzähler, einzelne Seeds, Fragearten, Fristenfenster und Ressourcen: [JSON]("+dateiname+").", "",
            "## A: getrennte Handlungsfolgen", "",
            "Die Sollrechnung wurde ausgeführt. A=1 bezeichnet Entlasten, nicht die nachgewiesene Rettung eines Auftrags.",
            "Die gemeinsame Beobachtung A=1/Y=0 wird neutral als Handlung ohne anschließenden Ausfall gezählt. Weil die Handlung den Ausgang verändert, belegt dieser Quotient weder Warnpräzision noch Rettung.", "",
            "| Verfahren | 32 Bewertung: Kosten | 16+32 Aufgaben: Kosten | 16+8 Aufgaben: Kosten |", "|---|---:|---:|---:|"]
    labels={"vier_beobachtungen":"Vier Beobachtungen je Zelle","eine_beobachtung":"Eine Beobachtung je Zelle",
            "nie_entlasten":"Nie entlasten","immer_entlasten":"Immer entlasten (Immer warnen)","bei_vorzeichen":"Bei Vorzeichen"}
    for m in a.METHODEN:
        gross=[r for r in daten["A"]["laeufe"] if r["methode"]==m and not r["stoerung"] and r["bewertung_runden"]==32]
        kurz=[r for r in daten["A"]["laeufe"] if r["methode"]==m and not r["stoerung"] and r["bewertung_runden"]==8]
        zeilen.append(f"| {labels[m]} | {sum(r['bewertung']['kosten'] for r in gross)} | {sum(r['gesamt']['kosten'] for r in gross)} | {sum(r['gesamt']['kosten'] for r in kurz)} |")
    zeilen += ["", "Summen über die vier vorab gleich gewichteten Welten, jeweils dieselbe Aufgabenanzahl pro Verfahren. Der einfachere adaptive Gegner ist günstiger; der Vierfach-Kandidat verdient gegenüber ihm seine Zusatzkosten nicht.",
               "A1 bestätigt identische Zustände bei identischer sichtbarer Geschichte; A2 und die getrennte Störfolge sind vollständig im JSON enthalten.", "",
               "## B: einmalige Wortwahl", "",
               "Alle Fehler zählen. Die Tabellen zeigen mittlere Verluste je Takt; 257–768 ist das vorab festgelegte Bewertungsfenster. Beide Fensterarten werden vollständig ausgewiesen."]
    blabel={m:m for m in b.METHODEN}; blabel.update({"immer_1":"Immer warnen","immer_0":"Nie warnen","letzter":"Letzter Ausgang"})
    for v in b.VARIANTEN:
        zeilen += ["", "### "+v, "", "| Verfahren | S: alle / Bewertung | N: alle / Bewertung | R: alle / Bewertung | Spitze Bytes | Nach Auswahl Bytes |", "|---|---:|---:|---:|---:|---:|"]
        for m in b.METHODEN:
            rows=[r for r in daten["B"]["laeufe"] if r["methode"]==m and r["variante"]==v]
            spalten=[]
            for w in ("S","N","R"):
                gruppe=[r for r in rows if r["welt"]==w]
                spalten.append(f"{mittel([r['gesamt']['fehler']/768 for r in gruppe]):.4f} / {mittel([r['bewertung']['fehler']/512 for r in gruppe]):.4f}")
            zeilen.append("| "+blabel[m]+" | "+" | ".join(spalten)+f" | {max(r['spitze_bytes'] for r in rows)} | {max(r['nach_auswahl_bytes'] for r in rows)} |")
        for w in ("S","N","R"):
            zeilen += ["", "Bewertungsfenster 257–768, Welt "+w+": 512 Takte je Spur; Quotienten aus summierten Rohzählern.", "",
                       "| Verfahren | Takte | Warnungen | Fehlalarme | Verpasst | Warnanteil | Trefferquote | Grundrate |",
                       "|---|---:|---:|---:|---:|---:|---:|---:|"]
            for m in b.METHODEN:
                gruppe=[r["bewertung"] for r in daten["B"]["laeufe"] if r["variante"]==v and r["welt"]==w and r["methode"]==m]
                total=sum(r["takte"] for r in gruppe); warn=sum(r["warnungen"] for r in gruppe)
                falsch=sum(r["fehlalarme"] for r in gruppe); verpasst=sum(r["verpasst"] for r in gruppe)
                treffer=warn-falsch; precision=f"{treffer/warn:.4f}" if warn else "NA"
                zeilen.append(f"| {blabel[m]} | {total} | {warn} | {falsch} | {verpasst} | {warn/total:.4f} | {precision} | {(treffer+verpasst)/total:.4f} |")
        k=next(k for k in daten["B"]["kriterien"] if k["variante"]==v)
        zeilen += ["", f"S: relevante Teilung {k['s_relevant']}/{k['folgen']}; Verlustdifferenz gegen ungeteilt {k['s_verlustdifferenz']:.6f}. N: {k['n_geteilt']}/{k['folgen']} Teilungen. R: mittlere Restdifferenz gegen Vierertabelle {k['r_restdifferenz']:.6f}."]
        if pruefung: zeilen.append(f"Vorab-Hürden: S {'bestanden' if k['s_bestanden'] else 'nicht bestanden'}, N {'bestanden' if k['n_bestanden'] else 'nicht bestanden'}, R {'bestanden' if k['r_bestanden'] else 'nicht bestanden'}.")
        else: zeilen.append("Die 200-Folgen-Abnahme wird auf diesem Entwicklungssatz nicht vorgenommen.")
    zeilen += ["", "Die Zustandsbytes enthalten auch Suchmodelle, Auswahlfehler, laufende Rundenzähler und die ausgewiesenen Arbeitszähler. Blattfenster werden nach Auswahl freigegeben. Arbeitszähler im JSON unterscheiden Ergebnislesungen, Fensterupdates und Haupt-/Nebenprognosen. Geringerer laufender Zustand ist kein Nachweis geringerer Spitze oder Energie.", "",
               "## C: Darstellung, Herkunft und Widerruf", "",
               "Verlust: richtig 0, falsch 4, unbekannt 1. Nenner sind die tatsächlich gestellten Fragen, nicht die 256 Beobachtungstakte; diese Tabellen sind keine Warnquoten je Gerätetakt. Zuerst Fragen innerhalb einer Kategorie, dann Prüfpunkte und Kategorien, danach Seeds und Familien gleich gewichtet. Der Widerruf ist eine eigene Kategorie. Nutzenentscheidungen verwenden exakte Brüche.", "",
               "Die Tabelle wird für jedes Budget getrennt ausgewertet."]
    for budget in (32,64,128):
        zeilen += ["", "### Budget "+str(budget)+" Byte", "", "| Budget | Verfahren | Wiederholung | Wechsel | Unregelmäßig | Gleichgewichteter Verlust | Bildspitze Bytes |", "|---:|---|---:|---:|---:|---:|---:|"]
        k=next(k for k in daten["C"]["kriterien"] if k["budget"]==budget)
        for m in c.METHODEN:
            rows=[r for r in daten["C"]["laeufe"] if r["budget"]==budget and r["methode"]==m]
            fam=[mittel([r["gesamtverlust"] for r in rows if r["familie"]==f]) for f in c.FAMILIEN]
            label="Immer warnen (zusätzliche Referenz)" if m=="immer_1" else m
            zeilen.append(f"| {budget} | {label} | "+" | ".join(f"{v:.6f}" for v in fam)+f" | {k['mittel'][m]:.6f} | {max(r['spitze_abbild_bytes'] for r in rows)} |")
        zeilen += ["", f"Budget {budget}: {'kleinerer' if k['nutzen'] else 'kein strikt kleinerer'} Gesamtverlust als alle fünf vorab benannten Pflichtgegner"+(" im Prüfsatz." if pruefung else " im Entwicklungssatz; kein unabhängiger Nutzennachweis."), ""]
    zeilen += ["Die zusätzliche Immer-warnen-Referenz ändert die fünf ursprünglichen Pflichtgegner nicht. Ausnahmeabnahme bei 64/128 Byte und Widerruf werden als harte Bedingungen geprüft. Ein korrekt beantworteter, aber im Bild nicht mehr belegbarer historischer Wert gilt als verbotener Cache-Zugriff.", "",
               "Die logischen C-Arbeitsraumgrenzen sind konservative Pufferbilanzen: Regelkandidat 480 Byte, Ring 448 Byte, andere Verfahren 144 Byte. Sie umfassen Eingabeblock, gepacktes Suffix, Kodierausgabe, Suchtemporäre und eine ausdrücklich angenommene 32-Byte-Verwaltung. Konservativer Regel-Join: 32 Eingabe + 128 gepacktes Suffix + höchstens 120 Abschnittsbytes + 128 neues Bild + 12 Header + 32 Verwaltung = 452 Byte. Die Regelsuche hält nur Parameter/Fehlerzahl und materialisiert erst den Gewinner. Ein entfernter Abschnitt wird sofort freigegeben. Beim Zählerausgabeaufbau fallen höchstens 32 + 16 + 8 + 16 + 24 + 32 = 128 Byte an; die angegebene Grenze 144 enthält Reserve. Für Abfragen liegen die konservativen Zusatzgrenzen bei 120 Bytes Ringslice + 32 Verwaltung = 152 beziehungsweise 32 Rohabschnitt + 26 Ausnahmekopie + 32 Verwaltung = 90 beim Regeldecoder; der alte persistente Zustand zählt separat zum Abbildbudget. Sie sind **keine Messung des Python-RAMs**; Python-Objektoverhead und Interpreter werden nicht als Geräte-RAM ausgegeben. Kodiervergleiche, Zählerupdates und tatsächlich dekodierte Ereignisse bei Abfragen stehen getrennt im JSON.", "",
               "## Grenzen und Reproduktion", "",
               "Der Katalog in C ist von Hand passend zur Modellfrage vorgegeben. B untersucht Merkmalsauswahl und festgelegte Fenster, kein frei wachsendes Wörterbuch. A besitzt weder Messrauschen noch lang wirkende Aktionen. Ein bestandenes Ergebnis belegt keinen Nutzen am Gerät.",
               "Die Prüfer testen Daten- und Zustandsverträge, keine Sicherheitsisolation beliebigen Python-Codes. Historische Antworten werden sowohl gegen die Wahrheit als auch gegen die im Bild tatsächlich vorhandenen Belege geprüft.", "",
               "```sh", "python3 -B -m unittest -v test_ideenlabor_pruefer test_ideenlabor test_ideenlabor_c",
               "python3 -B ideenlabor.py --satz entwicklung --ausgabe IDEEN-ENTWICKLUNG.json",
               "# Erst nach identischem, committetem Quellstand:",
               "python3 -B ideenlabor.py --satz pruefung --freeze COMMIT_HASH --ausgabe IDEEN-PRUEFUNG.json", "```", "",
               "Vorhandene Rohwerte und Berichte werden vor Beginn abgewiesen und beim Schreiben exklusiv angelegt. Entwicklung verwendet standardmäßig IDEEN-ENTWICKLUNG.json und IDEEN-ENTWICKLUNG.md; die Prüfung IDEEN-PRUEFUNG.json und IDEEN-ERGEBNISSE.md. Für Wiederholungsläufe sind neue explizite Ausgabepfade erforderlich. Der vollständige 40-stellige Freeze-Hash muss alle Laborquellen, Tests und die Planfassung enthalten. Das Skript vergleicht jede Datei vor Kontrollziehungen und erneut nach dem Lauf. Die 24-Stunden-Aufnahme wird weder geöffnet noch benötigt."]
    return "\n".join(zeilen)+"\n"


def ausgabeziele(satz,roh=None,text=None):
    roh=Path(roh or ("IDEEN-ENTWICKLUNG.json" if satz=="entwicklung" else "IDEEN-PRUEFUNG.json")).resolve()
    text=Path(text or ("IDEEN-ENTWICKLUNG.md" if satz=="entwicklung" else "IDEEN-ERGEBNISSE.md")).resolve()
    fordere(roh!=text,"Rohwerte und Bericht brauchen verschiedene Ausgabepfade")
    return roh,text


def pruefe_ausgaben(ziele):
    for ziel in ziele:
        fordere(not ziel.exists() and not ziel.is_symlink(),"Ausgabe existiert bereits; kein Ueberschreiben")


def schreibe_ausgaben(daten,roh,text):
    erstellt=[]
    try:
        # Exklusives Anlegen schuetzt auch gegen eine zwischenzeitlich erstellte Datei.
        with roh.open("x",encoding="utf-8") as out:
            erstellt.append((roh,os.fstat(out.fileno()).st_ino))
            with text.open("x",encoding="utf-8") as md:
                erstellt.append((text,os.fstat(md.fileno()).st_ino))
                out.write(json.dumps(daten,ensure_ascii=False,indent=2)+"\n")
                md.write(bericht(daten,roh.name))
    except BaseException:
        # Nur selbst angelegte, identische Dateien aufraeumen; fremde Racer bleiben.
        for pfad,inode in erstellt:
            if pfad.exists() and pfad.stat().st_ino==inode: pfad.unlink()
        raise


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--satz",choices=("entwicklung","pruefung"),default="entwicklung")
    parser.add_argument("--freeze")
    parser.add_argument("--ausgabe")
    parser.add_argument("--bericht")
    args=parser.parse_args(argv)
    try:
        roh,text=ausgabeziele(args.satz,args.ausgabe,args.bericht)
        pruefe_ausgaben((roh,text))
        daten=ausfuehren(args.satz,args.freeze)
        schreibe_ausgaben(daten,roh,text)
        print(json.dumps({"satz":args.satz,"tests":daten["tests"],"freeze":daten["freeze_commit"],
                          "b_lauefe":len(daten["B"]["laeufe"]),"c_lauefe":len(daten["C"]["laeufe"]),
                          "sekunden":daten["laufzeit_sekunden"]},ensure_ascii=False))
    except (Prueffehler,OSError) as error:
        parser.exit(2,"Ideenlabor abgebrochen: "+(str(error) if isinstance(error,Prueffehler) else "Dateizugriff fehlgeschlagen; keine bestehende Ausgabe ueberschrieben")+"\n")

if __name__=="__main__": main()
