"""Gemeinsame, kernunabhängige Grenzen des Ideenlabors (Planfassung 0.3)."""
import hashlib
import subprocess
from pathlib import Path

NAMENSRAUM = "OSCAN-IDEEN-v2"
_KONTROLLE = False
QUELLDATEIEN = ("ideenlabor.py", "ideenlabor_basis.py", "ideenlabor_pruefer.py",
               "ideenlabor_a.py", "ideenlabor_b.py", "ideenlabor_c.py",
               "test_ideenlabor_pruefer.py", "test_ideenlabor.py",
               "test_ideenlabor_c.py", "IDEEN-DANIEL.md")

class Prueffehler(ValueError):
    """Ein vorab festgelegter Vertrag wurde verletzt."""


def fordere(bedingung, meldung):
    if not bedingung:
        raise Prueffehler(meldung)


def ziehung(plan, satz, seed, familie, runde, feld, n):
    fordere(satz in ("entwicklung", "pruefung", "test"), "Unbekannter Datensatz")
    fordere(satz != "pruefung" or _KONTROLLE,
            "Pruefsatz bleibt bis zum verifizierten Freeze-Commit gesperrt")
    fordere(plan in ("B", "C") and type(seed) is int and seed >= 0,
            "Ungueltiger Ziehungsbezeichner")
    fordere(type(n) is int and 0 < n <= 2**256, "Ungueltiger Ziehungsbereich")
    for value in (familie, feld):
        fordere(isinstance(value, str) and "|" not in value, "Ungueltiges Feld")
    versuch = 0
    grenze = (2**256 // n) * n
    while True:
        text = f"{NAMENSRAUM}|{plan}|{satz}|{seed}|{familie}|{runde}|{feld}|{versuch}"
        wert = int.from_bytes(hashlib.sha256(text.encode("utf-8")).digest(), "big")
        if wert < grenze:
            return wert % n
        versuch += 1


def quellhashes():
    basis = Path(__file__).resolve().parent
    return {name: hashlib.sha256((basis / name).read_bytes()).hexdigest()
            for name in QUELLDATEIEN}


def pruefung_freigeben(commit):
    """Nur identischer, vorher committeter Code darf Kontrollziehungen erzeugen."""
    global _KONTROLLE
    fordere(isinstance(commit, str) and len(commit) == 40 and
            all(c in "0123456789abcdef" for c in commit), "Vollstaendiger Freeze-Hash erforderlich")
    basis = Path(__file__).resolve().parent
    for name in QUELLDATEIEN:
        result = subprocess.run(["git", "show", f"{commit}:Alex-Lerngedaechtnis/{name}"],
                                cwd=basis, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        fordere(result.returncode == 0, "Freeze enthaelt nicht alle Quelldateien")
        fordere(result.stdout == (basis / name).read_bytes(),
                "Quellstand weicht vom Freeze-Commit ab")
    _KONTROLLE = True
    return commit
