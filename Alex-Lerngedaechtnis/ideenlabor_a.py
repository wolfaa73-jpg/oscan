"""Plan A: feste kausale Schnittstelle, keine Abhaengigkeit vom OSCan-Kern."""
from ideenlabor_basis import fordere
from ideenlabor_pruefer import eingabe, a_beleg, a_vollstaendig

WELTEN = {"hilfreich": (1, 0), "unnoetig": (0, 0),
          "wirkungslos": (1, 1), "schaedlich": (0, 1)}
METHODEN = ("vier_beobachtungen", "eine_beobachtung", "nie_entlasten", "immer_entlasten", "bei_vorzeichen")

class Zaehler:
    def __init__(self):
        self.n = [[0, 0], [0, 0]]
        self.s = [[0, 0], [0, 0]]

    def sehen(self, x, a, y):
        self.n[x][a] += 1
        self.s[x][a] += y

    def handeln(self, daten, mindestanzahl):
        eingabe(daten, "A")
        x = daten["x"]
        if min(self.n[x]) < mindestanzahl:
            return x
        kosten = [a + 5*self.s[x][a]/self.n[x][a] for a in (0, 1)]
        return int(kosten[1] < kosten[0])

    def bild(self):
        return bytes(v for table in (self.n, self.s) for row in table for v in row)


def ausgang(welt, x, a, gestoert=False):
    return 1 if gestoert else (WELTEN[welt][a] if x else 0)


def identifizierbarkeit():
    bilder = {}
    for welt in WELTEN:
        modell = Zaehler()
        for _ in range(12):
            modell.sehen(1, 1, ausgang(welt, 1, 1))
        fordere(modell.n[1][0] == 0, "A1 erfindet unbeobachteten Arm")
        bilder[welt] = modell.bild().hex()
    fordere(bilder["hilfreich"] == bilder["unnoetig"] and
            bilder["wirkungslos"] == bilder["schaedlich"], "A1 unterscheidet gleiche sichtbare Geschichte")
    return bilder


def kalibriervergleich():
    bericht = []
    for welt in WELTEN:
        modell=Zaehler(); n=[0,0]; s=[0,0]
        for _ in range(4):
            for x,a in ((0,0),(0,1),(1,0),(1,1)):
                y=ausgang(welt,x,a); modell.sehen(x,a,y); n[x]+=1; s[x]+=y
        bericht.append({"welt":welt, "getrennt_n":modell.n, "getrennt_s":modell.s,
                        "naiv_p": [s[x]/n[x] for x in (0,1)], "anfang_n": [[0,0],[0,0]],
                        "anfang_unbekannt":True})
    return bericht


def lauf(welt, methode, bewertung=32, stoerung=False, modellklasse=Zaehler, ereignisfilter=None):
    fordere(welt in WELTEN and methode in METHODEN, "Unbekannter A-Lauf")
    modell=modellklasse(); protokoll=[]; kontroll_n=[[0,0],[0,0]]; kontroll_s=[[0,0],[0,0]]
    xs=[x for _ in range(4) for x in (0,0,1,1)] + [i % 2 for i in range(bewertung)]
    kalibrieraktionen=(0,1,0,1)
    for index,x in enumerate(xs):
        daten={"x":x}; eingabe(daten,"A")
        lernen = (methode=="vier_beobachtungen" and index<16) or (methode=="eine_beobachtung" and index<4)
        if lernen:
            a=kalibrieraktionen[index%4]
        elif methode in ("vier_beobachtungen", "eine_beobachtung"):
            a=modell.handeln(daten, 4 if methode=="vier_beobachtungen" else 1)
        else:
            a={"nie_entlasten":0,"immer_entlasten":1,"bei_vorzeichen":x}[methode]
        gestoert=stoerung and index-15 in (8,17)
        y=ausgang(welt,x,a,gestoert)
        e={"eingabe":daten,"belege":[(x,a,y)],"rettungen":0,"kosten":a+5*y,
           "gewertet":True,"gestoert":gestoert,"a":a,"y":y,"index":index+1}
        if ereignisfilter is not None: ereignisfilter(e)
        a_beleg(e,x,a,y); protokoll.append(e)
        if lernen:
            modell.sehen(x,a,y); kontroll_n[x][a]+=1; kontroll_s[x][a]+=y
        fordere(modell.n==kontroll_n and modell.s==kontroll_s,"A speichert nicht beobachtete Ergebnisse")
    a_vollstaendig(protokoll,16+bewertung,[16+i for i in (8,17) if i<=bewertung] if stoerung else [])
    def masse(zeilen):
        return {"takte":len(zeilen),"kosten":sum(e["kosten"] for e in zeilen),
                "handlungen":sum(e["a"] for e in zeilen),"fehlschlaege":sum(e["y"] for e in zeilen),
                "handlung_ohne_ausfall":sum(e["a"]==1 and e["y"]==0 for e in zeilen),
                "verpasst":sum(e["a"]==0 and e["y"]==1 for e in zeilen)}
    return {"welt":welt,"methode":methode,"stoerung":stoerung,"bewertung_runden":bewertung,
            "gesamt":masse(protokoll),"praefix":masse(protokoll[:16]),"bewertung":masse(protokoll[16:]),
            "modell_bytes":8 if methode in METHODEN[:2] else 0,
            "hinweis":"A=1/Y=0 ist eine gemeinsame Beobachtung, kein nachgewiesener unnoetiger Eingriff."}


def auswerten():
    return {"a1":identifizierbarkeit(), "a2":kalibriervergleich(),
            "laeufe":[lauf(w,m,b,s) for b,s in ((32,False),(8,False),(32,True))
                       for w in WELTEN for m in METHODEN]}
