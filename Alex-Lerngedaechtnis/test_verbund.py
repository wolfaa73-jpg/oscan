import math
import random
import unittest
import uuid

from kern import Knoten, REGELN, MAX_TAKT
from verbund import CRC, KOPF, FRAGE, MELDUNG, Messknoten, Paket, Zentrale
from verbundlabor import simulation

SITZUNG = uuid.UUID("00112233-4455-6677-8899-aabbccddeeff").bytes


class ProtokollTests(unittest.TestCase):
    def setUp(self):
        self.hub = Zentrale([1, 2], antwortfrist=1, gueltigkeit=3)
        self.hub.anmelden(1, SITZUNG)
        self.messungen = 0
        def quelle():
            self.messungen += 1
            return self.messungen, "SCHWACH"
        self.knoten = Messknoten(1, SITZUNG, Knoten(REGELN["erbe"]()), quelle)

    def test_vollstaendige_anfrage_und_getrennte_lokale_uhr(self):
        frage = self.hub.frage(1, 10000)
        antwort = self.knoten.antwort(frage)
        self.assertEqual(self.hub.empfange(antwort, 10000.1), "ANGENOMMEN")
        sicht = self.hub.sicht(1, 10000.2)
        self.assertEqual((sicht.zustand, sicht.takt, sicht.vorwarnung), ("SCHWACH", 1, True))

    def test_wiederholung_lernt_nicht_doppelt(self):
        frage = self.hub.frage(1, 1)
        antwort = self.knoten.antwort(frage)
        self.assertEqual(self.knoten.antwort(frage), antwort)
        self.assertEqual(self.messungen, 1)
        self.assertEqual(self.hub.empfange(antwort, 1.1), "ANGENOMMEN")
        self.assertEqual(self.hub.empfange(antwort, 1.2), "DOPPELT")
        self.assertAlmostEqual(self.hub.sicht(1, 1.3).alter, 0.3)

    def test_verzoegerte_antwort_verjuengt_das_wissen_nicht(self):
        frage = self.hub.frage(1, 1)
        self.hub.empfange(self.knoten.antwort(frage), 1.9)
        self.assertEqual(self.hub.sicht(1, 3.99).zustand, "SCHWACH")
        self.assertEqual(self.hub.sicht(1, 4).grund, "VERALTET")

    def test_genau_auf_der_antwortfrist_wird_abgewiesen(self):
        frage = self.hub.frage(1, 1)
        self.assertEqual(self.hub.empfange(self.knoten.antwort(frage), 2), "ZU_SPAET")
        self.assertIsNone(self.hub.sicht(1, 2).zustand)

    def test_alte_runde_und_eigener_messtakt(self):
        alt = self.knoten.antwort(self.hub.frage(1, 1))
        neu = self.knoten.antwort(self.hub.frage(1, 2))
        self.assertIsNone(self.knoten.antwort(Paket(FRAGE, 1, SITZUNG, 1).kodieren()))
        self.assertEqual(self.hub.empfange(alt, 2.1), "ALTE_RUNDE")
        self.assertEqual(self.hub.empfange(neu, 2.2), "ANGENOMMEN")
        self.hub.frage(1, 3)
        alter_messwert = Paket(MELDUNG, 1, SITZUNG, 3, 2, 1, 0).kodieren()
        self.assertEqual(self.hub.empfange(alter_messwert, 3.1), "ALTER_MESSWERT")

    def test_neustart_eines_knotens_verwirft_alte_pakete(self):
        alt = self.knoten.antwort(self.hub.frage(1, 1))
        sitzung = self.hub.anmelden(1)
        neu = Messknoten(1, sitzung, Knoten(REGELN["erbe"]()), lambda: (1, "OK"))
        antwort = neu.antwort(self.hub.frage(1, 2))
        self.assertEqual(self.hub.empfange(alt, 2.1), "ALTE_SITZUNG")
        self.assertEqual(self.hub.empfange(antwort, 2.2), "ANGENOMMEN")
        self.assertEqual(self.hub.sicht(1, 2.3).takt, 1)

    def test_zentrale_nach_neustart_glaubt_alten_paketen_nicht(self):
        alt = self.knoten.antwort(self.hub.frage(1, 1))
        hub = Zentrale([1])
        hub.anmelden(1)
        hub.frage(1, 2)
        self.assertEqual(hub.empfange(alt, 2.1), "ALTE_SITZUNG")
        self.assertIsNone(hub.sicht(1, 2.2).zustand)

    def test_fremder_knoten_oder_falsche_sitzung_erzeugt_keine_messung(self):
        for paket in (Paket(FRAGE, 2, SITZUNG, 1),
                      Paket(FRAGE, 1, uuid.uuid4().bytes, 1)):
            self.assertIsNone(self.knoten.antwort(paket.kodieren()))
        self.assertEqual(self.messungen, 0)
        fremd = Paket(MELDUNG, 99, SITZUNG, 1, 1, 1, 0).kodieren()
        self.assertEqual(self.hub.empfange(fremd, 1), "UNBEKANNT")
        self.assertEqual(len(self.hub.verbindungen), 1)

    def test_sitzungen_nicht_wiederverwenden(self):
        with self.assertRaises(ValueError):
            self.hub.anmelden(2, SITZUNG)
        with self.assertRaises(ValueError):
            self.hub.anmelden(3)

    def test_beschaedigte_bits_veraendern_keinen_empfaengerstand(self):
        frage = self.hub.frage(1, 1)
        daten = self.knoten.antwort(frage)
        for byte in range(len(daten)):
            for bit in range(8):
                falsch = bytearray(daten)
                falsch[byte] ^= 1 << bit
                self.assertEqual(self.hub.empfange(bytes(falsch), 1.1), "UNGUELTIG")
        self.assertIsNone(self.hub.sicht(1, 1.2).zustand)
        self.assertEqual(self.hub.empfange(daten, 1.3), "ANGENOMMEN")

    def test_ungueltige_felder(self):
        for daten in (b"", b"x"*35, b"x"*37, "kein Bytepaket"):
            with self.assertRaises(ValueError):
                Paket.lesen(daten)
        for paket in (Paket(FRAGE, 1, SITZUNG, 1, 5),
                      Paket(MELDUNG, 1, SITZUNG, 1, 0, 1),
                      Paket(MELDUNG, 1, SITZUNG, 1, 1, 3, 1),
                      Paket(MELDUNG, 1, SITZUNG, 1, 1, 1, 2),
                      Paket(FRAGE, True, SITZUNG, 1),
                      Paket(FRAGE, 1, b"\x00"*16, 1)):
            with self.assertRaises(ValueError):
                paket.kodieren()

    def test_monotone_zeit_und_zaehlerueberlauf(self):
        self.hub.frage(1, 5)
        for zeit in (4, math.nan, math.inf):
            with self.assertRaises(ValueError):
                self.hub.frage(1, zeit)
        self.hub.verbindungen[1].runde = MAX_TAKT
        with self.assertRaises(ValueError):
            self.hub.frage(1, 6)
        self.assertEqual(self.hub.verbindungen[1].runde, MAX_TAKT)

    def test_knoten_bleiben_unabhaengig(self):
        sitzung2 = self.hub.anmelden(2)
        knoten2 = Messknoten(2, sitzung2, Knoten(REGELN["zeit"]()), lambda: (999, "AUSFALL"))
        frage1, frage2 = self.hub.frage(1, 1), self.hub.frage(2, 1)
        self.hub.empfange(knoten2.antwort(frage2), 1.1)
        self.hub.empfange(self.knoten.antwort(frage1), 1.2)
        self.assertEqual(self.hub.sicht(1, 1.3).zustand, "SCHWACH")
        self.assertEqual(self.hub.sicht(2, 1.3).zustand, "AUSFALL")


class VersuchsTests(unittest.TestCase):
    def test_stoerungen_und_neuzuordnung(self):
        d = simulation()
        self.assertEqual(d["statistik"]["ANGENOMMEN"], 112)
        self.assertEqual(d["statistik"]["MODELL_NUTZBYTES"], 8568)
        for t in range(15, 19):
            self.assertEqual(d["verlauf"][t-1]["knoten"][0]["sicht"]["grund"], "VERALTET")
            self.assertIsNotNone(d["verlauf"][t-1]["knoten"][1]["sicht"]["zustand"])
        self.assertIsNotNone(d["verlauf"][18]["knoten"][0]["sicht"]["zustand"])
        self.assertEqual(simulation(), d)

    def test_zufaellige_verzoegerung_duplikate_und_ausfaelle(self):
        # Jede Antwort über ihrer Frist wird auch als zeitlich letztes Paket eingespielt.
        # Sie darf einen ausgelaufenen Zustand niemals wiederbeleben.
        for seed in range(40):
            rng = random.Random(seed)
            hub = Zentrale([1, 2], antwortfrist=.5, gueltigkeit=1)
            knoten = {}
            zaehler = {1: 0, 2: 0}
            for nr in (1, 2):
                s = hub.anmelden(nr)
                def quelle(nr=nr):
                    zaehler[nr] += 1
                    return zaehler[nr], "OK" if nr == 1 else "AUSFALL"
                knoten[nr] = Messknoten(nr, s, Knoten(REGELN["erbe"]()), quelle)
            for runde in range(1, 41):
                zeit = runde * 2
                fragen = {nr: hub.frage(nr, zeit) for nr in (1, 2)}
                lieferungen = []
                for nr in (1, 2):
                    antwort = knoten[nr].antwort(fragen[nr])
                    if rng.random() < .2:
                        continue
                    verzoegerung = rng.choice((.1, .4, .6, 1.2))
                    lieferungen.append((zeit+verzoegerung, nr, antwort))
                for jetzt, nr, antwort in sorted(lieferungen):
                    ergebnis = hub.empfange(antwort, jetzt)
                    self.assertEqual(ergebnis, "ANGENOMMEN" if jetzt-zeit < .5 else "ZU_SPAET")
                    self.assertIn(hub.empfange(antwort, jetzt), ("DOPPELT", "ZU_SPAET"))
                for nr in (1, 2):
                    self.assertIsNone(hub.sicht(nr, zeit+1.5).zustand)


if __name__ == "__main__":
    unittest.main()
