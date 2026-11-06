"""Verbindet bestätigte Knotenmeldungen mit fester Disposition und lokalen Aufträgen."""
import argparse
import json
import uuid
from dataclasses import asdict, replace
from pathlib import Path

from auftraege import Auftrag, Auftragsregister
from kern import Knoten, MAX_TAKT, REGELN
from systemkern import Arbeitsprozesse, disponiere
from verbund import Messknoten, Zentrale


class Verbundsystem:
    """Knoten 1 ist Primär, Knoten 2 Reserve. Gelernt wird ausschließlich dort.

    Der vertrauenswürdige Betreiber ordnet Sitzungen zu. Jeder lokale Zyklus
    fragt beide Knoten genau einmal ab. Nur neue Antworten aus dieser Runde
    gelten zur Arbeitsvergabe. Alle Methoden gehören in denselben Ereignisablauf.
    """

    def __init__(self, antwortfrist=.5, gueltigkeit=1, sitzung=None, kapazitaet=1024, *, register=None):
        if register is not None and (sitzung is not None or kapazitaet != 1024):
            raise ValueError("Sitzung und Kapazität gehören zum übergebenen Register.")
        self.hub = Zentrale([1, 2], antwortfrist, gueltigkeit)
        self.register = Auftragsregister(sitzung, kapazitaet) if register is None else register
        self.takt = 0
        self.offen = False
        self.auftrag = None
        self.bild = None
        self.vorher = None
        self.sitzungen = None

    def anmelden(self, nummer, sitzung=None):
        sitzung = self.hub.anmelden(nummer, sitzung)
        # Jede Neuzuordnung beendet den begonnenen Zyklus und seine Reserve.
        self.offen, self.vorher = False, None
        return sitzung

    def beginne(self, takt, jetzt):
        if type(takt) is not int or not self.takt < takt <= MAX_TAKT:
            raise ValueError("Zyklen müssen positiv und aufsteigend sein.")
        if set(self.hub.verbindungen) != {1, 2}:
            raise ValueError("Beide Knoten müssen zugeordnet sein.")
        if any(v.runde == MAX_TAKT for v in self.hub.verbindungen.values()):
            raise ValueError("Neue Knotensitzung erforderlich.")
        self.hub.zeit_pruefen(jetzt)
        fragen = {nr: self.hub.frage(nr, jetzt) for nr in (1, 2)}
        self.takt, self.offen, self.auftrag = takt, True, None
        self.sitzungen = tuple(self.hub.verbindungen[nr].sitzung for nr in (1, 2))
        return fragen

    def empfange(self, daten, jetzt):
        return self.hub.empfange(daten, jetzt)

    def _aktuell(self, jetzt):
        sichten = {}
        bild = []
        for nr in (1, 2):
            v = self.hub.verbindungen[nr]
            s = self.hub.sicht(nr, jetzt)
            neu = v.erledigt and v.meldung is not None and v.meldung.runde == v.runde
            sichten[nr] = s if neu and s.zustand is not None else None
            bild.append((v.sitzung, v.meldung.takt) if sichten[nr] is not None else None)
        return sichten, tuple(bild)

    def entscheide(self, jetzt):
        if not self.offen:
            raise ValueError("Kein offener, unverändert zugeordneter Zyklus.")
        sichten, bild = self._aktuell(jetzt)
        if self.auftrag is not None:
            return self.auftrag
        primaer, reserve = sichten[1], sichten[2]
        reserve_gesund = reserve is not None and reserve.zustand != "AUSFALL"
        bereit = False
        if self.vorher is not None and all(x is not None for x in bild):
            takt, reserviert, alt = self.vorher
            bereit = (takt == self.takt - 1 and reserviert == self.takt
                       and all(x is not None for x in alt)
                       and all(a[0] == b[0] and a[1] + 1 == b[1] for a, b in zip(alt, bild))
                       and reserve_gesund)
        plan = disponiere(self.takt, primaer.zustand if primaer else None,
                          primaer.vorwarnung if primaer else False, bereit)
        if not reserve_gesund:
            plan = replace(plan, reserve_fuer=None)
        self.bild = bild
        self.vorher = (self.takt, plan.reserve_fuer, bild)
        self.auftrag = Auftrag(self.register.sitzung, plan)
        return self.auftrag

    def ausfuehren(self, auftrag, jetzt, arbeiter):
        self.hub.zeit_pruefen(jetzt)
        bekannt = self.register.bekannt(auftrag)
        if bekannt is not None:
            return bekannt  # Nur Quittung zurückgeben; keine erneute Ausführung.
        if not self.offen or auftrag != self.auftrag:
            raise ValueError("Auftrag ist nicht die aktuelle Freigabe.")
        if auftrag.plan.ziel == "WARTEN":
            return self.register.ausfuehren(auftrag, arbeiter)
        sichten, bild = self._aktuell(jetzt)
        sitzungen = tuple(self.hub.verbindungen[nr].sitzung for nr in (1, 2))
        # Die Meldung, auf deren Grundlage entschieden wurde, muss bis zur
        # Übergabe an den lokalen Arbeiter gültig bleiben.
        benoetigt = (1, 2) if auftrag.plan.ziel == "RESERVE" else (1,)
        if sitzungen != self.sitzungen or any(sichten[nr] is None or bild[nr-1] != self.bild[nr-1] for nr in benoetigt):
            self.vorher = None
            return self.register.vermerken(auftrag, "VERFALLEN", "Freigabe vor Arbeitsbeginn veraltet")
        try:
            q = self.register.ausfuehren(auftrag, arbeiter)
        except BaseException:
            self.vorher = None
            raise
        if q.status == "UNGEKLAERT":
            self.vorher = None
        return q


def versuch():
    """Echte lokale Arbeiter, echte OC-Pakete, deterministisch gestörter In-Memory-Kanal."""
    system = Verbundsystem(sitzung=uuid.UUID(int=100).bytes)
    knoten, zaehler, zustaende = {}, {1: 0, 2: 10000}, {1: "OK", 2: "OK"}
    for nr in (1, 2):
        sitzung = system.anmelden(nr, uuid.UUID(int=nr).bytes)
        def quelle(nr=nr):
            zaehler[nr] += 1
            return zaehler[nr], zustaende[nr]
        knoten[nr] = Messknoten(nr, sitzung, Knoten(REGELN["erbe"]()), quelle)
    verlauf, letzte_antwort = [], None
    with Arbeitsprozesse() as arbeiter:
        def ausfuehren(auftrag):
            return arbeiter.ausfuehren(auftrag.plan, sitzung=auftrag.sitzung)
        for t, zustand in enumerate(("SCHWACH", "AUSFALL", "SCHWACH", "AUSFALL", "SCHWACH", "AUSFALL", "SCHWACH", "AUSFALL"), 1):
            zustaende[1] = zustand
            ablehnungen = []
            if t == 6:
                sitzung = system.anmelden(1, uuid.UUID(int=11).bytes)
                knoten[1] = Messknoten(1, sitzung, knoten[1].lernen, knoten[1].quelle)
            fragen = system.beginne(t, t * 2)
            if t == 6:
                ablehnungen.append(system.empfange(letzte_antwort, t * 2 + .05))
            for nr in (1, 2):
                antwort = knoten[nr].antwort(fragen[nr])
                if nr == 1:
                    letzte_antwort = antwort
                if t == 4 and nr == 2:
                    continue
                system.empfange(antwort, t * 2 + .1)
                ablehnungen.append(system.empfange(antwort, t * 2 + .1))
            auftrag = system.entscheide(t * 2 + .2)
            jetzt = t * 2 + (1 if t == 8 else .25)
            quittung = system.ausfuehren(auftrag, jetzt, ausfuehren)
            wiederholt = system.ausfuehren(auftrag, jetzt, ausfuehren)
            assert quittung == wiederholt
            verlauf.append(dict(takt=t, plan=asdict(auftrag.plan), quittung={**asdict(quittung), "sitzung": quittung.sitzung.hex()},
                                wiederholung_identisch=True, abgewiesen=ablehnungen))
    return dict(art="OC-Pakete über simulierten Kanal, zwei echte lokale Arbeiter",
                lernen="ausschließlich in den beiden sendenden Knoten", verlauf=verlauf)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", type=Path)
    args = parser.parse_args()
    daten = versuch()
    text = json.dumps(daten, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    if args.json:
        args.json.write_text(text, encoding="utf-8")
    for z in daten["verlauf"]:
        print(f'Takt {z["takt"]}: {z["plan"]["ziel"]}, {z["quittung"]["status"]}, Wiederholung bestätigt')


if __name__ == "__main__":
    main()
