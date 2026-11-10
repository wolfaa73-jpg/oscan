// Serieller Replay-Prüfstand. Eine vollständige Zeile löst genau eine Beobachtung aus.
// Im Körpermodus misst sich der Knoten in eigenem Takt selbst.
#include "Erkundung.h"
#include "Knoten.h"
#include "Koerper.h"
#include "Reize.h"
#include <string.h>
#ifdef ARDUINO_ARCH_ESP32
#include <Preferences.h>
#include <esp_heap_caps.h>
#include <esp_system.h>
#endif
// Die Selbsterkundung schaltet Pins und kennt dafür nur die freien des ESP32-S3.
#if defined(ARDUINO_ARCH_ESP32) && defined(CONFIG_IDF_TARGET_ESP32S3)
#define ALEX_ERKUNDUNG
#endif

#if defined(ALEX_KONTEXT) + defined(ALEX_ERBE) + defined(ALEX_STARTWERT) > 1
#error "Pro Firmware nur eine Lernregel: ALEX_KONTEXT, ALEX_ERBE oder ALEX_STARTWERT"
#elif defined(ALEX_STARTWERT)
Knoten knoten(Regel::STARTWERT);
const char *const bereit = "BEREIT,STARTWERT";
const char *const standKey = "startwert";
#elif defined(ALEX_ERBE)
Knoten knoten(Regel::ERBE);
const char *const bereit = "BEREIT,ERBE";
const char *const standKey = "erbe";
#elif defined(ALEX_KONTEXT)
Knoten knoten(Regel::KONTEXT);
const char *const bereit = "BEREIT,KONTEXT";
const char *const standKey = "kontext";
#else
Knoten knoten;
const char *const bereit = "BEREIT,ZEIT";
const char *const standKey = "zeit";
#endif
char zeile[64];
size_t laenge = 0;
bool verwerfen = false;
// Weiterlernen über Läufe: Das Gerät sichert selbst jeden n-ten Takt. Nach LADEN lässt der
// nächste Körpertakt eine Lücke, damit die Pause zwischen zwei Läufen kein Übergang wird.
uint32_t sichernAlle = 0;
bool frischGeladen = false;
bool lernstand(bool speichern, bool melden = true);
const char *const namen[] = {"OK", "SCHWACH", "AUSFALL"};
const uint32_t maxTemp = 100000;  // Zehntelgrad, nur Plausibilitätsgrenze der Eingabe
Grenzen grenzen = {};
bool grenzenGesetzt = false;
bool koerperAn = false;

// Liest eine Dezimalzahl ohne Vorzeichen und rückt den Zeiger vor.
bool zahl(const char *&text, uint32_t &wert) {
    if (*text < '0' || *text > '9') return false;
    wert = 0;
    while (*text >= '0' && *text <= '9') {
        const unsigned ziffer = *text++ - '0';
        if (wert > (UINT32_MAX - ziffer) / 10) return false;
        wert = wert * 10 + ziffer;
    }
    return true;
}

// Genau anzahl Zahlen, durch je ein Leerzeichen getrennt, bis zum Zeilenende.
bool felder(const char *text, uint32_t *werte, unsigned anzahl) {
    for (unsigned i = 0; i < anzahl; ++i) {
        if (i && *text++ != ' ') return false;
        if (!zahl(text, werte[i])) return false;
    }
    return *text == '\0';
}

bool befehl(const char *name, const char *&rest) {
    const size_t n = strlen(name);
    if (strncmp(zeile, name, n) != 0 || zeile[n] != ' ') return false;
    rest = zeile + n + 1;
    return true;
}

#ifdef ARDUINO_ARCH_ESP32
// Durchläufe mit eigener Arbeit (Messung, Ausgabe, LED) zählen nicht zur Lücke.
bool eigeneArbeit = false;

// Last auf Kern 0 im Rhythmus des Rechners. Der Knoten erfährt davon nur über
// seine Messwerte, die Ausgabe vermerkt die Phase nur für die Auswertung.
volatile bool lastAktiv = false;
volatile uint32_t lastAnMs = 0;
volatile uint32_t lastAusMs = 0;
TaskHandle_t lastTask = nullptr;
volatile uint32_t lastSenke = 0;
Lastplan lastplan;  // nur die Lastaufgabe zieht daraus, der Befehl setzt die Saat

void lastSchleife(void *) {
    uint32_t x = 1;
    for (;;) {
        if (!lastAnMs) {
            lastAktiv = false;
            vTaskDelay(pdMS_TO_TICKS(100));
            continue;
        }
        lastAktiv = true;
        const uint32_t ende = millis() + lastplan.dauer(lastAnMs / 1000) * 1000;
        while (lastAnMs && static_cast<int32_t>(millis() - ende) < 0) {
            const uint32_t stueck = millis() + 10;
            while (static_cast<int32_t>(millis() - stueck) < 0) x = x * 1664525u + 1013904223u;
            lastSenke = x;
            vTaskDelay(1);  // Leerlauf von Kern 0 hält den Task-Wachhund ruhig
        }
        lastAktiv = false;
        const uint32_t pause = millis() + lastplan.dauer(lastAusMs / 1000) * 1000;
        while (lastAnMs && static_cast<int32_t>(millis() - pause) < 0) vTaskDelay(pdMS_TO_TICKS(100));
    }
}

// Speicherleck und Bremse der Hauptschleife, beide im Takt des Körpers. Auch davon
// erfährt der Knoten nur über seine Messwerte.
Leck leck;
Bremse bremse;
void *bloecke[512];
unsigned belegt = 0;
uint32_t stauMs = 0;    // Stillstand, der im nächsten Durchlauf von loop() ansteht
bool gebremst = false;  // seit dem letzten Takt stand die Schleife einmal still

void leckFrei() {
    while (belegt) heap_caps_free(bloecke[--belegt]);
}

// Speicherlage am Boden des Lecks, direkt nach der Freigabe und wenn ein ganzer Block in kein
// freies Stück mehr passt (KLEIN). Sie zeigt, wie zerstückelt der Speicher ist: Hält die eigene
// Bedingung das Leck an (versucht 0), oder fand heap_caps_malloc trotz genug freiem Speicher
// kein Stück, das groß genug ist (versucht 1)?
// Die Zeile folgt der Körperzeile desselben Takts, damit diese zuerst kommt.
struct Speicherlage {
    const char *ereignis = nullptr;  // BODEN, FREI oder KLEIN, nullptr: nichts zu melden
    bool versucht = false;
    uint32_t frei = 0;               // ESP.getFreeHeap(), dieselbe Zahl wie in der Bedingung
    multi_heap_info_t info = {};     // für MALLOC_CAP_INTERNAL | MALLOC_CAP_8BIT wie das Leck
    unsigned leckbloecke = 0;
} speicherlage;

void merkeSpeicher(const char *ereignis, bool versucht, uint32_t frei) {
    speicherlage.ereignis = ereignis;
    speicherlage.versucht = versucht;
    speicherlage.frei = frei;
    heap_caps_get_info(&speicherlage.info, MALLOC_CAP_INTERNAL | MALLOC_CAP_8BIT);
    speicherlage.leckbloecke = belegt;
}

// SPEICHER,takt,ereignis,versucht,frei,frei8,groesster,freie_bloecke,belegte_bloecke,leckbloecke
void meldeSpeicher(uint32_t takt) {
    if (!speicherlage.ereignis) return;
    const multi_heap_info_t &i = speicherlage.info;
    Serial.print("SPEICHER,");
    Serial.print(takt);
    Serial.print(',');
    Serial.print(speicherlage.ereignis);
    Serial.print(speicherlage.versucht ? ",1," : ",0,");
    Serial.print(speicherlage.frei);
    Serial.print(',');
    Serial.print(static_cast<unsigned long>(i.total_free_bytes));
    Serial.print(',');
    Serial.print(static_cast<unsigned long>(i.largest_free_block));
    Serial.print(',');
    Serial.print(static_cast<unsigned long>(i.free_blocks));
    Serial.print(',');
    Serial.print(static_cast<unsigned long>(i.allocated_blocks));
    Serial.print(',');
    Serial.print(speicherlage.leckbloecke);
    Serial.println("");
    speicherlage.ereignis = nullptr;
}

// Vor der Messung: einen Block belegen oder alles freigeben, wie es der Ablauf will.
void leckTakt() {
    switch (leck.takt()) {
    case Leck::BELEGEN: {
        const uint32_t frei = ESP.getFreeHeap();
        const bool versucht = belegt < sizeof(bloecke) / sizeof(bloecke[0]) && frei > leck.boden
                              && frei - leck.boden >= leck.block;
        void *block = nullptr;
        if (versucht) {
            block = heap_caps_malloc(leck.block, MALLOC_CAP_INTERNAL | MALLOC_CAP_8BIT);
            // Genug frei, aber kein Stück groß genug: Lage merken, dann kleinere Blöcke.
            if (!block) merkeSpeicher("KLEIN", true, frei);
            for (uint32_t g = Leck::kleiner(leck.block); !block && g; g = Leck::kleiner(g))
                block = heap_caps_malloc(g, MALLOC_CAP_INTERNAL | MALLOC_CAP_8BIT);
        }
        if (block) {
            bloecke[belegt++] = block;
        } else {
            leck.voll();
            merkeSpeicher("BODEN", versucht, frei);
        }
        break;
    }
    case Leck::FREIGEBEN:
        leckFrei();
        merkeSpeicher("FREI", false, ESP.getFreeHeap());
        break;
    default:
        break;
    }
}

#ifdef ALEX_RGB_PIN
bool blitzAn = false;
uint32_t blitzEnde = 0;
Zustand ledZustand = UNBEKANNT;

// Grün OK, Gelb SCHWACH, Rot AUSFALL, schwaches Weiß bereit. Gedämpft, fürs Auge reicht das.
void zeigeZustand(Zustand z) {
    static const uint8_t farbe[4][3] = {{0, 6, 0}, {10, 5, 0}, {12, 0, 0}, {3, 3, 3}};
    neopixelWrite(ALEX_RGB_PIN, farbe[z][0], farbe[z][1], farbe[z][2]);
    ledZustand = z;
    eigeneArbeit = true;
}

// Vorwarnung: kurz blau, danach wieder die Farbe des Zustands.
void blitze(Zustand z) {
    neopixelWrite(ALEX_RGB_PIN, 0, 0, 16);
    ledZustand = z;
    blitzAn = true;
    blitzEnde = millis() + 150;
    eigeneArbeit = true;
}
#endif
#endif

#ifdef ALEX_ERKUNDUNG
// Pins, die die Erkundung überhaupt prüft, am ESP32-S3 N16R8. Nie: 0, 3, 45, 46 (Strapping), 19 und 20
// (USB), 26 bis 37 (Flash und PSRAM), 43 und 44 (UART0 für Serial), 48 (RGB-LED). Wie ERLAUBTE_PINS in
// selbsterkundung.py.
const uint8_t erlaubtePins[] = {1, 2, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 21, 38, 39, 40, 41, 42, 47};
const unsigned erlaubteAnzahl = sizeof(erlaubtePins) / sizeof(erlaubtePins[0]);
Erkundung erkundung;
bool pinGeschrieben[Erkundung::maxPins];

// Hängt etwas am Pin? Ohne ihn zu treiben: einmal mit Pull-up lesen, einmal mit Pull-down.
// F folgt beiden (frei), M bleibt tief (Last gegen Masse, etwa eine Transistorbasis), P bleibt hoch,
// U verhält sich verkehrt herum. Danach bleibt der Pin ein Eingang mit Pull-down.
char pinKlasse(uint8_t pin) {
    pinMode(pin, INPUT_PULLUP);
    delayMicroseconds(200);
    const bool hoch = digitalRead(pin) == HIGH;
    pinMode(pin, INPUT_PULLDOWN);
    delayMicroseconds(200);
    const bool tief = digitalRead(pin) == LOW;
    return hoch && tief ? 'F' : tief ? 'M' : hoch ? 'P' : 'U';
}

void meldePins(const char *kopf, const char *klassen) {
    Serial.print(kopf);
    for (unsigned i = 0; i < erlaubteAnzahl; ++i) {
        Serial.print(',');
        Serial.print(static_cast<unsigned>(erlaubtePins[i]));
        Serial.print(klassen[i]);
    }
    Serial.println("");
}

// Erkundung beenden: jeder Kandidat aus und wieder Eingang mit Pull-down, damit nichts weiterläuft.
void pinsAus() {
    for (unsigned i = 0; i < erkundung.anzahl(); ++i) {
        digitalWrite(erkundung.pin(i), LOW);
        pinMode(erkundung.pin(i), INPUT_PULLDOWN);
    }
    erkundung.beende();
}

// Nach dem Körpertakt: Zeilen der Erkundung ausgeben, dann die Pins so setzen, wie sie entschieden hat.
void erkundungTakt(uint32_t takt, bool gueltig, int32_t temp) {
    erkundung.takt(takt, gueltig, temp);
    for (unsigned i = 0; i < erkundung.zeilen(); ++i) Serial.println(erkundung.zeile(i));
    for (unsigned i = 0; i < erkundung.anzahl(); ++i) {
        if (erkundung.an(i) == pinGeschrieben[i]) continue;
        digitalWrite(erkundung.pin(i), erkundung.an(i) ? HIGH : LOW);
        pinGeschrieben[i] = erkundung.an(i);
    }
}
#endif

// Welche Reize gerade wirken, als Bits für die Auswertung: 1 Last, 2 Leck, 4 Bremse.
unsigned reize() {
#ifdef ARDUINO_ARCH_ESP32
    return (lastAktiv ? 1u : 0u) | (belegt ? 2u : 0u) | (gebremst ? 4u : 0u);
#else
    return 0;
#endif
}

// Körpermodus und alle Reize aus, die LED zurück auf bereit.
void ruhe() {
    koerperAn = false;
#ifdef ARDUINO_ARCH_ESP32
    lastAnMs = 0;
    leck = Leck();
    leckFrei();
    speicherlage.ereignis = nullptr;
    bremse = Bremse();
    stauMs = 0;
    gebremst = false;
#ifdef ALEX_ERKUNDUNG
    pinsAus();
#endif
#ifdef ALEX_RGB_PIN
    blitzAn = false;
    zeigeZustand(UNBEKANNT);
#endif
#endif
}

// Ein Körpertakt: einstufen, lernen, Rohwerte und Entscheidung ausgeben.
bool koerperTakt(bool tempGueltig, int32_t temp, uint32_t heap, uint32_t luecke) {
    const Zustand zustand = einstufen(tempGueltig, temp, heap, luecke, grenzen);
    const uint32_t takt = knoten.takt() + (frischGeladen ? 2 : 1);
    Entscheidung entscheidung;
    if (!knoten.schritt(takt, zustand, entscheidung)) return false;
    frischGeladen = false;
    Serial.print("K,");
    Serial.print(takt);
    Serial.print(',');
    Serial.print(namen[zustand]);
    Serial.print(entscheidung.sofort ? ",1" : ",0");
    Serial.print(entscheidung.warnung ? ",1," : ",0,");
    if (tempGueltig) Serial.print(temp); else Serial.print('-');
    Serial.print(',');
    Serial.print(heap);
    Serial.print(',');
    Serial.print(luecke);
    Serial.print(',');
    Serial.print(reize());
    Serial.println("");
#if defined(ARDUINO_ARCH_ESP32) && defined(ALEX_RGB_PIN)
    if (entscheidung.warnung) blitze(zustand); else zeigeZustand(zustand);
#endif
    // Still sichern. Schlägt es fehl, folgt FEHLER, und die Aufnahme bricht sichtbar ab.
    return !sichernAlle || takt % sichernAlle || lernstand(true, false);
}

#ifdef ARDUINO_ARCH_ESP32
uint32_t intervallMs = 0;
uint32_t naechsterTick = 0;
uint32_t letzteRunde = 0;
uint32_t luecke = 0;

// Die Lücke ist der größte Abstand zwischen zwei Durchläufen von loop() seit dem
// letzten Takt. Durchläufe mit eigener Arbeit zählen nicht mit, gemessen wird
// also nur fremde Wartezeit.
void koerperSchleife() {
    const uint32_t jetzt = micros();
    if (!eigeneArbeit && jetzt - letzteRunde > luecke) luecke = jetzt - letzteRunde;
    eigeneArbeit = false;
    letzteRunde = jetzt;
    if (stauMs) {
        // Die Bremse: Dieser Durchlauf steht still, die Lücke misst das als fremde Wartezeit.
        const uint32_t ms = stauMs;
        stauMs = 0;
        gebremst = true;
        delay(ms);
        return;
    }
#ifdef ALEX_RGB_PIN
    if (blitzAn && static_cast<int32_t>(millis() - blitzEnde) >= 0) {
        blitzAn = false;
        zeigeZustand(ledZustand);
    }
#endif
    if (!koerperAn || static_cast<int32_t>(millis() - naechsterTick) < 0) return;
    leckTakt();
    const float grad = temperatureRead();
    const bool gueltig = !isnan(grad);
    const int32_t temp = gueltig ? static_cast<int32_t>(lroundf(grad * 10.0f)) : 0;
    if (!koerperTakt(gueltig, temp, ESP.getFreeHeap(), luecke)) {
        ruhe();
        Serial.println("FEHLER");
    } else {
        meldeSpeicher(knoten.takt());
#ifdef ALEX_ERKUNDUNG
        erkundungTakt(knoten.takt(), gueltig, temp);
#endif
    }
    gebremst = false;
    stauMs = bremse.takt();
    eigeneArbeit = true;
    luecke = 0;
    naechsterTick += intervallMs;
    // Nach einem Stillstand nicht nachholen, sondern ab jetzt neu takten.
    if (static_cast<int32_t>(millis() - naechsterTick) >= 0) naechsterTick = millis() + intervallMs;
}
#endif

#ifdef ARDUINO_ARCH_ESP32
// Warum das Gerät zuletzt neu gestartet ist, als Zahl und Name. Die Nummern sind die von
// esp_reset_reason_t in ESP-IDF 4.4. Ein Neustart mitten in einer Aufnahme ist sonst nicht zu klären.
void meldeNeustart() {
    static const char *const gruende[] = {"UNBEKANNT", "EINSCHALTEN", "EXTERN", "SOFTWARE", "PANIK",
                                          "INT_WACHHUND", "TASK_WACHHUND", "WACHHUND", "TIEFSCHLAF",
                                          "UNTERSPANNUNG", "SDIO"};
    const int grund = esp_reset_reason();
    Serial.print("NEUSTART,");
    Serial.print(grund);
    Serial.print(',');
    Serial.println(grund >= 0 && grund < static_cast<int>(sizeof(gruende) / sizeof(gruende[0])) ? gruende[grund] : "?");
}
#endif

bool lernstand(bool speichern, bool melden) {
    uint8_t daten[Knoten::maxStandBytes];
    uint8_t alt[Knoten::maxStandBytes];
    const size_t n = knoten.standBytes();
    if (speichern && !knoten.exportiere(daten)) return false;
    Preferences nvs;
    if (!nvs.begin("alex-lernlabor", !speichern)) return false;
    const char *key = standKey;
    // isKey zuerst: getBytesLength meldet einen fehlenden Schlüssel selbst auf Serial und
    // stünde dann vor GESICHERT oder FEHLER mitten im Protokoll.
    const bool lesbar = nvs.isKey(key) && nvs.getBytesLength(key) == n && nvs.getBytes(key, alt, n) == n;
    bool ok;
    if (speichern) {
        ok = (lesbar && memcmp(daten, alt, n) == 0) || nvs.putBytes(key, daten, n) == n;
    } else {
        ok = lesbar && knoten.importiere(alt);
        frischGeladen = ok;
    }
    nvs.end();
    if (ok && melden) Serial.println(speichern ? "GESICHERT" : "GELADEN");
    return ok;
}

bool verarbeiteZeile() {
    const char *rest = nullptr;
    if (strcmp(zeile, "SICHERN") == 0) return lernstand(true);
    if (strcmp(zeile, "LADEN") == 0) return lernstand(false);
    if (strcmp(zeile, "NEUER_LAUF") == 0) {
        knoten.neuerLauf();
        sichernAlle = 0;
        frischGeladen = false;
        ruhe();
        Serial.println(bereit);
        return true;
    }
    if (strcmp(zeile, "STOP") == 0) {
        ruhe();
        Serial.println("KOERPER,aus");
        return true;
    }
    if (befehl("GRENZEN", rest)) {
        uint32_t w[6];
        if (!felder(rest, w, 6) || w[0] > maxTemp || w[1] > maxTemp) return false;
        const Grenzen neu = {static_cast<int32_t>(w[0]), static_cast<int32_t>(w[1]), w[2], w[3], w[4], w[5]};
        if (!neu.gueltig()) return false;
        grenzen = neu;
        grenzenGesetzt = true;
        Serial.println("GRENZEN,ok");
        return true;
    }
    if (befehl("BLICK", rest)) {
        // Takte, die die Vorwarnung vorausdenkt. Nicht während des Körpermodus, sonst passt
        // die Aufnahme nicht mehr zu ihrer Nachrechnung.
        uint32_t takte;
        if (koerperAn || !felder(rest, &takte, 1) || !knoten.setzeBlick(takte)) return false;
        Serial.println("BLICK,ok");
        return true;
    }
    if (befehl("SICHERN_ALLE", rest)) {
        // Jeden n-ten Körpertakt selbst sichern, 0 schaltet ab. Wie BLICK nicht im Körpermodus.
        uint32_t n;
        if (koerperAn || !felder(rest, &n, 1)) return false;
        sichernAlle = n;
        Serial.println("SICHERN_ALLE,ok");
        return true;
    }
    if (befehl("MESSWERT", rest)) {
        // Rohwerte von außen, etwa eine aufgezeichnete Spur. "-" steht für eine nicht lesbare Temperatur.
        const bool gueltig = *rest != '-';
        uint32_t temp = 0, w[2];
        if (gueltig) {
            if (!zahl(rest, temp) || temp > maxTemp) return false;
        } else {
            ++rest;
        }
        if (*rest++ != ' ' || !felder(rest, w, 2)) return false;
        return grenzenGesetzt && !koerperAn && koerperTakt(gueltig, static_cast<int32_t>(temp), w[0], w[1]);
    }
#ifdef ARDUINO_ARCH_ESP32
    if (befehl("KOERPER", rest)) {
        uint32_t ms;
        if (!felder(rest, &ms, 1) || ms < 100 || !grenzenGesetzt) return false;
        intervallMs = ms;
        naechsterTick = millis() + ms;
        luecke = 0;
        koerperAn = true;
        Serial.println("KOERPER,an");
        return true;
    }
    if (befehl("LAST", rest)) {
        // Arbeitsphase und Pause in Sekunden, LAST 0 0 beendet die Last. Mit einer Saat als drittem
        // Wert dauert jede Phase zufällig lang, von einem Viertel bis zum vollen Wert (Lastplan).
        uint32_t w[3] = {};
        if (!felder(rest, w, 3)) {
            w[2] = 0;
            if (!felder(rest, w, 2)) return false;
        }
        if (w[0] > 3600 || w[1] > 3600) return false;
        lastAnMs = 0;  // die laufende Phase endet, bevor die Saat wechselt
        lastplan.zufall = w[2];
        lastAusMs = w[1] * 1000;
        lastAnMs = w[0] * 1000;
        if (w[0] && !lastTask
            && xTaskCreatePinnedToCore(lastSchleife, "last", 3072, nullptr, 1, &lastTask, 0) != pdPASS) return false;
        Serial.println("LAST,ok");
        return true;
    }
    if (befehl("LECK", rest)) {
        // Byte je Takt, Boden in Byte, Takte am Boden, Takte Pause, wahlweise ein flacher Boden und das
        // Muster der Durchgänge, die schon an ihm anhalten. LECK 0 0 0 0 beendet und gibt frei.
        uint32_t w[6] = {};
        if (!felder(rest, w, 6)) {
            w[4] = w[5] = 0;
            if (!felder(rest, w, 4)) return false;
        }
        Leck neu;
        if ((w[0] | w[1] | w[2] | w[3] | w[4] | w[5]) && !neu.starte(w[0], w[1], w[2], w[3], w[4], w[5])) return false;
        leckFrei();
        leck = neu;
        Serial.println("LECK,ok");
        return true;
    }
    if (befehl("BREMSE", rest)) {
        // Start, Schritt und Ende des Stillstands in ms, Takte am Ende, Takte Pause. BREMSE 0 0 0 0 0 beendet.
        uint32_t w[5];
        if (!felder(rest, w, 5)) return false;
        Bremse neu;
        if ((w[0] | w[1] | w[2] | w[3] | w[4]) && !neu.starte(w[0], w[1], w[2], w[3], w[4])) return false;
        bremse = neu;
        stauMs = 0;
        Serial.println("BREMSE,ok");
        return true;
    }
#endif
#ifdef ALEX_ERKUNDUNG
    if (strcmp(zeile, "PINS") == 0) {
        // Nur nachsehen, was an den erlaubten Pins hängt. Nichts wird getrieben.
        if (koerperAn || erkundung.aktiv()) return false;
        char klassen[erlaubteAnzahl];
        for (unsigned i = 0; i < erlaubteAnzahl; ++i) klassen[i] = pinKlasse(erlaubtePins[i]);
        meldePins("PINS", klassen);
        return true;
    }
    if (befehl("ERKUNDUNG", rest)) {
        // Takte Ruhe, Takte an, Takte im Mittel, Schwelle in Zehntelgrad, Versuche je Pin, Takte Regelung
        // zwischen zwei Prüfungen (0 nie), Saat der Zufallszahlen. ERKUNDUNG 0 0 0 0 0 0 0 beendet.
        // Vorher wird jeder erlaubte Pin passiv geprüft, geschaltet werden nur F und M.
        uint32_t w[7];
        if (koerperAn || !grenzenGesetzt || !felder(rest, w, 7)) return false;
        pinsAus();
        if (!(w[0] | w[1] | w[2] | w[3] | w[4] | w[5] | w[6])) {
            Serial.println("ERKUNDUNG,ok");
            return true;
        }
        char klassen[erlaubteAnzahl];
        uint8_t kandidaten[Erkundung::maxPins];
        unsigned anzahl = 0;
        for (unsigned i = 0; i < erlaubteAnzahl; ++i) {
            klassen[i] = pinKlasse(erlaubtePins[i]);
            if (klassen[i] == 'F' || klassen[i] == 'M') kandidaten[anzahl++] = erlaubtePins[i];
        }
        if (!erkundung.starte(kandidaten, anzahl, w[0], w[1], w[2], w[3], w[4], w[5], w[6], grenzen.tempSchwach))
            return false;
        for (unsigned i = 0; i < anzahl; ++i) {
            digitalWrite(kandidaten[i], LOW);
            pinMode(kandidaten[i], OUTPUT);
            digitalWrite(kandidaten[i], LOW);
            pinGeschrieben[i] = false;
        }
        meldePins("ERKUNDUNG,ok", klassen);
        return true;
    }
#endif
    if (koerperAn) return false;
    const char *text = zeile;
    uint32_t takt;
    if (!zahl(text, takt) || *text++ != ',') return false;
    Zustand zustand = UNBEKANNT;
    for (unsigned i = 0; i < 3; ++i) {
        if (strcmp(text, namen[i]) == 0) zustand = static_cast<Zustand>(i);
    }
    Entscheidung entscheidung;
    if (!knoten.schritt(takt, zustand, entscheidung)) return false;
    frischGeladen = false;
    Serial.print(takt);
    Serial.print(',');
    Serial.print(namen[zustand]);
    Serial.print(entscheidung.sofort ? ",1" : ",0");
    Serial.println(entscheidung.warnung ? ",1" : ",0");
    return true;
}

void setup() {
    Serial.begin(115200);
#if defined(ARDUINO_ARCH_ESP32) && defined(ALEX_RGB_PIN)
    zeigeZustand(UNBEKANNT);
#endif
    Serial.println("takt,zustand,sofort,vorwarnung");
#ifdef ARDUINO_ARCH_ESP32
    meldeNeustart();
#endif
}

void loop() {
#ifdef ARDUINO_ARCH_ESP32
    koerperSchleife();
#endif
    while (Serial.available() > 0) {
        const int c = Serial.read();
        if (c == '\n') {
            if (laenge && zeile[laenge - 1] == '\r') --laenge;
            zeile[laenge] = '\0';
            if (verwerfen || !verarbeiteZeile()) Serial.println("FEHLER");
            laenge = 0;
            verwerfen = false;
        } else if (c <= 0 || c > 127 || laenge >= sizeof(zeile) - 1) {
            verwerfen = true;
        } else {
            zeile[laenge++] = static_cast<char>(c);
        }
    }
}
