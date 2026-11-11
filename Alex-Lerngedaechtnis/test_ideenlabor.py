import unittest
from unittest.mock import patch
from ideenlabor_basis import Prueffehler, ziehung
import ideenlabor_a as a
import ideenlabor_b as b

class PlanA(unittest.TestCase):
    def test_identische_sicht_und_keine_gegenbeobachtung(self):
        bilder=a.identifizierbarkeit()
        self.assertEqual(bilder["hilfreich"],bilder["unnoetig"])
        self.assertEqual(bilder["wirkungslos"],bilder["schaedlich"])

    def test_exakte_algebraische_bilanzen(self):
        erwartet={32:[208,160,240,432,336],8:[136,88,120,216,168]}
        for n,werte in erwartet.items():
            self.assertEqual([sum(a.lauf(w,m,n)["gesamt"]["kosten"] for w in a.WELTEN) for m in a.METHODEN],werte)
        self.assertEqual([sum(a.lauf(w,m)["bewertung"]["kosten"] for w in a.WELTEN) for m in a.METHODEN],[96,96,160,288,224])

    def test_stoerfolgen_zaehlen_alle_aufgaben(self):
        for w in a.WELTEN:
            for m in a.METHODEN:
                r=a.lauf(w,m,32,True)
                self.assertEqual(r["gesamt"]["takte"],48)

    def test_mutierter_lerner_speichert_erfundene_gegenbeobachtung(self):
        class Defekt(a.Zaehler):
            def sehen(self,x,aktion,y):
                super().sehen(x,aktion,y)
                if aktion==1 and y==0: super().sehen(x,0,0)
        with self.assertRaises(Prueffehler): a.lauf("hilfreich","vier_beobachtungen",modellklasse=Defekt)

    def test_mutierte_a_protokolle_laufen_durch_echten_pruefer(self):
        def rettung(e): e["rettungen"]=int(e["belege"][0][2]==0)
        def geheim(e): e["eingabe"]["welt"]="hilfreich"
        def nenner(e): e["gewertet"]=False
        def stoerung(e): e["gestoert"]=False
        for mutation in (rettung,geheim,nenner,stoerung):
            with self.subTest(mutation=mutation.__name__),self.assertRaises(Prueffehler):
                a.lauf("hilfreich","vier_beobachtungen",stoerung=True,ereignisfilter=mutation)

    def test_wiederlesen_veraendert_zaehler_nicht(self):
        modell=a.Zaehler(); modell.sehen(1,1,0); vorher=modell.bild()
        for _ in range(100): modell.handeln({"x":1},4)
        self.assertEqual(vorher,modell.bild())

class PlanB(unittest.TestCase):
    def test_sha_ziehung_mit_unabhaengiger_referenz(self):
        import hashlib
        text="OSCAN-IDEEN-v2|B|test|7|basis|1|x|0"
        self.assertEqual(ziehung("B","test",7,"basis",1,"x",2),int.from_bytes(hashlib.sha256(text.encode()).digest(),"big")%2)

    def test_fenster_ring_gegen_naive_liste(self):
        r=b.Ring(); hist=[]
        for i in range(100):
            y=int(i%3==0); r.lernen(y); hist=(hist+[y])[-32:]
            self.assertEqual(r.historie(),hist); self.assertEqual(r.n,len(hist)); self.assertEqual(r.s,sum(hist))
            self.assertEqual(len(r.bild()),35)

    def test_schwelle_und_start(self):
        for variant in b.VARIANTEN:
            m=b.Modell("ungeteilt",variant)
            self.assertEqual(m.prognose({"wort":"KNAPP","x":0,"z":1}),1)
            m.lernen(0)
            self.assertEqual(m.prognose({"wort":"KNAPP","x":0,"z":1}),0)

    def test_praefix_wird_wirklich_ungeteilt_ausgegeben(self):
        for variant in b.VARIANTEN:
            c=b.Modell("kandidat",variant); p=b.Modell("ungeteilt",variant)
            for i in range(256):
                x=i%2; z=(i//2)%2; daten={"wort":"KNAPP","x":x,"z":z}
                self.assertEqual(c.prognose(daten),p.prognose(daten)); c.lernen(x); p.lernen(x)
            self.assertEqual(c.wahl,"x")

    def test_wahl_tiebreak_und_20_fehler_huerde(self):
        for fehler,erwartet in (({"ungeteilt":40,"x":20,"z":20},"x"),({"ungeteilt":40,"x":21,"z":22},"ungeteilt")):
            m=b.Modell("kandidat","blatt32"); m.runde=255; m.fehler=fehler.copy()
            m.prognose({"wort":"KNAPP","x":0,"z":0}); m.lernen(1)
            self.assertEqual(m.wahl,erwartet)

    def test_globales_fenster_hat_identische_zeitgrenze(self):
        for typ in ("ungeteilt","x","z","xz","kandidat"):
            m=b.Modell(typ,"global128")
            for i in range(300):
                m.prognose({"wort":"KNAPP","x":i%2,"z":(i//2)%2}); m.lernen(i%2)
            self.assertEqual(len(m.globaldaten),128)
            self.assertLessEqual(len(m.bild()),512)

    def test_keine_neuwahl_nach_konzeptwechsel(self):
        for variant in b.VARIANTEN:
            m=b.Modell("kandidat",variant)
            for i in range(768):
                x=i%2; z=(i//2)%2; m.prognose({"wort":"KNAPP","x":x,"z":z}); m.lernen(x if i<400 else z)
                if i>=255: self.assertEqual(m.wahl,"x")

    def test_mutierter_kandidat_mit_eingefrorener_erfahrung_wird_im_lauf_entdeckt(self):
        class Defekt(b.Modell):
            def lernen(self,y):
                if self.runde>=256:
                    self.runde+=1; self.offen=None
                else: super().lernen(y)
        folge=[(i%2,(i//2)%2,0,0) for i in range(768)]
        for variant in b.VARIANTEN:
            with self.assertRaises(Prueffehler): b.lauf(folge,0,448,"R","kandidat",variant,Defekt)

    def test_mutierter_kandidat_mit_wortwechsel_wird_im_lauf_entdeckt(self):
        class Defekt(b.Modell):
            def lernen(self,y):
                super().lernen(y)
                if self.runde==300: self.wahl="z"
        folge=[(i%2,(i//2)%2,0,0) for i in range(768)]
        with self.assertRaises(Prueffehler): b.lauf(folge,0,448,"S","kandidat","blatt32",Defekt)

    def test_mutierter_runner_liest_ziel_vor_prognose(self):
        def defekt(t): t.ausgang(); t.prognose(); t.lernen()
        folge=[(i%2,(i//2)%2,0,0) for i in range(768)]
        with self.assertRaises(Prueffehler): b.lauf(folge,0,448,"S","kandidat","blatt32",ablauf=defekt)

    def test_mutierter_runner_wertet_erst_nach_lernen_neu_aus(self):
        def defekt(t): t.prognose(); t.ausgang(); t.lernen(); t.prognose()
        folge=[(i%2,(i//2)%2,0,0) for i in range(768)]
        with self.assertRaises(Prueffehler): b.lauf(folge,0,448,"S","kandidat","blatt32",ablauf=defekt)

    def test_jede_prognose_vor_ihrem_ausgang(self):
        m=b.Modell("x","blatt32")
        with self.assertRaises(Prueffehler): m.lernen(1)
        m.prognose({"wort":"KNAPP","x":0,"z":0})
        with self.assertRaises(Prueffehler): m.prognose({"wort":"KNAPP","x":0,"z":0})

class AusgabeCLI(unittest.TestCase):
    def test_getrennte_defaults_fuer_entwicklung_und_pruefung(self):
        import ideenlabor as cli
        self.assertEqual(tuple(p.name for p in cli.ausgabeziele("entwicklung")),("IDEEN-ENTWICKLUNG.json","IDEEN-ENTWICKLUNG.md"))
        self.assertEqual(tuple(p.name for p in cli.ausgabeziele("pruefung")),("IDEEN-PRUEFUNG.json","IDEEN-ERGEBNISSE.md"))

    def test_gleicher_ausgabepfad_wird_vor_rechnung_abgelehnt(self):
        import ideenlabor as cli
        with patch.object(cli,"ausfuehren") as run,self.assertRaises(SystemExit) as error:
            cli.main(["--ausgabe","gleich.json","--bericht","./gleich.json"])
        self.assertEqual(error.exception.code,2); run.assert_not_called()

    def test_existierende_datei_wird_vor_rechnung_nicht_ueberschrieben(self):
        import tempfile
        from pathlib import Path
        import ideenlabor as cli
        with tempfile.TemporaryDirectory(dir=".") as directory:
            roh=Path(directory)/"vorhanden.json"; text=Path(directory)/"neu.md"
            roh.write_text("behalten")
            with patch.object(cli,"ausfuehren") as run,self.assertRaises(SystemExit):
                cli.main(["--ausgabe",str(roh),"--bericht",str(text)])
            run.assert_not_called(); self.assertEqual(roh.read_text(),"behalten"); self.assertFalse(text.exists())

    def test_exklusives_schreiben_verliert_keinen_zwischenzeitlichen_bericht(self):
        import tempfile
        from pathlib import Path
        import ideenlabor as cli
        with tempfile.TemporaryDirectory(dir=".") as directory:
            roh=Path(directory)/"neu.json"; text=Path(directory)/"zwischenzeitlich.md"
            cli.pruefe_ausgaben((roh,text)); text.write_text("fremder Stand")
            with self.assertRaises(FileExistsError): cli.schreibe_ausgaben({},roh,text)
            self.assertEqual(text.read_text(),"fremder Stand"); self.assertFalse(roh.exists())

if __name__ == "__main__": unittest.main()
