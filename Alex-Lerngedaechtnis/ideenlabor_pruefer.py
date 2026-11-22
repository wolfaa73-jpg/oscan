"""Pruefer zuerst: Vertragsverletzungen werden unabhaengig vom Nutzen abgelehnt."""
from ideenlabor_basis import fordere


def eingabe(daten, plan):
    erlaubt = {"A": {"x"}, "B": {"wort", "x", "z"}}[plan]
    fordere(type(daten) is dict and set(daten) == erlaubt, "Verborgene oder fehlende Eingabefelder")
    fordere(type(daten["x"]) is int and daten["x"] in (0, 1), "Ungueltiges x")
    if plan == "B":
        fordere(daten["wort"] == "KNAPP" and type(daten["z"]) is int and
                daten["z"] in (0, 1), "Ungueltiges Wort oder z")


def a_beleg(ereignis, x, a, y):
    eingabe(ereignis["eingabe"], "A")
    fordere(ereignis["eingabe"]["x"] == x, "Andere aeussere Aufgabe")
    fordere(ereignis["belege"] == [(x, a, y)], "Erfundene Gegenbeobachtung")
    fordere(ereignis["rettungen"] == 0, "Erfolg ist kein beobachteter Rettungsbeleg")
    fordere(ereignis["kosten"] == a + 5*y, "Unvollstaendige Handlungskosten")


def a_vollstaendig(ereignisse, anzahl, stoerungen):
    fordere(len(ereignisse) == anzahl and all(e["gewertet"] for e in ereignisse),
            "Aufgabe aus Nenner entfernt")
    fordere([i+1 for i, e in enumerate(ereignisse) if e["gestoert"]] == list(stoerungen),
            "Stoerungen haengen vom Verfahren ab")


def b_reihenfolge(phasen, daten):
    eingabe(daten, "B")
    fordere(phasen == ("eingabe", "prognose", "ausgang", "lernen"),
            "Ausgang vor Vorhersage oder fehlendes Lernen")


def b_wahl(wahl, eingefroren, runde):
    if runde >= 257:
        fordere(wahl == eingefroren, "Wortstruktur nach Auswahl geaendert")


def b_speicher(abbild, gemeldet):
    fordere(type(abbild) is bytes and len(abbild) <= 512, "B-Zustandsbudget verletzt")
    fordere(gemeldet == len(abbild), "Suchspeicher unterschlagen")


def b_globalfenster(vorher, nachher, beobachtung):
    fordere(nachher == (vorher + [beobachtung])[-128:], "Neue Erfahrung nicht kausal gespeichert")


def c_zustand(zustand, budget):
    fordere(type(zustand) is bytes, "Zusatzspeicher ausserhalb des Abbilds")
    fordere(len(zustand) <= budget, "C-Zustandsbudget verletzt")


def c_rekonstruktion(rekonstruiert, wahrheit):
    for nummer, wert in rekonstruiert.items():
        fordere(nummer in wahrheit and wert == wahrheit[nummer],
                "Erfundener oder falsch rekonstruierter historischer Beleg")


def c_antwort(art, nummer, antwort, wahrheit, widerrufe, belegbare_ids=None):
    if art == "zukunft":
        fordere(antwort == "UNBEKANNT" or (type(antwort) is int and antwort in (0,1)), "Ungueltige Zukunftsantwort")
        return
    if nummer in widerrufe:
        fordere(antwort == "WIDERRUFEN", "Widerrufener Beleg weiter gueltig")
    elif antwort != "UNBEKANNT":
        if belegbare_ids is not None:
            fordere(nummer in belegbare_ids, "Antwort greift auf nicht gespeicherten Beleg zu")
        feld = 2 if art == "historie" else 1
        fordere(nummer in wahrheit and antwort == wahrheit[nummer][feld],
                "Erfundener historischer Inhalt oder Herkunft")


def c_prognose(antwort,frage,typ,belege,zaehler,widerrufe):
    """Unabhaengige Abfrage-Oracle ausschliesslich aus dem uebergebenen Bild."""
    if typ>=4:
        erwartet="UNBEKANNT" if typ==4 else (0 if typ==5 else 1)
    else:
        x,q=frage
        if typ in (2,3):
            null,eins=zaehler[4*x+2*q:4*x+2*q+2]
        else:
            ys=[v[2] for i,v in belege.items() if i not in widerrufe and v[:2]==(x,q)]
            null=ys.count(0); eins=ys.count(1)
        erwartet="UNBEKANNT" if null+eins==0 else int(eins>null)
    fordere(antwort==erwartet,"Prognose folgt nicht dem gespeicherten Belegbestand")
