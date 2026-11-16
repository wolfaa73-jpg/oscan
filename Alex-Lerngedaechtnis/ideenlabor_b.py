"""Plan B: einmalige Wortwahl, zwei vorab festgelegte Zeitfenster."""
from collections import deque
import struct
from ideenlabor_basis import fordere, ziehung
from ideenlabor_pruefer import eingabe, b_reihenfolge, b_wahl, b_speicher, b_globalfenster

METHODEN = ("kandidat", "immer_1", "immer_0", "letzter", "ungeteilt", "x", "z", "xz")
VARIANTEN = ("blatt32", "global128")
TEILE = ("ungeteilt", "x", "z", "xz")

class Ring:
    def __init__(self):
        self.daten=bytearray(32); self.n=0; self.pos=0; self.s=0
    def lernen(self,y):
        if self.n==32: self.s-=self.daten[self.pos]
        else: self.n+=1
        self.daten[self.pos]=y; self.s+=y; self.pos=(self.pos+1)%32
    def historie(self):
        start=self.pos if self.n==32 else 0
        return [self.daten[(start+i)%32] for i in range(self.n)]
    def bild(self):
        return bytes(self.daten)+bytes((self.n,self.pos,self.s))


def blatt(teilung,x,z):
    return {"ungeteilt":0,"x":x,"z":z,"xz":2*x+z}[teilung]

class Modell:
    def __init__(self,methode,variant):
        fordere(methode in METHODEN and variant in VARIANTEN,"Unbekanntes B-Verfahren")
        self.methode=methode; self.variant=variant; self.runde=0; self.letzter=1
        self.wahl=None if methode=="kandidat" else (methode if methode in TEILE else None)
        aktiv=TEILE[:3] if methode=="kandidat" else ((methode,) if methode in TEILE else ())
        self.fenster={p:[Ring() if variant=="blatt32" else None for _ in range({"ungeteilt":1,"x":2,"z":2,"xz":4}[p])] for p in aktiv}
        self.globaldaten=deque(maxlen=128); self.fehler={p:0 for p in TEILE[:3]}
        self.offen=None; self.arbeit={"ausgangslesungen":0,"fenster_updates":0,"neben_und_hauptprognosen":0}

    def bild(self):
        # Runde/Auswahl/Fehler/letzter Ausgang sowie ausstehende Nebenprognosen sind bezahlt.
        auswahl=255 if self.wahl is None else TEILE.index(self.wahl)
        pending=(0,0,0,0,0,0) if self.offen is None else (1,self.offen[0],self.offen[1],
                 *(self.offen[2].get(p,0) for p in TEILE[:3]))
        kopf=struct.pack("<BBBBH3HB",1,VARIANTEN.index(self.variant),METHODEN.index(self.methode),
                         auswahl,self.runde,*(self.fehler[p] for p in TEILE[:3]),self.letzter)+bytes(pending)
        kopf=kopf.ljust(20,b"\0")+struct.pack("<3I",*(self.arbeit[k] for k in ("ausgangslesungen","fenster_updates","neben_und_hauptprognosen")))
        if not self.fenster: return kopf
        if self.variant=="global128":
            daten=bytes(x | (z<<1) | (y<<2) for x,z,y in self.globaldaten)
            return kopf+bytes((len(daten),))+daten.ljust(128,b"\0")
        return kopf+b"".join(r.bild() for p in TEILE if p in self.fenster for r in self.fenster[p])

    def gedächtnis(self):
        if self.variant=="global128": return list(self.globaldaten)
        return {p:[r.historie() for r in rs] for p,rs in self.fenster.items()}

    def prognose(self,daten):
        eingabe(daten,"B"); fordere(self.offen is None,"Doppelte Vorhersage ohne Ausgang")
        x,z=daten["x"],daten["z"]; vorhersagen={}
        for p in self.fenster:
            if self.variant=="global128":
                n=s=0
                for xx,zz,y in self.globaldaten:
                    self.arbeit["ausgangslesungen"]+=1
                    if blatt(p,xx,zz)==blatt(p,x,z): n+=1; s+=y
            else:
                r=self.fenster[p][blatt(p,x,z)]; n,s=r.n,r.s
            vorhersagen[p]=int(2*s>=n)  # (s+1)/(n+2) >= 1/2, exakt ganzzahlig.
            self.arbeit["neben_und_hauptprognosen"]+=1
        if self.methode=="kandidat": a=vorhersagen[self.wahl or "ungeteilt"]
        elif self.methode in TEILE: a=vorhersagen[self.methode]
        else:
            a={"immer_1":1,"immer_0":0,"letzter":self.letzter}[self.methode]
            self.arbeit["neben_und_hauptprognosen"]+=1
        self.offen=(x,z,vorhersagen)
        return a

    def lernen(self,y):
        fordere(self.offen is not None and type(y) is int and y in (0,1),"Ausgang ohne Vorhersage")
        x,z,vorhersagen=self.offen; self.runde+=1
        if self.methode=="kandidat" and 129<=self.runde<=256:
            for p in TEILE[:3]: self.fehler[p]+=int(vorhersagen[p]!=y)
        if self.fenster:
            if self.variant=="global128":
                self.globaldaten.append((x,z,y)); self.arbeit["fenster_updates"]+=1
            else:
                for p,rs in self.fenster.items():
                    rs[blatt(p,x,z)].lernen(y); self.arbeit["fenster_updates"]+=1
        self.letzter=y; self.offen=None
        if self.methode=="kandidat" and self.runde==256:
            geeignet=[p for p in ("x","z") if self.fehler["ungeteilt"]-self.fehler[p]>=20]
            self.wahl=min(geeignet,key=lambda p:(self.fehler[p],TEILE.index(p))) if geeignet else "ungeteilt"
            self.fenster={self.wahl:self.fenster[self.wahl]}


def pruefe_lernen(vorher,nachher,x,z,y,variant):
    if variant=="global128":
        b_globalfenster(vorher,nachher,(x,z,y)); return
    for p,fenster in nachher.items():
        fordere(p in vorher,"Neue Wortstruktur ohne Auswahl")
        for index,werte in enumerate(fenster):
            erwartet=(vorher[p][index]+[y])[-32:] if index==blatt(p,x,z) else vorher[p][index]
            fordere(werte==erwartet,"B-Ergebnisfenster nicht korrekt weitergelernt")


def grundfolge(satz,seed):
    d=lambda r,f,n:ziehung("B",satz,seed,"basis",r,f,n)
    c=d(0,"merkmal",2); wechsel=(448,512,576)[d(0,"wechsel",3)]
    werte=[(d(i,"x",2),d(i,"z",2),d(i,"b",2),int(d(i,"e",10)==0)) for i in range(1,769)]
    return c,wechsel,werte


class Transaktion:
    """Protokolliert ausgefuehrte Schnittstellenaufrufe, keine behaupteten Phasen."""
    def __init__(self,modell,daten,ziel):
        self.modell=modell; self.daten=daten; self.ziel=ziel
        self.phasen=["eingabe"]; self.a=None; self.y=None
    def prognose(self):
        self.a=self.modell.prognose(self.daten); self.phasen.append("prognose")
        return self.a
    def ausgang(self):
        self.y=self.ziel(); self.phasen.append("ausgang"); return self.y
    def lernen(self):
        self.modell.lernen(self.y); self.phasen.append("lernen")
    def ausfuehren(self,ablauf=None):
        if ablauf is None:
            self.prognose(); self.ausgang(); self.lernen()
        else: ablauf(self)
        b_reihenfolge(tuple(self.phasen),self.daten)
        return self.a,self.y


def lauf(werte,c,wechsel,welt,methode,variant,modellklasse=Modell,ablauf=None):
    modell=modellklasse(methode,variant); spitze=len(modell.bild()); nach_auswahl=0; freeze=None
    fehler=[]; alarm=[]; verpasst=[]; warn=[]; fensterkontrollen=0
    for i,(x,z,b,e) in enumerate(werte,1):
        daten={"wort":"KNAPP","x":x,"z":z}; vorher=modell.gedächtnis()
        if methode=="kandidat" and i>=257: b_wahl(modell.wahl,freeze,i)
        # Nur der Auswerter besitzt die Welt. Der Zielzugriff wird tatsaechlich
        # erst durch Transaktion.ausgang nach der festgehaltenen Prognose ausgefuehrt.
        def ziel():
            relevant=(x,z)[c]
            return b if welt=="N" else relevant ^ e ^ int(welt=="R" and i>wechsel)
        transaktion=Transaktion(modell,daten,ziel)
        a,y=transaktion.ausfuehren(ablauf)
        # Ausstehende Nebenprognosen benoetigen hoechstens denselben festen Kopf;
        # fensterbezogene Spitze wird vor und nach Lernen erfasst.
        b_speicher(modell.bild(),len(modell.bild()))
        spitze=max(spitze,len(modell.bild()))
        if modell.fenster:
            pruefe_lernen(vorher,modell.gedächtnis(),x,z,y,variant); fensterkontrollen+=1
        if i==256: freeze=modell.wahl; nach_auswahl=len(modell.bild())
        b_speicher(modell.bild(),len(modell.bild())); spitze=max(spitze,len(modell.bild()))
        fehler.append(int(a!=y)); alarm.append(int(a==1 and y==0)); verpasst.append(int(a==0 and y==1)); warn.append(a)
    def zahlen(lo,hi):
        return {"takte":hi-lo,"fehler":sum(fehler[lo:hi]),"fehlalarme":sum(alarm[lo:hi]),
                "verpasst":sum(verpasst[lo:hi]),"warnungen":sum(warn[lo:hi]),
                "ausfaelle":sum(warn[lo:hi])-sum(alarm[lo:hi])+sum(verpasst[lo:hi])}
    return {"welt":welt,"methode":methode,"variante":variant,"wahl":modell.wahl,
            "relevant":("x","z")[c],"wechsel":wechsel,"gesamt":zahlen(0,768),
            "bewertung":zahlen(256,768),"anpassung":zahlen(wechsel,wechsel+64),
            "rest":zahlen(wechsel+64,768),"spitze_bytes":spitze,"nach_auswahl_bytes":nach_auswahl,
            "ende_bytes":len(modell.bild()),"arbeit":modell.arbeit,"fensterkontrollen":fensterkontrollen}


def kriterien(zeilen):
    ergebnis=[]
    for v in VARIANTEN:
        def werte(w,m): return sorted((r for r in zeilen if r["variante"]==v and r["welt"]==w and r["methode"]==m),key=lambda r:r["seed"])
        s=werte("S","kandidat"); n=werte("N","kandidat"); r=werte("R","kandidat")
        pooled=werte("S","ungeteilt"); vier=werte("R","xz")
        korrekt=sum(a["wahl"]==a["relevant"] for a in s); geteilt=sum(a["wahl"]!="ungeteilt" for a in n)
        differenz=sum((a["bewertung"]["fehler"]-b["bewertung"]["fehler"])/512 for a,b in zip(s,pooled))/len(s)
        rest=sum(a["rest"]["fehler"]/a["rest"]["takte"]-b["rest"]["fehler"]/b["rest"]["takte"] for a,b in zip(r,vier))/len(r)
        ergebnis.append({"variante":v,"folgen":len(s),"s_relevant":korrekt,"s_verlustdifferenz":differenz,
                         "n_geteilt":geteilt,"r_restdifferenz":rest,
                         "abnahme_anwendbar":len(s)==200,
                         "s_bestanden":len(s)==200 and korrekt>=180 and differenz<=-0.10,
                         "n_bestanden":len(n)==200 and geteilt<=10,
                         "r_bestanden":len(r)==200 and rest<=0.02})
    return ergebnis


def auswerten(satz,seeds):
    zeilen=[]
    for seed in seeds:
        c,wechsel,folge=grundfolge(satz,seed)
        for welt in ("S","N","R"):
            for variante in VARIANTEN:
                for methode in METHODEN:
                    zeile=lauf(folge,c,wechsel,welt,methode,variante)
                    zeile["seed"]=seed; zeilen.append(zeile)
    return {"laeufe":zeilen,"kriterien":kriterien(zeilen)}
