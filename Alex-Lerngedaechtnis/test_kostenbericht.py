"""Unabhängige Paarungs-, Normierungs- und Integritätsprüfungen des Kostenberichts."""
import contextlib
import csv
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import kostenlabor as k
import kostenbericht as b


class BootstrapTests(unittest.TestCase):
    def test_quantile_linear_interpolation(self):
        self.assertEqual(b.quantil([10,0],.025),.25)
        self.assertEqual(b.quantil([10,0],.975),9.75)
        self.assertEqual(b.quantil([4],.5),4)
        with self.assertRaises(ValueError):
            b.quantil([], .5)

    def test_identische_paare_bleiben_exakt_null(self):
        p = b.BootstrapPlan({"a":3,"b":2},50)
        self.assertEqual(p.intervall({"a":[0]*3,"b":[0]*2},930),
                         dict(differenz_pro_1000=0,untergrenze=0,obergrenze=0))

    def test_strata_behalten_ihre_urspruenglichen_groessen(self):
        # Nicht Mittel der Familienmittel: (1 + 9+9+9)/4 = 7, nicht 5.
        p = b.BootstrapPlan({"a":1,"b":3},50)
        z = p.intervall({"a":[1],"b":[9,9,9]},100)
        self.assertEqual(z,dict(differenz_pro_1000=70,untergrenze=70,obergrenze=70))

    def test_reproduzierbar_und_ungueltige_familien_abgewiesen(self):
        x = {"a":[-2,0,3,8],"b":[3,5]}
        a = b.BootstrapPlan({"a":4,"b":2},50,11).intervall(x,20)
        c = b.BootstrapPlan({"b":2,"a":4},50,11).intervall(x,20)
        self.assertEqual(a,c)
        self.assertLess(a["untergrenze"],a["obergrenze"])
        with self.assertRaises(ValueError):
            b.BootstrapPlan({"a":4},50).intervall(x,20)
        with self.assertRaises(ValueError):
            b.BootstrapPlan({"a":0})
        with self.assertRaises(ValueError):
            b.BootstrapPlan({"a":1}).intervall({"a":[float("nan")]},20)

    def test_takt_und_phase_sind_verschiedene_gepaarte_kosten(self):
        daten = {
            ("speicher","startwert-h03-s10"): {f:[(5,7,3)]*2 for f in k.s.FAMILIEN},
            ("speicher","startwert-h06-s12"): {f:[(1,2,1)]*2 for f in k.s.FAMILIEN},
        }
        auswertungen = [dict(signal="speicher",kostenmodell=art,verhaeltnis=10,
                            suche="startwert_gemeinsam",konfiguration="startwert-h03-s10") for art in k.KOSTEN]
        meta = dict(anzahl=2,einstellungen=dict(takte=90,horizont=30))
        rows = list(b.intervalle(auswertungen,daten,meta,wiederholungen=20))
        # Delta-FP=4, Delta-FN=5, Delta-Phase=2. Normierung auf60 Instrumenttakte.
        for row, erwartet in zip(rows,(900,400)):
            self.assertAlmostEqual(row["differenz_pro_1000"],erwartet)
            self.assertAlmostEqual(row["untergrenze"],erwartet)
            self.assertAlmostEqual(row["obergrenze"],erwartet)


class SchwellenwechselTests(unittest.TestCase):
    @staticmethod
    def auswahl():
        return [dict(signal="temperatur",kostenmodell="takt",suche="erbe_schwelle",verhaeltnis=r,
                     **k.konfig("erbe",index=11 if r in (3,100) else 12)) for r in range(1,101)]

    def test_aa_b_a_wird_nur_ueber_benachbarte_verhaeltnisse_zusammengefasst(self):
        original = self.auswahl()
        # Eingabereihenfolge ist kein zusätzlicher Auswahlparameter.
        rows = list(b.schwellenwechsel(list(reversed(original))))
        self.assertEqual([(z["r_von"],z["r_bis"],z["konfiguration"]) for z in rows],
                         [(1,2,"erbe-s12"),(3,3,"erbe-s11"),(4,99,"erbe-s12"),(100,100,"erbe-s11")])
        wiederhergestellt = [(r,z["konfiguration"]) for z in rows for r in range(z["r_von"],z["r_bis"]+1)]
        self.assertEqual(wiederhergestellt,[(z["verhaeltnis"],z["konfiguration"]) for z in original])
        self.assertEqual(rows[0]["schwelle"],.6)
        self.assertEqual(rows[1]["schwelle"],.55)

    def test_luecken_und_doppelte_verhaeltnisse_werden_abgewiesen(self):
        original = self.auswahl()
        for falsch in (original[:-1],original+[original[0]],[]):
            with self.subTest(anzahl=len(falsch)), self.assertRaises(ValueError):
                list(b.schwellenwechsel(falsch))


def fixture(root):
    """Kleine erfundene Zähler, keine Generator- oder Produktionskontrollspuren."""
    dev, con = root/"entwicklung", root/"kontrolle"
    dev.mkdir(); con.mkdir()
    e = k.s.asdict(k.s.Einstellungen(takte=90))
    hashes = k.quellhashes()
    n = 2

    def basis(c):
        warn,treffer,vorgewarnt = {"immer":(50,20,2),"nie":(0,0,0),"fest":(10,8,2),"letzter":(5,4,1)}.get(c["modell"],(15,10,1))
        return dict(takte=60,auswertbar=50,warntakte=warn,treffertakte=treffer,zieltakte=20,
                    fehlwarntakte=warn-treffer,verpasste_zieltakte=20-treffer,
                    phasen=2,vorgewarnt=vorgewarnt,verpasst=2-vorgewarnt)

    def summen(configs):
        rows = []
        for f in ("alle",*k.s.FAMILIEN):
            for signal,_,_ in k.s.SIGNALE:
                for c in configs:
                    anzahl = n * (len(k.s.FAMILIEN) if f=="alle" else 1)
                    z = {feld:anzahl*wert for feld,wert in basis(c).items()}
                    rows.append(dict(familie=f,signal=signal,**c,schwelle=c["schwellenindex"]/20,
                                     spuren=anzahl,**z,**k.quoten(z)))
        return rows

    ds, cs = summen(k.alle_konfigurationen()), summen(k.defaults())
    k.csv_schreiben(dev/"summen.csv",ds)
    k.csv_schreiben(con/"summen.csv",cs)
    di = {(r["familie"],r["signal"],r["konfiguration"]):r for r in ds}
    ci = {(r["familie"],r["signal"],r["konfiguration"]):r for r in cs}
    aus = []
    for signal,_,_ in k.s.SIGNALE:
        for art in k.KOSTEN:
            for r in range(1,101):
                for suche in k.SUCHEN:
                    c = k.konfig("erbe") if suche=="erbe_schwelle" else k.konfig("startwert",6)
                    aus.append(dict(signal=signal,kostenmodell=art,verhaeltnis=r,suche=suche,**c,
                                    entwicklungskosten=k.kostenzahl(di["alle",signal,c["konfiguration"]],art,r)))
    a = dict(schema=1,tiebreakversion=1,quellhashes=hashes,einstellungen=e,
             entwicklung=dict(seedstart=900000,anzahl=n,summen_sha256=k.sha(dev/"summen.csv")),
             kontrolle=dict(seedstart=900100,anzahl=n),auswahl=aus)
    k.json_schreiben(dev/"auswahl.json",a)
    familien = []
    pruefung = []
    for f in ("alle",*k.s.FAMILIEN):
        for z in aus:
            if f!="alle":
                zz = dict(z,entwicklungskosten=k.kostenzahl(di[f,z["signal"],z["konfiguration"]],z["kostenmodell"],z["verhaeltnis"]))
                familien.append(dict(familie=f,**zz))
            pruefung.append(dict(familie=f,**z,kontrollkosten=k.kostenzahl(ci[f,z["signal"],z["konfiguration"]],z["kostenmodell"],z["verhaeltnis"])))
    k.csv_schreiben(dev/"familien-auswahl.csv",familien)
    k.csv_schreiben(con/"auswahl-pruefung.csv",pruefung)
    raw = []
    for f in k.s.FAMILIEN:
        for seed in range(900100,900100+n):
            for signal,_,_ in k.s.SIGNALE:
                for c in k.defaults():
                    raw.append(dict(familie=f,seed=seed,signal=signal,**c,schwelle=c["schwellenindex"]/20,**basis(c)))
    k.csv_schreiben(con/"einzel.csv",raw)
    for satz,ordner,seed in (("entwicklung",dev,900000),("kontrolle",con,900100)):
        m = dict(schema=1,status="vollstaendig",satz=satz,seedstart=seed,anzahl=n,spuren=8,
                 familien=list(k.s.FAMILIEN),einstellungen=e,quellhashes=hashes,
                 ergebnisse={p.name:k.sha(p) for p in ordner.iterdir()})
        if satz=="kontrolle": m["auswahl_sha256"] = k.sha(dev/"auswahl.json")
        k.json_schreiben(ordner/"manifest.json",m)
    return dev,con


class EingabeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        # Fixture-Metadaten bleiben unabhängig von gleichzeitig bearbeitetem Quellcode.
        self.patch = mock.patch.object(k,"quellhashes",return_value={"fixture":"0"*64})
        self.patch.start()
        self.dev,self.con = fixture(self.root)

    def tearDown(self):
        self.patch.stop()
        self.tmp.cleanup()

    def test_gepruefte_fixture_72_intervalle_und_baselines(self):
        d,c,a,ds,cs,configs = b.pruefe_eingaben(self.dev,self.con)
        jobs,paare = b.lese_paare(self.con,c,a,cs,configs)
        rows = list(b.intervalle(jobs,paare,c,wiederholungen=20))
        self.assertEqual(len(rows),72)
        self.assertTrue(all(r["differenz_pro_1000"]==r["untergrenze"]==r["obergrenze"]==0 for r in rows))
        text = b.bericht(d,c,a,ds,cs,rows)
        self.assertEqual(text.count("| Immer warnen |"),18)
        self.assertIn("nichtkritischen Takte, auch OK",text)
        self.assertEqual(len(list(b.halbwertsprofil(ds))),5*3*29)

    def test_dateiaenderung_und_falscher_auswahlhash_werden_abgewiesen(self):
        p = self.con/"einzel.csv"
        p.write_bytes(p.read_bytes()+b"\n")
        with self.assertRaises(ValueError): b.pruefe_eingaben(self.dev,self.con)
        p.write_bytes(p.read_bytes()[:-1])
        m = json.loads((self.con/"manifest.json").read_text())
        m["auswahl_sha256"] = "f"*64
        k.json_schreiben(self.con/"manifest.json",m)
        with self.assertRaises(ValueError): b.pruefe_eingaben(self.dev,self.con)

    def test_unvollstaendiges_manifest_wird_abgewiesen(self):
        m = json.loads((self.dev/"manifest.json").read_text())
        m["status"] = "unvollstaendig"
        k.json_schreiben(self.dev/"manifest.json",m)
        with self.assertRaises(ValueError): b.pruefe_eingaben(self.dev,self.con)

    def test_doppelte_rohspur_trotz_neuer_dateipruefsumme_wird_abgewiesen(self):
        p = self.con/"einzel.csv"
        zeilen = p.read_text().splitlines(keepends=True)
        p.write_text("".join(zeilen)+zeilen[1])
        m = json.loads((self.con/"manifest.json").read_text())
        m["ergebnisse"]["einzel.csv"] = k.sha(p)
        k.json_schreiben(self.con/"manifest.json",m)
        _,c,a,_,cs,configs = b.pruefe_eingaben(self.dev,self.con)
        with self.assertRaises(ValueError): b.lese_paare(self.con,c,a,cs,configs)

    def test_verschiedene_spurmerkmale_trotz_gleicher_summen_werden_abgewiesen(self):
        p = self.con/"einzel.csv"
        with p.open(newline="") as f:
            original = list(csv.DictReader(f))
        for feld,abgeleitet in (("auswertbar",None),("zieltakte","verpasste_zieltakte"),("phasen","verpasst")):
            with self.subTest(feld=feld):
                rows = [dict(row) for row in original]
                paar = [row for row in rows if row["familie"] == k.s.FAMILIEN[0]
                        and row["signal"] == "temperatur" and row["konfiguration"] == "erbe-s12"]
                self.assertEqual(len(paar),2)
                # Gegenläufige Änderungen halten sämtliche aggregierten Zähler exakt gleich.
                for row,delta in zip(paar,(1,-1)):
                    row[feld] = str(int(row[feld])+delta)
                    if abgeleitet: row[abgeleitet] = str(int(row[abgeleitet])+delta)
                k.csv_schreiben(p,rows)
                m = json.loads((self.con/"manifest.json").read_text())
                m["ergebnisse"]["einzel.csv"] = k.sha(p)
                k.json_schreiben(self.con/"manifest.json",m)
                _,c,a,_,cs,configs = b.pruefe_eingaben(self.dev,self.con)
                with self.assertRaisesRegex(ValueError,"unterschiedliche Kontrollspuren"):
                    b.lese_paare(self.con,c,a,cs,configs)

    def test_eingefrorene_wahl_mit_falschem_tiebreak_wird_abgewiesen(self):
        p = self.dev/"auswahl.json"
        a = json.loads(p.read_text())
        self.assertEqual(a["auswahl"][0]["konfiguration"],"erbe-s12")
        # Gleiche Entwicklungskosten aller Erbe-Schwellen: s12 ist der festgelegte Tiebreak.
        a["auswahl"][0].update(k.konfig("erbe",index=11))
        k.json_schreiben(p,a)
        m = json.loads((self.dev/"manifest.json").read_text())
        m["ergebnisse"]["auswahl.json"] = k.sha(p)
        k.json_schreiben(self.dev/"manifest.json",m)
        m = json.loads((self.con/"manifest.json").read_text())
        m["auswahl_sha256"] = k.sha(p)
        k.json_schreiben(self.con/"manifest.json",m)
        with self.assertRaisesRegex(ValueError,"Eingefrorene Entwicklungsauswahl verletzt"):
            b.pruefe_eingaben(self.dev,self.con)

    def test_familienwahl_mit_falschem_tiebreak_wird_abgewiesen(self):
        p = self.dev/"familien-auswahl.csv"
        with p.open(newline="") as f:
            rows = list(csv.DictReader(f))
        rows[0].update(k.konfig("erbe",index=11))
        k.csv_schreiben(p,rows)
        m = json.loads((self.dev/"manifest.json").read_text())
        m["ergebnisse"]["familien-auswahl.csv"] = k.sha(p)
        k.json_schreiben(self.dev/"manifest.json",m)
        with self.assertRaisesRegex(ValueError,"Familienweise Entwicklungsauswahl verletzt"):
            b.pruefe_eingaben(self.dev,self.con)

    def test_kommando_manifest_pruefsummen_und_ueberschreibschutz(self):
        out = self.root/"bericht"
        args = ["kostenbericht.py","--entwicklung",str(self.dev),"--kontrolle",str(self.con),"--ausgabe",str(out)]
        with mock.patch("sys.argv",args), contextlib.redirect_stdout(io.StringIO()): b.main()
        meta = json.loads((out/"manifest.json").read_text())
        self.assertEqual((meta["status"],meta["intervalle"]),("vollstaendig",72))
        self.assertEqual(meta["schwellenbereiche"],24)
        self.assertIn("schwellenwechsel.csv",meta["ergebnisse"])
        with (out/"schwellenwechsel.csv").open(newline="") as f:
            wechsel = list(csv.DictReader(f))
        self.assertEqual(len(wechsel),24)
        self.assertTrue(all(z["r_von"]=="1" and z["r_bis"]=="100" for z in wechsel))
        self.assertTrue(all(k.sha(out/name)==digest for name,digest in meta["ergebnisse"].items()))
        self.assertNotIn(str(self.root),(out/"manifest.json").read_text())
        vorher = (out/"manifest.json").read_bytes()
        with mock.patch("sys.argv",args), contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as raised:
            b.main()
        self.assertEqual(raised.exception.code,2)
        self.assertEqual(vorher,(out/"manifest.json").read_bytes())


if __name__ == "__main__":
    unittest.main()
