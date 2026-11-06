"""Plan C: selbstenthaltene Bytebilder; keine Rueckgriffe auf ein Roharchiv.

Der Auswerter kennt den Verlauf; Kodierer und Abfrage erhalten nur das Bytebild
und den neuen 32-Byte-Block bzw. die einzelne Frage. Python-Objekt/RAM-Overhead
ist ausdruecklich keine gemessene Hardwaregroesse. Die logische Arbeitsbilanz
zaehlt die unten tatsaechlich begrenzten Puffer und 32 Byte Verwaltungszustaende.
"""
import struct
from itertools import chain
from fractions import Fraction
from ideenlabor_basis import fordere, ziehung
from ideenlabor_pruefer import c_zustand, c_rekonstruktion, c_antwort, c_prognose

METHODEN=("regel","ring","zaehler","halbiert","unbekannt","konstant_0","immer_1")
PFLICHTGEGNER=METHODEN[1:6]
FAMILIEN=("wiederholung","wechsel","unregelmaessig")
KOPF=struct.Struct("<BBHHBB")
REGEL=struct.Struct("<BHHBBBB")
ROH=struct.Struct("<BHB")
UNBEKANNT="UNBEKANNT"
WIDERRUFEN="WIDERRUFEN"


def packen(werte):
    daten=bytearray(); halb=False
    for v in werte:
        fordere(type(v) is int and 0<=v<16,"Ungueltiges Vierbit-Ereignis")
        if halb: daten[-1]|=v<<4
        else: daten.append(v)
        halb=not halb
    return bytes(daten)


def wert(daten,i): return (daten[i//2] >> (4*(i%2))) & 15

def tupel(v): return (v&3,(v>>2)&1,(v>>3)&1)

def kopf(art,ende,anzahl,widerrufe=()):
    return KOPF.pack(1,art,ende,anzahl,len(widerrufe),0)+b"".join(struct.pack("<H",i) for i in widerrufe)


def leer(verfahren):
    art={"regel":0,"ring":0,"zaehler":2,"halbiert":3,"unbekannt":4,"konstant_0":5,"immer_1":6}[verfahren]
    return kopf(art,0,16 if art in (2,3) else 0)+(bytes(16) if art in (2,3) else b"")


def lesen(bild):
    fordere(type(bild) is bytes and len(bild)>=8,"Kein vollstaendiges C-Abbild")
    version,art,ende,n,nw,flags=KOPF.unpack_from(bild)
    fordere(version==1 and art in range(7) and flags==0 and nw<=2 and ende<=256,"Ungueltiger C-Kopf")
    pos=8+2*nw; fordere(len(bild)>=pos,"Verkuerzter Widerruf")
    widerrufe=tuple(struct.unpack_from("<H",bild,8+2*i)[0] for i in range(nw))
    fordere(tuple(sorted(set(widerrufe)))==widerrufe and all(1<=i<=ende for i in widerrufe),"Ungueltige Ruecknahmen")
    if art==0:
        fordere(n<=ende and len(bild)==pos+(n+1)//2,"Ungueltiges Ringbild")
        if n%2: fordere(bild[-1]<16,"Nichtnull-Padding")
    elif art in (2,3): fordere(n==16 and len(bild)==pos+16,"Ungueltiges Zaehlerbild")
    elif art>=4: fordere(n==0 and len(bild)==pos,"Ungueltiges konstantes Bild")
    return art,ende,n,widerrufe,pos


def regelwert(xm,qm,ym,i):
    x=xm if xm<4 else (i+xm-4)%4
    q=qm if qm<2 else (i+qm-2)%2
    y=ym if ym<2 else (x%2) ^ (ym==3)
    return x | (q<<2) | (int(y)<<3)


def dekodieren(bild):
    art,ende,n,widerrufe,pos=lesen(bild)
    if art==0:
        for k in range(n): yield ende-n+1+k,wert(bild[pos:],k)
    elif art==1:
        vorher=None
        for _ in range(n):
            fordere(pos<len(bild),"Abschnitt fehlt")
            typ=bild[pos]
            if typ==0:
                fordere(pos+4<=len(bild),"Rohkopf fehlt")
                _,start,laenge=ROH.unpack_from(bild,pos); pos+=4
                fordere(1<=laenge<=64 and pos+(laenge+1)//2<=len(bild),"Rohabschnitt ungueltig")
                daten=bild[pos:pos+(laenge+1)//2]; pos+=(laenge+1)//2
                if laenge%2: fordere(daten[-1]<16,"Nichtnull-Padding")
                values=(wert(daten,i) for i in range(laenge))
            elif typ==1:
                fordere(pos+9<=len(bild),"Regelkopf fehlt")
                _,start,laenge,xm,qm,ym,nex=REGEL.unpack_from(bild,pos); pos+=9
                fordere(1<=laenge<=64 and xm<8 and qm<4 and ym<4 and nex<=laenge and pos+2*nex<=len(bild),"Regelabschnitt ungueltig")
                ausnahmen=bild[pos:pos+2*nex]; pos+=2*nex
                fordere(all(ausnahmen[2*i]<laenge and ausnahmen[2*i+1]<16 and
                            (i==0 or ausnahmen[2*i]>ausnahmen[2*i-2]) for i in range(nex)),"Ausnahmen ungueltig")
                def generate():
                    k=0
                    for i in range(laenge):
                        if k<nex and ausnahmen[2*k]==i:
                            yield ausnahmen[2*k+1]; k+=1
                        else: yield regelwert(xm,qm,ym,i)
                values=generate()
            else: fordere(False,"Abschnittstyp ungueltig")
            fordere(start>=1 and (start-1)//64==(start+laenge-2)//64,"Abschnitt ueber Blockgrenze")
            fordere(vorher is None or start==vorher+1,"Luecke im erhaltenen Suffix")
            for i,v in enumerate(values): yield start+i,v
            vorher=start+laenge-1
        fordere(pos==len(bild) and (n==0 or vorher==ende),"Restbytes oder falsches Ende")


def abschnitt(start,werte):
    # Suche speichert nur Regelnummer und Fehlerzahl. Erst der Gewinner wird
    # materialisiert; keine Sammlung alter/versuchsweiser Regelbilder.
    beste_laenge=4+(len(werte)+1)//2; beste_regel=None; arbeit=0
    for xm in range(8):
        for qm in range(4):
            for ym in range(4):
                fehler=0
                for i,v in enumerate(werte):
                    arbeit+=1; fehler+=int(v!=regelwert(xm,qm,ym,i))
                    if 9+2*fehler>=beste_laenge: break
                else:
                    if 9+2*fehler<beste_laenge:
                        beste_laenge=9+2*fehler; beste_regel=(xm,qm,ym,fehler)
    if beste_regel is None:
        return ROH.pack(0,start,len(werte))+packen(werte),arbeit
    xm,qm,ym,nex=beste_regel; abweichungen=bytearray()
    for i,v in enumerate(werte):
        arbeit+=1
        if v!=regelwert(xm,qm,ym,i): abweichungen.extend((i,v))
    return REGEL.pack(1,start,len(werte),xm,qm,ym,nex)+bytes(abweichungen),arbeit


class Nibbles:
    """Lesesicht ohne zweite Kopie eines Abschnitts."""
    def __init__(self,daten,start,n): self.daten=daten; self.start=start; self.n=n
    def __len__(self): return self.n
    def __iter__(self):
        for i in range(self.n): yield wert(self.daten,self.start+i)


def auswahl(kombi,anzahl,ende,budget,widerrufe,mit_regeln):
    platz=budget-8-2*len(widerrufe); ringzahl=min(anzahl,2*platz)
    teile=[]; gespeicherte=0; gesamtbytes=0; arbeit=0
    if mit_regeln:
        start=ende-anzahl+1; offset=0
        while offset<anzahl:
            laenge=min(64-(start+offset-1)%64,anzahl-offset)
            block=Nibbles(kombi,offset,laenge)
            teil,aufwand=abschnitt(start+offset,block); arbeit+=aufwand
            while teile and gesamtbytes+len(teil)>platz:
                alt,n=teile.pop(0); gesamtbytes-=len(alt); gespeicherte-=n; del alt
            if len(teil)<=platz:
                teile.append((teil,laenge)); gesamtbytes+=len(teil); gespeicherte+=laenge
            offset+=laenge
            del block,teil
    regel_gewinnt=mit_regeln and (gespeicherte>ringzahl or
                       (gespeicherte==ringzahl and gesamtbytes<(ringzahl+1)//2))
    if regel_gewinnt:
        anzahlteile=len(teile)
        # kombi wird im Aufrufer nicht als zusaetzlicher Zustand aufbewahrt.
        bild=b"".join([kopf(1,ende,anzahlteile,widerrufe)]+[t for t,_ in teile])
    else:
        teile.clear()
        payload=packen(wert(kombi,i) for i in range(anzahl-ringzahl,anzahl))
        bild=kopf(0,ende,ringzahl,widerrufe)+payload
    return bild,arbeit


def verarbeiten(bild,block,verfahren,budget):
    c_zustand(bild,budget); art,ende,n,widerrufe,pos=lesen(bild)
    fordere(len(block)==32 and ende+64<=256 and not widerrufe,"Genau ein neuer 64er-Block erforderlich")
    ende+=64; arbeit=0
    if verfahren in ("regel","ring"):
        anzahl=sum(1 for _ in dekodieren(bild))
        kombi=packen(chain((v for _,v in dekodieren(bild)),(wert(block,i) for i in range(64))))
        neu,arbeit=auswahl(kombi,anzahl+64,ende,budget,(),verfahren=="regel")
    elif verfahren in ("zaehler","halbiert"):
        z=list(bild[pos:]);
        for i in range(64):
            x,q,y=tupel(wert(block,i)); stelle=4*x+2*q+y
            if z[stelle]==255: z=[v//2 for v in z]
            z[stelle]+=1; arbeit+=1
        if verfahren=="halbiert": z=[v//2 for v in z]
        neu=kopf(2 if verfahren=="zaehler" else 3,ende,16)+bytes(z)
    else:
        neu=kopf({"unbekannt":4,"konstant_0":5,"immer_1":6}[verfahren],ende,0)
    c_zustand(neu,budget)
    return neu,{"regelvergleiche":arbeit if verfahren=="regel" else 0,
                "zaehler_updates":64 if verfahren in ("zaehler","halbiert") else 0,
                "arbeitsraum_logisch_obere_grenze":480 if verfahren=="regel" else (448 if verfahren=="ring" else 144)}


def widerrufen(bild,nummern,verfahren,budget):
    art,ende,n,vorher,pos=lesen(bild); nummern=tuple(sorted(set(vorher).union(nummern)))
    fordere(len(nummern)<=2 and all(1<=i<=ende for i in nummern),"Ungueltiger Widerruf")
    if verfahren in ("regel","ring"):
        anzahl=sum(1 for _ in dekodieren(bild)); kombi=packen(v for _,v in dekodieren(bild))
        neu,_=auswahl(kombi,anzahl,ende,budget,nummern,verfahren=="regel")
    elif verfahren in ("zaehler","halbiert"):
        neu=kopf(art,ende,16,nummern)+bytes(16)
    else: neu=kopf(art,ende,0,nummern)
    c_zustand(neu,budget); return neu


def antwort(bild,art,frage,mit_aufwand=False):
    typ,ende,n,widerrufe,pos=lesen(bild); schritte=0
    def resultat(v): return (v,schritte) if mit_aufwand else v
    if art!="zukunft":
        if frage in widerrufe: return resultat(WIDERRUFEN)
        for nummer,v in dekodieren(bild):
            schritte+=1
            if nummer==frage: return resultat(tupel(v)[2 if art=="historie" else 1])
        return resultat(UNBEKANNT)
    x,q=frage
    if typ>=4: return resultat(UNBEKANNT if typ==4 else (0 if typ==5 else 1))
    if typ in (2,3):
        null,eins=bild[pos+4*x+2*q:pos+4*x+2*q+2]
    else:
        null=eins=0
        for nummer,v in dekodieren(bild):
            schritte+=1; xx,qq,y=tupel(v)
            if nummer not in widerrufe and (xx,qq)==(x,q):
                null+=int(y==0); eins+=int(y==1)
    return resultat(UNBEKANNT if null+eins==0 else int(eins>null))


def welt(satz,seed,familie):
    d=lambda r,f,n:ziehung("C",satz,seed,familie,r,f,n)
    u=d(0,"u",4); v=d(0,"v",2); frueh=1+d(0,"ausnahme_frueh",64); spaet=129+d(0,"ausnahme_spaet",128)
    wechsel=(96,160,224)[d(0,"wechsel",3)]; werte=[]
    for i in range(1,257):
        if familie=="unregelmaessig": x,q,y=d(i,"x",4),d(i,"q",2),d(i,"y",2)
        else:
            x=(i-1+u)%4; q=((i-1)//64+v)%2; y=x%2
            if familie=="wiederholung" and i in (frueh,spaet): y^=1
            if familie=="wechsel" and i>wechsel: y^=1
        werte.append((x,q,y))
    return werte,{"frueh":frueh,"spaet":spaet,"wechsel":wechsel}


def fragen(satz,seed,familie,punkt,meta):
    d=lambda f,n:ziehung("C",satz,seed,familie,punkt,f,n)
    pflicht=[meta["frueh"],meta["spaet"]] if familie=="wiederholung" else ([meta["wechsel"],meta["wechsel"]+1] if familie=="wechsel" else [])
    ids=[i for i in pflicht if i<=punkt]; index=0
    while len(ids)<12:
        i=1+d(f"frage_{index}",punkt); index+=1
        if i not in ids: ids.append(i)
    ids.sort(key=lambda i:(d(f"reihenfolge_{i}",2**256),i))
    ziele={}
    for x in range(4):
        for q in range(2):
            ziele[x,q]=d(f"zukunft_{x}_{q}",2) if familie=="unregelmaessig" else x%2 ^ int(familie=="wechsel" and punkt>meta["wechsel"])
    return ids,ziele


def ruecknahmen(satz,seed,familie,meta):
    ids=[meta["frueh"]] if familie=="wiederholung" else []; index=0
    while len(ids)<2:
        i=1+ziehung("C",satz,seed,familie,256,f"widerruf_{index}",256); index+=1
        if i not in ids and (familie!="wiederholung" or i not in (meta["frueh"],meta["spaet"])): ids.append(i)
    return sorted(ids)


def batterie(bild,ids,ziele,wahrheit,widerrufe=(),antwortfunktion=antwort):
    ergebnis={}
    belege={i:tupel(v) for i,v in dekodieren(bild)}
    belegbare_ids=set(belege)
    typ,_,_,_,pos=lesen(bild)
    for art in ("zukunft","historie","quelle"):
        zaehler={"fragen":0,"richtig":0,"falsch":0,"unbekannt":0,"verlust":0,"widerrufen":0,"dekodierte_ereignisse":0,
                 "warnungen":0,"fehlalarme":0,"verpasst":0,"ausfaelle":0}
        for frage in (list(ziele) if art=="zukunft" else ids):
            # Jede Antwort liest nur dieselben unveraenderlichen Bytes. Keine Anfragehistorie.
            if antwortfunktion is antwort:
                a,schritte=antwort(bytes(bild),art,frage,mit_aufwand=True)
            else:
                a=antwortfunktion(bytes(bild),art,frage); schritte=0
            zaehler["dekodierte_ereignisse"]+=schritte
            c_antwort(art,frage,a,wahrheit,widerrufe,belegbare_ids)
            if art=="zukunft": c_prognose(a,frage,typ,belege,bild[pos:],widerrufe)
            ziel=ziele[frage] if art=="zukunft" else (WIDERRUFEN if frage in widerrufe else wahrheit[frage][2 if art=="historie" else 1])
            status="unbekannt" if a==UNBEKANNT else ("richtig" if a==ziel else "falsch")
            zaehler["fragen"]+=1; zaehler[status]+=1; zaehler["verlust"]+={"richtig":0,"falsch":4,"unbekannt":1}[status]
            zaehler["widerrufen"]+=int(a==WIDERRUFEN)
            if art=="zukunft":
                zaehler["warnungen"]+=int(a==1); zaehler["fehlalarme"]+=int(a==1 and ziel==0)
                zaehler["verpasst"]+=int(a==0 and ziel==1); zaehler["ausfaelle"]+=ziel
        ergebnis[art]=zaehler
    return ergebnis


def lauf(satz,seed,familie,verfahren,budget,verarbeiter=verarbeiten,antwortfunktion=antwort):
    werte,meta=welt(satz,seed,familie); wahrheit={i+1:w for i,w in enumerate(werte)}
    bild=leer(verfahren); fragenwerte=[]; spitze=len(bild); arbeit=0; arbeitsraum=0
    for punkt in (64,128,192,256):
        block=packen(x | (q<<2) | (y<<3) for x,q,y in werte[punkt-64:punkt])
        bild,aufwand=verarbeiter(bild,block,verfahren,budget)
        c_zustand(bild,budget); fordere(lesen(bild)[1]==punkt,"C-Abbild behauptet falschen Beobachtungszeitpunkt")
        c_rekonstruktion({i:tupel(v) for i,v in dekodieren(bild)},{i:v for i,v in wahrheit.items() if i<=punkt})
        spitze=max(spitze,len(bild)); arbeit+=aufwand["regelvergleiche"]+aufwand["zaehler_updates"]
        arbeitsraum=max(arbeitsraum,aufwand["arbeitsraum_logisch_obere_grenze"])
        ids,ziele=fragen(satz,seed,familie,punkt,meta)
        fragenwerte.append({"punkt":punkt,"werte":batterie(bild,ids,ziele,wahrheit,antwortfunktion=antwortfunktion),"abbild_bytes":len(bild)})
    ausnahmen={str(i):antwort(bild,"historie",i) for i in (meta["frueh"],meta["spaet"])} if familie=="wiederholung" else {}
    if verfahren=="regel" and familie=="wiederholung" and budget>=64:
        fordere(all(ausnahmen[str(i)]==wahrheit[i][2] for i in (meta["frueh"],meta["spaet"])),"Ausnahmeabnahme bei 64/128 Byte gescheitert")
    widerrufe=ruecknahmen(satz,seed,familie,meta)
    nachher=widerrufen(bild,widerrufe,verfahren,budget); spitze=max(spitze,len(nachher))
    ids=list(dict.fromkeys(ids+widerrufe))
    rueck=batterie(nachher,ids,ziele,wahrheit,widerrufe,antwortfunktion)
    mittel={art:sum(Fraction(t["werte"][art]["verlust"],t["werte"][art]["fragen"]) for t in fragenwerte)/4 for art in ("zukunft","historie","quelle")}
    mittel["widerruf"]=sum(Fraction(rueck[a]["verlust"],rueck[a]["fragen"]) for a in rueck)/3
    gesamt=sum(mittel.values())/4
    return {"seed":seed,"familie":familie,"methode":verfahren,"budget":budget,"pruefpunkte":fragenwerte,
            "widerruf":rueck,"ausnahmen":ausnahmen,"frageart_mittel":{k:float(v) for k,v in mittel.items()},"gesamtverlust":float(gesamt),
            "gesamtbruch":[gesamt.numerator,gesamt.denominator],
            "spitze_abbild_bytes":spitze,"ende_bytes":len(nachher),"regel_und_zaehleroperationen":arbeit,
            "arbeitsraum_logisch_obere_grenze":arbeitsraum}


def auswerten(satz,seeds):
    zeilen=[lauf(satz,seed,familie,m,b) for seed in seeds for familie in FAMILIEN for b in (32,64,128) for m in METHODEN]
    urteile=[]
    for budget in (32,64,128):
        mittel={m:sum(sum(Fraction(*r["gesamtbruch"]) for r in zeilen if r["budget"]==budget and r["methode"]==m and r["familie"]==f)/len(seeds) for f in FAMILIEN)/3 for m in METHODEN}
        urteile.append({"budget":budget,"mittel":{k:float(v) for k,v in mittel.items()},"pflichtgegner":list(PFLICHTGEGNER),
                        "nutzen":all(mittel["regel"]<mittel[m] for m in PFLICHTGEGNER)})
    return {"laeufe":zeilen,"kriterien":urteile}
