#pragma once
#include <stdint.h>
#include "Knoten.h"

// Grenzen kommen per GRENZEN vom Rechner, die Firmware hat keine eigenen.
// Temperatur in Zehntelgrad, freier Speicher in Byte, Schleifenlücke in Mikrosekunden.
struct Grenzen {
    int32_t tempSchwach, tempAusfall;
    uint32_t heapSchwach, heapAusfall, lueckeSchwach, lueckeAusfall;
    bool gueltig() const {
        return tempSchwach < tempAusfall && heapSchwach > heapAusfall && lueckeSchwach < lueckeAusfall;
    }
};

// Wie einstufen in koerper.py: Der schlechteste Wert zählt. Eine nicht lesbare
// Temperatur geht nicht ein, sie steht in der Ausgabe als "-".
inline Zustand einstufen(bool tempGueltig, int32_t temp, uint32_t heap, uint32_t luecke, const Grenzen &g) {
    if ((tempGueltig && temp >= g.tempAusfall) || heap <= g.heapAusfall || luecke >= g.lueckeAusfall) return AUSFALL;
    if ((tempGueltig && temp >= g.tempSchwach) || heap <= g.heapSchwach || luecke >= g.lueckeSchwach) return SCHWACH;
    return OKAY;
}
