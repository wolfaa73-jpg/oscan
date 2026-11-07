import unittest
from ideenlabor_basis import Prueffehler
import ideenlabor_c as c

class PlanC(unittest.TestCase):
    @staticmethod
    def block(start,ausnahmen=()):
        return c.packen(((i-1)%4) | ((((i-1)//64)%2)<<2) | ((((i-1)%2)^int(i in ausnahmen))<<3) for i in range(start,start+64))

    def test_bits_halbbytes_und_little_endian(self):
        self.assertEqual(c.packen([1,14,3]),bytes((225,3)))
        self.assertEqual(c.kopf(0,256,12),bytes((1,0,0,1,12,0,0,0)))
        self.assertEqual([c.wert(c.packen([1,14,3]),i) for i in range(3)],[1,14,3])

    def test_katalognummer_und_vollstaendiger_ersatz(self):
        for xm in range(8):
            for qm in range(4):
                for ym in range(4):
                    werte=[c.regelwert(xm,qm,ym,i) for i in range(64)]
                    werte[7]^=15
                    enc,_=c.abschnitt(1,werte)
                    bild=c.kopf(1,64,1)+enc
                    self.assertEqual([v for _,v in c.dekodieren(bild)],werte)

    def test_layoutrechnung_128_und_kurze_folge(self):
        bild=c.leer("regel")
        for start in (1,65): bild,_=c.verarbeiten(bild,self.block(start,(5,)),"regel",128)
        self.assertEqual(len(bild),28)
        self.assertEqual(8+len(c.packen([0]*128)),72)
        self.assertEqual(8+len(c.packen([0]*12)),14)
        self.assertEqual(8+c.REGEL.size+2,19)

    def test_budget_32_vergisst_ehrlich_64_erhaelt_beide_ausnahmen(self):
        for budget in (32,64,128):
            bild=c.leer("regel")
            for start in (1,65,129,193):
                bild,work=c.verarbeiten(bild,self.block(start,(1,130)),"regel",budget)
                self.assertLessEqual(len(bild),budget); self.assertLessEqual(work["arbeitsraum_logisch_obere_grenze"],512)
            if budget==32: self.assertEqual(c.antwort(bild,"historie",1),c.UNBEKANNT)
            else:
                self.assertEqual(c.antwort(bild,"historie",1),1)
                self.assertEqual(c.antwort(bild,"historie",130),0)
                self.assertEqual(len(bild),48)

    def test_rohring_ids_und_verlorene_daten_kommen_nicht_zurueck(self):
        bild=c.leer("ring")
        for start in (1,65,129,193): bild,_=c.verarbeiten(bild,self.block(start),"ring",32)
        daten=dict(c.dekodieren(bild))
        self.assertEqual(min(daten),209); self.assertEqual(max(daten),256); self.assertEqual(len(daten),48)

    def test_widerruf_entwertet_zaehler_und_bleibt_bezahlt(self):
        for typ in c.METHODEN:
            bild=c.leer(typ)
            for start in (1,65,129,193): bild,_=c.verarbeiten(bild,self.block(start),typ,64)
            nachher=c.widerrufen(bild,[1,256],typ,64)
            self.assertLessEqual(len(nachher),64)
            for i in (1,256):
                self.assertEqual(c.antwort(nachher,"historie",i),c.WIDERRUFEN)
                self.assertEqual(c.antwort(nachher,"quelle",i),c.WIDERRUFEN)
            if typ in ("zaehler","halbiert"):
                self.assertEqual(c.antwort(nachher,"zukunft",(0,0)),c.UNBEKANNT)

    def test_historische_abfragen_veraendern_keinen_zustand(self):
        bild,_=c.verarbeiten(c.leer("regel"),self.block(1,(7,)),"regel",64)
        vorher=bytes(bild)
        for i in range(1,65): c.antwort(bild,"historie",i); c.antwort(bild,"quelle",i)
        self.assertEqual(bild,vorher)

    def mutation(self,modus):
        def defekt(bild,block,verfahren,budget):
            neu,arbeit=c.verarbeiten(bild,block,verfahren,budget)
            if modus=="cache": return {"abbild":neu,"cache":{1:1}},arbeit
            art,ende,n,rev,pos=c.lesen(neu)
            if art==1 and neu[pos]==1:
                daten=bytearray(neu)
                if modus=="ausnahme" and daten[pos+8]:
                    daten[pos+8]-=1; del daten[pos+9:pos+11]
                elif modus=="quelle": daten[pos+6]^=1
                elif modus=="rueckwirkend" and ende>=128: daten[pos+7]=3
                neu=bytes(daten)
            return neu,arbeit
        return defekt

    def test_mutierter_kodierer_ohne_ausnahme_wird_vom_echten_lauf_abgelehnt(self):
        with self.assertRaises(Prueffehler): c.lauf("test",0,"wiederholung","regel",64,self.mutation("ausnahme"))

    def test_mutierter_kodierer_mit_falscher_quelle_wird_vom_echten_lauf_abgelehnt(self):
        with self.assertRaises(Prueffehler): c.lauf("test",0,"wiederholung","regel",64,self.mutation("quelle"))

    def test_mutierter_kodierer_mit_rueckwirkender_regel_wird_vom_echten_lauf_abgelehnt(self):
        with self.assertRaises(Prueffehler): c.lauf("test",0,"wiederholung","regel",64,self.mutation("rueckwirkend"))

    def test_mutierter_kodierer_mit_aussenarchiv_wird_vom_echten_lauf_abgelehnt(self):
        with self.assertRaises(Prueffehler): c.lauf("test",0,"wiederholung","regel",64,self.mutation("cache"))

    def test_mutierte_abfrage_ignoriert_widerruf_und_wird_vom_echten_lauf_abgelehnt(self):
        def defekt(bild,art,frage):
            typ,ende,n,rev,pos=c.lesen(bild)
            if rev: bild=c.kopf(typ,ende,n)+bild[pos:]
            return c.antwort(bild,art,frage)
        with self.assertRaises(Prueffehler): c.lauf("test",0,"wiederholung","regel",64,antwortfunktion=defekt)

    def test_echter_closure_cache_mit_korrekten_vergessenen_werten_wird_abgelehnt(self):
        werte,_=c.welt("test",0,"wiederholung")
        cache={i+1:w for i,w in enumerate(werte)}
        def defekt(bild,art,frage):
            antwort=c.antwort(bild,art,frage)
            if antwort==c.UNBEKANNT and art!="zukunft":
                return cache[frage][2 if art=="historie" else 1]
            return antwort
        with self.assertRaises(Prueffehler):
            c.lauf("test",0,"wiederholung","regel",32,antwortfunktion=defekt)

    def test_zukunftsprognose_darf_keinen_externen_cache_nutzen(self):
        def defekt(bild,art,frage):
            normal=c.antwort(bild,art,frage)
            return 1 if art=="zukunft" and normal==c.UNBEKANNT else normal
        with self.assertRaises(Prueffehler):
            c.lauf("test",0,"wiederholung","unbekannt",32,antwortfunktion=defekt)

    def test_falscher_zeitstand_des_abbilds_wird_abgelehnt(self):
        def defekt(bild,block,verfahren,budget):
            neu,arbeit=c.verarbeiten(bild,block,verfahren,budget)
            daten=bytearray(neu); daten[2:4]=(128).to_bytes(2,"little")
            return bytes(daten),arbeit
        with self.assertRaises(Prueffehler): c.lauf("test",0,"wiederholung","ring",32,verarbeiter=defekt)

    def test_naive_zaehleroracle(self):
        for typ in ("zaehler","halbiert"):
            bild=c.leer(typ); oracle=[0]*16
            for start in (1,65,129,193):
                block=self.block(start,(4,17,201))
                for i in range(64):
                    x,q,y=c.tupel(c.wert(block,i)); oracle[4*x+2*q+y]+=1
                if typ=="halbiert": oracle=[v//2 for v in oracle]
                bild,_=c.verarbeiten(bild,block,typ,32)
                self.assertEqual(list(bild[8:]),oracle)

    def test_zaehlerueberlauf_und_periodisches_halbieren(self):
        for typ,erwartet in (("zaehler",128),("halbiert",60)):
            bild=c.leer(typ)
            for _ in range(4): bild,_=c.verarbeiten(bild,bytes(32),typ,32)
            self.assertEqual(bild[8],erwartet)
            self.assertEqual(bild[9:],bytes(15))

    def test_roh_gewinnt_gleichstand_und_kleinste_regelnummer(self):
        kurz,_=c.abschnitt(1,[0]*9)
        self.assertEqual(kurz[0],0)
        lang,_=c.abschnitt(1,[0]*64)
        self.assertEqual(c.REGEL.unpack(lang),(1,1,64,0,0,0,0))

    def test_fragenlisten_und_widerruf_reproduzierbar(self):
        werte,meta=c.welt("test",0,"wiederholung")
        ids,ziele=c.fragen("test",0,"wiederholung",256,meta)
        self.assertEqual(len(set(ids)),12)
        self.assertIn(meta["frueh"],ids); self.assertIn(meta["spaet"],ids)
        self.assertEqual((ids,ziele),c.fragen("test",0,"wiederholung",256,meta))
        rev=c.ruecknahmen("test",0,"wiederholung",meta)
        self.assertIn(meta["frueh"],rev); self.assertNotIn(meta["spaet"],rev)
        self.assertEqual(len(set(rev)),2)

if __name__ == "__main__": unittest.main()
