#pragma once
#include "../Lernknoten/Vorhersage.h"
#include "../Lernknoten/Empfinden.h"
#include "../Lernknoten/Fahrt.h"
#include "../Lernknoten/Reize.h"
#include "../Gemeinsam/EmpfindenPaket.h"

// Das Display als eigenes Wesen: Es sagt seine eigene Chiptemperatur voraus, empfindet daraus und zeigt
// das im eigenen Gesicht. Kein Funk, kein zweiter Knoten. Gerechnet wird mit denselben Bausteinen wie im
// Lernknoten (Vorhersage.h, Empfinden.h) und in derselben Reihenfolge wie dort in koerperTakt. Dieser Teil
// kennt kein Display und keinen Flash, damit ihn der Rechner gegen selbstvorhersage.py und empfinden.py
// prüfen kann.
//
// Eigene Last ist hier die Hintergrundbeleuchtung: Lichtplan schaltet sie zwischen zwei Helligkeiten, in
// zufälligen Abständen wie die Rechenlast des Knotens (Lastplan aus Reize.h, 60 bis 240 Takte). Ob das
// Licht den Chip messbar wärmt, ist beim Schreiben nicht gemessen.
struct Lichtplan {
    static const uint32_t hoechstens = 240;  // gesetzt, wie LAST 240 240 im Fahrtmodus des Knotens
    Lastplan plan;
    uint32_t rest = 0;
    bool hell = false;
    void starte(uint32_t saat) {
        plan.zufall = saat ? saat : 1;
        hell = false;
        rest = plan.dauer(hoechstens);
    }
    // Einmal je Takt, nach der Messung. Liefert, ob der nächste Takt hell ist.
    bool weiter() {
        if (!rest) {
            hell = !hell;
            rest = plan.dauer(hoechstens);
        }
        --rest;
        return hell;
    }
};

struct Selbst {
    static const unsigned standBytes = sizeof(Selbstvorhersage) + Empfinden::standBytes;
    static const unsigned pause = 127;  // Neustartgrund im Satz, wenn kein Chipneustart, sondern FAHRTLEER voranging
    Selbstvorhersage vorhersage;
    Empfinden empfinden;
    uint32_t takt = 0;
    bool erster = true, beiNull = true;

    void beginne(uint32_t ab = 0) {
        vorhersage.starte();
        empfinden.starte();
        takt = ab;
        erster = beiNull = true;
    }
    void exportiere(uint8_t *p) const {
        vorhersage.exportiere(p);
        empfinden.exportiere(p + sizeof(Selbstvorhersage));
    }
    // Nach dem Einschalten mit gesichertem Stand. Passt er nicht, beginnt alles bei null.
    bool importiere(const uint8_t *p, uint32_t gesichertBis) {
        if (!vorhersage.importiere(p) || !empfinden.importiere(p + sizeof(Selbstvorhersage))
            || !empfinden.aktiv()) {
            beginne(gesichertBis);
            return false;
        }
        empfinden.neustart();
        takt = gesichertBis;
        erster = true;
        beiNull = false;
        return true;
    }
    // Ein Takt nach der Messung. satz bekommt FahrtV2::bytes Byte für das Protokoll. Schmerz gibt es hier
    // noch nicht: Für diesen Chip sind keine Grenzen gemessen, also steht der Zustand immer auf 0.
    EmpfindenPaket::Zustand schritt(bool gueltig, int32_t temp, bool last, unsigned grund, bool voll, uint8_t *satz) {
        ++takt;
        vorhersage.takt(takt, gueltig, temp, last);
        empfinden.takt(takt, gueltig, temp, vorhersage.hatFehler(), vorhersage.mittel());
        Fahrtsatz::packe(satz, takt, gueltig, temp, last, vorhersage.ueberrascht(), false, false, 0, erster, grund,
                         beiNull, vorhersage.vKurz(), vorhersage.vLang(), vorhersage.hatFehler(),
                         vorhersage.mittel(), vorhersage.grenze());
        if (gueltig && !empfinden.anlauf()) Fahrtsatz::empfinden(satz, empfinden.gerade(), empfinden.woanders());
        FahrtV2::reize(satz, last ? 1u : 0u);
        erster = false;
        EmpfindenPaket::Zustand z;
        z.takt = takt;
        z.temp = gueltig && temp >= -1000 && temp <= 2000 ? static_cast<int16_t>(temp) : -32768;
        z.gerade = static_cast<int8_t>(empfinden.gerade());
        z.woanders = static_cast<int8_t>(empfinden.woanders());
        const bool auffaellig = empfinden.gerade() <= -2 || empfinden.gerade() >= 2;
        z.bits = (empfinden.anlauf() ? EmpfindenPaket::ANLAUF : 0) | (auffaellig ? EmpfindenPaket::UEBERRASCHT : 0)
               | (voll ? EmpfindenPaket::VOLL : 0);
        return z;
    }
};
