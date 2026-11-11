"""Zusaetzliche B-Speicherpruefung NACH Freeze/Kontrolllauf.

Aendert kein Verfahren und erzeugt keine Entwicklungs- oder Pruefziehung.
Zaehlt reale Zustandsfelder und prueft den Serializer unabhaengig. Dies ist
keine Isolation beliebigen Python-Codes, sondern ein geschlossener Feldvertrag
fuer die eingefrorenen Modellklassen.
"""
import argparse
import hashlib
from collections import deque
import json
from pathlib import Path
import ideenlabor_b as b
from ideenlabor_basis import fordere, Prueffehler, quellhashes

FELDER={"methode","variant","runde","letzter","wahl","fenster","globaldaten","fehler","offen","arbeit"}
RINGFELDER={"daten","n","pos","s"}
ARBEIT=("ausgangslesungen","fenster_updates","neben_und_hauptprognosen")
TEILE=("ungeteilt","x","z","xz")


def ganz(wert,lo,hi): return type(wert) is int and lo<=wert<=hi


def zustand_pruefen(modell):
    fordere(set(vars(modell))==FELDER,"Unbekannte Modellfelder oder versteckter Cache")
    fordere(modell.methode in b.METHODEN and modell.variant in b.VARIANTEN,"Unbekanntes Modell")
    fordere(ganz(modell.runde,0,768) and ganz(modell.letzter,0,1),"Ungueltiger Rundenzustand")
    if modell.methode=="kandidat":
        if modell.runde<256:
            fordere(modell.wahl is None,"Vorzeitige Auswahl"); aktiv=TEILE[:3]
        else:
            fordere(modell.wahl in TEILE[:3],"Ungueltige Auswahl"); aktiv=(modell.wahl,)
    else:
        aktiv=(modell.methode,) if modell.methode in TEILE else ()
        fordere(modell.wahl==(modell.methode if aktiv else None),"Feste Methode wechselte Struktur")
    fordere(type(modell.fenster) is dict and set(modell.fenster)==set(aktiv),"Nicht bilanzierte Suchfenster")
    fordere(set(modell.fehler)==set(TEILE[:3]) and all(ganz(v,0,128) for v in modell.fehler.values()),"Ungueltige Auswahlzaehler")
    fordere(set(modell.arbeit)==set(ARBEIT) and all(ganz(v,0,2**32-1) for v in modell.arbeit.values()),"Nicht bilanzierte Arbeitszaehler")
    fordere(type(modell.globaldaten) is deque and modell.globaldaten.maxlen==128,"Unbegrenzter globaler Puffer")
    if modell.offen is None: pending=(0,0,0,0,0,0)
    else:
        fordere(type(modell.offen) is tuple and len(modell.offen)==3,"Nicht bilanzierter Pending-Zustand")
        x,z,vorhersagen=modell.offen
        fordere(ganz(x,0,1) and ganz(z,0,1) and type(vorhersagen) is dict and
                set(vorhersagen)==set(aktiv) and all(ganz(v,0,1) for v in vorhersagen.values()),"Unbekannte Pending-Felder")
        pending=(1,x,z,*(vorhersagen.get(p,0) for p in TEILE[:3]))
    kopf=bytes((1,b.VARIANTEN.index(modell.variant),b.METHODEN.index(modell.methode),
                255 if modell.wahl is None else TEILE.index(modell.wahl)))
    kopf+=modell.runde.to_bytes(2,"little")
    kopf+=b"".join(modell.fehler[p].to_bytes(2,"little") for p in TEILE[:3])
    kopf+=bytes((modell.letzter,))+bytes(pending)+bytes(1)
    kopf+=b"".join(modell.arbeit[k].to_bytes(4,"little") for k in ARBEIT)
    fordere(len(kopf)==32,"Metadatenbilanz inkonsistent")
    payload=bytearray()
    for teil in TEILE:
        if teil not in modell.fenster: continue
        rings=modell.fenster[teil]
        fordere(type(rings) is list and len(rings)=={"ungeteilt":1,"x":2,"z":2,"xz":4}[teil],"Ungueltige Blattanzahl")
        for ring in rings:
            if modell.variant=="global128":
                fordere(ring is None,"Versteckter zusaetzlicher Blattpuffer")
                continue
            fordere(set(vars(ring))==RINGFELDER,"Versteckter Cache im Blatt")
            fordere(type(ring.daten) is bytearray and len(ring.daten)==32 and all(v in (0,1) for v in ring.daten),"Blattpuffer ungueltig")
            fordere(ganz(ring.n,0,32) and ganz(ring.pos,0,31) and ganz(ring.s,0,32),"Blattverwaltung ungueltig")
            if ring.n<32:
                fordere(ring.pos==ring.n and all(v==0 for v in ring.daten[ring.n:]),"Nichtkanonischer Teilpuffer")
            start=ring.pos if ring.n==32 else 0
            fordere(sum(ring.daten[(start+i)%32] for i in range(ring.n))==ring.s,"Falsche gespeicherte Einsenzahl")
            payload.extend(ring.daten); payload.extend((ring.n,ring.pos,ring.s))
    if modell.variant=="global128" and aktiv:
        fordere(len(modell.globaldaten)==min(modell.runde,128),"Globales Zeitfenster unvollstaendig")
        for zeile in modell.globaldaten:
            fordere(type(zeile) is tuple and len(zeile)==3 and all(ganz(v,0,1) for v in zeile),"Versteckte Felder im globalen Puffer")
        daten=bytes(x+2*z+4*y for x,z,y in modell.globaldaten)
        payload=bytearray(bytes((len(daten),))+daten+bytes(128-len(daten)))
    else: fordere(len(modell.globaldaten)==0,"Unbilanziertes globales Archiv")
    # Die feste xz-Nebenprognose hat kein eigenes Headerbit: Sie ist aus
    # Fenster und pending x/z eindeutig wiederherstellbar. Diese Redundanz
    # wird geprueft, statt einen beliebigen ausgelassenen Wert zu erlauben.
    if modell.offen is not None:
        x,z,vorhersagen=modell.offen
        for teil in aktiv:
            def index(xx,zz):
                return 0 if teil=="ungeteilt" else xx if teil=="x" else zz if teil=="z" else 2*xx+zz
            if modell.variant=="global128":
                ys=[y for xx,zz,y in modell.globaldaten if index(xx,zz)==index(x,z)]
                n,ones=len(ys),sum(ys)
            else:
                ring=modell.fenster[teil][index(x,z)]; n,ones=ring.n,ring.s
            fordere(vorhersagen[teil]==int(2*ones>=n),"Pending-Prognose ist nicht aus dem Bild rekonstruierbar")
    erwartet=kopf+bytes(payload)
    tatsaechlich=modell.bild()
    fordere(type(tatsaechlich) is bytes and tatsaechlich==erwartet,"Serializer laesst realen Zustand aus oder veraendert ihn")
    fordere(set(vars(modell))==FELDER and len(erwartet)<=512,"Zustandsbudget oder Feldvertrag verletzt")
    return len(erwartet)


def handfolgen():
    anzahl=0
    for variant in b.VARIANTEN:
        for methode in b.METHODEN:
            for signal in ("x","z","wechselnd"):
                modell=b.Modell(methode,variant)
                for i in range(768):
                    x=i%2; z=(i//2)%2
                    modell.prognose({"wort":"KNAPP","x":x,"z":z})
                    zustand_pruefen(modell); anzahl+=1
                    modell.lernen(x if signal=="x" else z if signal=="z" else (i//4)%2)
                    zustand_pruefen(modell); anzahl+=1
    return anzahl


def erwartete_groessen(methode,variant,wahl):
    if methode in ("immer_1","immer_0","letzter"): return 32,32,32
    if variant=="global128": return 161,161,161
    if methode=="kandidat":
        fordere(wahl in TEILE[:3],"Ungueltige publizierte Teilung")
        ende=67 if wahl=="ungeteilt" else 102
        return 207,ende,ende
    n={"ungeteilt":67,"x":102,"z":102,"xz":172}[methode]
    return n,n,n


def rohzeilen_pruefen(zeilen):
    for r in zeilen:
        fordere(r["methode"] in b.METHODEN and r["variante"] in b.VARIANTEN,"Unbekannte Rohzeile")
        soll=erwartete_groessen(r["methode"],r["variante"],r["wahl"])
        ist=tuple(r[k] for k in ("spitze_bytes","nach_auswahl_bytes","ende_bytes"))
        fordere(ist==soll,"Publizierte Speicherbilanz widerspricht realen Pufferformaten")
    return len(zeilen)


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rohwerte",type=Path)
    parser.add_argument("--ausgabe",type=Path,default=Path("IDEEN-SPEICHERPRUEFUNG.json"))
    args=parser.parse_args(argv)
    try:
        fordere(not args.ausgabe.exists(),"Ausgabe existiert bereits")
        daten=json.loads(args.rohwerte.read_text(encoding="utf-8"))
        fordere(daten["quellhashes"]==quellhashes(),"Eingefrorene Quellen wurden veraendert")
        anzahl=handfolgen(); roh=rohzeilen_pruefen(daten["B"]["laeufe"])
        ergebnis={"phase":"zusaetzliche_Prueferabsicherung_nach_Kontrolllauf",
                  "freeze_commit":daten["freeze_commit"],"quellhashes":daten["quellhashes"],
                  "zustandspruefungen_handfolgen":anzahl,"gepruefte_rohzeilen":roh,
                  "neue_kontrollziehungen":0,"kandidaten_geaendert":False,
                  "urspruenglicher_pruefer_erkannte_gekuerzten_serializer":False,
                  "unabhaengige_pruefung_bestanden":True,
                  "nachpruefer_hashes":{name:hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
                      for name in ("ideenlabor_speicherpruefung.py","test_ideenlabor_speicherpruefung.py")}}
        with args.ausgabe.open("x",encoding="utf-8") as out: out.write(json.dumps(ergebnis,ensure_ascii=False,indent=2)+"\n")
        print(json.dumps({k:v for k,v in ergebnis.items() if k!="quellhashes"},ensure_ascii=False))
    except (Prueffehler,OSError,KeyError,ValueError) as error:
        parser.exit(2,"Speicherpruefung abgebrochen: "+(str(error) if isinstance(error,Prueffehler) else "Eingabe oder Ausgabe ungueltig")+"\n")

if __name__=="__main__": main()
