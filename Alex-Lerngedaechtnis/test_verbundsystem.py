import copy
import hashlib
import unittest
import uuid
from dataclasses import replace

from auftraege import Auftrag, Auftragsregister
from kern import Knoten, MAX_TAKT, REGELN
from systemkern import Arbeitsprozesse, disponiere
from verbund import Messknoten, Paket, MELDUNG
from verbundsystem import Verbundsystem, versuch


def ergebnis(plan):
    return hashlib.sha256(f"OSCan-Auftrag:{plan.takt}".encode("ascii")).hexdigest()


class RegisterTests(unittest.TestCase):
    def setUp(self):
        self.register = Auftragsregister(uuid.UUID(int=101).bytes, kapazitaet=2)
        self.auftrag = Auftrag(self.register.sitzung, disponiere(1, "OK", False, False))
        self.aufrufe = 0

    def arbeiter(self, auftrag):
        self.aufrufe += 1
        return ergebnis(auftrag.plan)

    def test_wiederholungen_fuehren_genau_einmal_aus(self):
        a = self.register.ausfuehren(self.auftrag, self.arbeiter)
        for _ in range(100):
            self.assertEqual(a, self.register.ausfuehren(self.auftrag, self.arbeiter))
        self.assertEqual((a.status, self.aufrufe), ("ERLEDIGT", 1))

    def test_gleiche_kennung_mit_anderem_ziel_ist_konflikt(self):
        self.register.ausfuehren(self.auftrag, self.arbeiter)
        falsch = replace(self.auftrag, plan=replace(self.auftrag.plan, ziel="RESERVE"))
        with self.assertRaises(ValueError):
            self.register.ausfuehren(falsch, self.arbeiter)
        self.assertEqual(self.aufrufe, 1)

    def test_verlorene_quittung_wird_nicht_durch_neue_arbeit_repariert(self):
        def verloren(auftrag):
            self.arbeiter(auftrag)
            raise TimeoutError("Wirkung bereits erfolgt, Antwort verloren")
        a = self.register.ausfuehren(self.auftrag, verloren)
        self.assertEqual(a.status, "UNGEKLAERT")
        self.assertEqual(self.register.ausfuehren(self.auftrag, self.arbeiter), a)
        self.assertEqual(self.aufrufe, 1)

    def test_falsches_ergebnis_ist_ungeklaert(self):
        a = self.register.ausfuehren(self.auftrag, lambda p: "falscher Auftrag")
        self.assertEqual(a.status, "UNGEKLAERT")
        self.assertEqual(self.register.ausfuehren(self.auftrag, self.arbeiter), a)
        self.assertEqual(self.aufrufe, 0)

    def test_erneuter_aufruf_waehrend_arbeit_wird_nicht_ausgefuehrt(self):
        def reentrant(auftrag):
            q = self.register.ausfuehren(self.auftrag, self.arbeiter)
            self.assertEqual(q.status, "IN_ARBEIT")
            return self.arbeiter(auftrag)
        self.assertEqual(self.register.ausfuehren(self.auftrag, reentrant).status, "ERLEDIGT")
        self.assertEqual(self.aufrufe, 1)

    def test_unterbrechung_bleibt_ungeklaert(self):
        def abbruch(plan):
            raise KeyboardInterrupt
        with self.assertRaises(KeyboardInterrupt):
            self.register.ausfuehren(self.auftrag, abbruch)
        self.assertEqual(self.register.ausfuehren(self.auftrag, self.arbeiter).status, "UNGEKLAERT")
        self.assertEqual(self.aufrufe, 0)

    def test_volles_register_vergisst_keine_kennung(self):
        for t in (1, 2):
            a = replace(self.auftrag, plan=replace(self.auftrag.plan, takt=t))
            self.register.ausfuehren(a, self.arbeiter)
        with self.assertRaises(OverflowError):
            self.register.ausfuehren(replace(self.auftrag, plan=replace(self.auftrag.plan, takt=3)), self.arbeiter)
        self.register.ausfuehren(self.auftrag, self.arbeiter)
        self.assertEqual((len(self.register.eintraege), self.aufrufe), (2, 2))

    def test_neues_register_lehnt_alte_sitzung_ab(self):
        with self.assertRaises(ValueError):
            Auftragsregister().ausfuehren(self.auftrag, self.arbeiter)
        self.assertEqual(self.aufrufe, 0)

    def test_arbeiterantwort_aus_anderer_sitzung_wird_abgewiesen(self):
        auftrag = self.auftrag
        class AlterKanal:
            def send(self, daten):
                self.gesendet = daten
            def poll(self, frist):
                return True
            def recv(self):
                return ((uuid.UUID(int=999).bytes, auftrag.plan.takt), ergebnis(auftrag.plan))
        arbeiter = Arbeitsprozesse()
        kanal = AlterKanal()
        arbeiter.arbeiter = {"PRIMAER": (kanal, None)}
        with self.assertRaises(ValueError):
            arbeiter.ausfuehren(auftrag.plan, sitzung=auftrag.sitzung)
        self.assertEqual(kanal.gesendet[0], (auftrag.sitzung, auftrag.plan.takt))

    def test_warten_hat_keine_wirkung(self):
        a = replace(self.auftrag, plan=disponiere(1, None, False, False))
        self.assertEqual(self.register.ausfuehren(a, self.arbeiter).status, "AUSGESETZT")
        self.assertEqual(self.aufrufe, 0)


class AnschlussTests(unittest.TestCase):
    def setUp(self):
        self.system = Verbundsystem()
        self.zaehler = {1: 0, 2: 10000}
        self.zustaende = {1: "OK", 2: "OK"}
        self.knoten = {}
        self.aufrufe = 0
        for nr in (1, 2):
            s = self.system.anmelden(nr)
            def quelle(nr=nr):
                self.zaehler[nr] += 1
                return self.zaehler[nr], self.zustaende[nr]
            self.knoten[nr] = Messknoten(nr, s, Knoten(REGELN["erbe"]()), quelle)

    def arbeiter(self, auftrag):
        self.aufrufe += 1
        return ergebnis(auftrag.plan)

    def runde(self, t, primaer, reserve="OK", verlust=()):
        self.zustaende = {1: primaer, 2: reserve}
        fragen = self.system.beginne(t, t * 2)
        self.antworten = {}
        for nr in (1, 2):
            a = self.knoten[nr].antwort(fragen[nr])
            self.antworten[nr] = a
            if nr not in verlust:
                self.assertEqual(self.system.empfange(a, t * 2 + .1), "ANGENOMMEN")
        return self.system.entscheide(t * 2 + .2)

    def test_bestaetigte_warnung_steuert_reserve_mit_getrennten_uhren(self):
        self.runde(1, "SCHWACH")
        a = self.runde(2, "AUSFALL")
        self.assertEqual(a.plan.ziel, "RESERVE")
        self.assertEqual(self.system.ausfuehren(a, 4.3, self.arbeiter).status, "ERLEDIGT")
        self.assertEqual(self.aufrufe, 1)

    def test_empfang_und_disposition_lernen_nicht_erneut(self):
        a = self.runde(1, "SCHWACH")
        vorher = copy.deepcopy(self.knoten[1].lernen.gedaechtnis.gewichte)
        for _ in range(10):
            self.assertEqual(self.system.empfange(self.antworten[1], 2.2), "DOPPELT")
            self.assertEqual(self.system.entscheide(2.2), a)
            self.system.ausfuehren(a, 2.2, self.arbeiter)
        self.assertEqual(self.knoten[1].lernen.gedaechtnis.gewichte, vorher)
        self.assertEqual((self.zaehler[1], self.aufrufe), (1, 1))

    def test_alte_sicht_reicht_trotz_gueltiger_ttl_nicht_fuer_neue_runde(self):
        self.system.hub.gueltigkeit = 10
        self.runde(1, "SCHWACH")
        a = self.runde(2, "AUSFALL", verlust=(1,))
        self.assertEqual(self.system.hub.sicht(1, 4.2).zustand, "SCHWACH")
        self.assertIsNone(a.plan.zustand)
        self.assertEqual(self.system.ausfuehren(a, 4.3, self.arbeiter).status, "AUSGESETZT")
        self.assertEqual(self.aufrufe, 0)

    def test_fehlende_oder_ausgefallene_reserve_wird_nicht_beauftragt(self):
        for reserve, verlust in (("OK", (2,)), ("AUSFALL", ())):
            self.setUp()
            self.runde(1, "SCHWACH")
            a = self.runde(2, "AUSFALL", reserve, verlust)
            self.assertEqual((a.plan.ziel, a.plan.reserve_fuer), ("WARTEN", None))

    def test_sprung_der_messuhr_verwirft_vorsorge(self):
        self.runde(1, "SCHWACH")
        self.zaehler[1] += 1
        self.assertEqual(self.runde(2, "AUSFALL").plan.ziel, "WARTEN")

    def test_sprung_des_dispositionstakts_verwirft_vorsorge(self):
        self.runde(1, "SCHWACH")
        self.assertEqual(self.runde(3, "AUSFALL").plan.ziel, "WARTEN")

    def test_neuzuordnung_verwirft_vorsorge_und_alte_pakete(self):
        self.runde(1, "SCHWACH")
        alt = self.antworten[1]
        s = self.system.anmelden(1)
        k = self.knoten[1]
        self.knoten[1] = Messknoten(1, s, k.lernen, k.quelle)
        a = self.runde(2, "AUSFALL")
        self.assertEqual(self.system.empfange(alt, 4.2), "ALTE_SITZUNG")
        self.assertEqual(a.plan.ziel, "WARTEN")

    def test_neuzuordnung_nach_plan_verhindert_erste_ausfuehrung(self):
        a = self.runde(1, "OK")
        self.system.anmelden(2)
        with self.assertRaises(ValueError):
            self.system.ausfuehren(a, 2.3, self.arbeiter)
        self.assertEqual(self.aufrufe, 0)

    def test_frist_wird_vor_arbeitsbeginn_erneut_geprueft(self):
        a = self.runde(1, "OK")
        q = self.system.ausfuehren(a, 3, self.arbeiter)
        self.assertEqual(q.status, "VERFALLEN")
        self.assertEqual(self.system.ausfuehren(a, 3.1, self.arbeiter), q)
        self.assertEqual(self.aufrufe, 0)

    def test_erledigte_arbeit_liefert_nach_ablauf_nur_die_quittung(self):
        a = self.runde(1, "OK")
        q = self.system.ausfuehren(a, 2.3, self.arbeiter)
        self.assertEqual(self.system.ausfuehren(a, 5, self.arbeiter), q)
        self.assertEqual(self.aufrufe, 1)

    def test_alter_unbenutzter_auftrag_und_geaenderter_plan_werden_abgewiesen(self):
        alt = self.runde(1, "OK")
        neu = self.runde(2, "OK")
        for a in (alt, replace(neu, plan=replace(neu.plan, ziel="RESERVE"))):
            with self.assertRaises(ValueError):
                self.system.ausfuehren(a, 4.3, self.arbeiter)
        self.assertEqual(self.aufrufe, 0)

    def test_zaehlerende_und_ungueltiger_zyklus_aendern_keine_runden(self):
        self.runde(1, "OK")
        vorher = [v.runde for v in self.system.hub.verbindungen.values()]
        with self.assertRaises(ValueError):
            self.system.beginne(1, 3)
        self.assertEqual([v.runde for v in self.system.hub.verbindungen.values()], vorher)
        self.system.hub.verbindungen[2].runde = MAX_TAKT
        with self.assertRaises(ValueError):
            self.system.beginne(2, 4)
        self.assertEqual(self.system.hub.verbindungen[1].runde, vorher[0])

    def test_mehrtakt_prognose_wird_nicht_stillschweigend_eingefuehrt(self):
        with self.assertRaises(ValueError):
            disponiere(1, "TEMP_HOCH", True, False)
        with self.assertRaises(ValueError):
            disponiere(1, "SCHWACH", 30, False)

    def test_gemeinsamer_versuch_mit_echten_arbeitern(self):
        daten = versuch()
        self.assertEqual([z["quittung"]["status"] for z in daten["verlauf"]],
                         ["ERLEDIGT", "ERLEDIGT", "ERLEDIGT", "AUSGESETZT", "ERLEDIGT", "AUSGESETZT", "ERLEDIGT", "VERFALLEN"])
        self.assertIn("ALTE_SITZUNG", daten["verlauf"][5]["abgewiesen"])


if __name__ == "__main__":
    unittest.main()
