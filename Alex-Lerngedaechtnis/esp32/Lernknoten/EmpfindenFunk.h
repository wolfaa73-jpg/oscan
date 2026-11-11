#pragma once
#include "../Gemeinsam/EmpfindenPaket.h"
#include "../Gemeinsam/FunkPlan.h"
#ifdef ARDUINO_ARCH_ESP32
#include <WiFi.h>
#include <esp_now.h>
#include <esp_wifi.h>
#endif

struct EmpfindenFunk {
    unsigned modus=0;
    bool plan=false;
    bool setze(unsigned neu) {
        if(neu>2)return false;
        if(neu==modus)return true;
#ifdef ARDUINO_ARCH_ESP32
        if(!neu) {
            esp_now_deinit();
            if(!WiFi.mode(WIFI_OFF))return false;
        } else if(!modus) {
            WiFi.persistent(false);
            if(!WiFi.mode(WIFI_STA))return false;
            WiFi.disconnect(false,false);
            if(esp_wifi_set_channel(EmpfindenPaket::kanal,WIFI_SECOND_CHAN_NONE)!=ESP_OK
               || esp_wifi_set_ps(WIFI_PS_NONE)!=ESP_OK || esp_now_init()!=ESP_OK) {
                WiFi.mode(WIFI_OFF);return false;
            }
            esp_now_peer_info_t peer={};
            for(unsigned i=0;i<6;++i)peer.peer_addr[i]=255;
            peer.channel=EmpfindenPaket::kanal;peer.ifidx=WIFI_IF_STA;peer.encrypt=false;
            if(esp_now_add_peer(&peer)!=ESP_OK){esp_now_deinit();WiFi.mode(WIFI_OFF);return false;}
        }
#endif
        modus=neu;return true;
    }
    bool vorTakt(uint32_t t){return !plan || setze(FunkPlan::modus(t));}
    // bit 8: Sendebefehl in diesem Takt; bit 16: Funk bereit; bit 32: API lehnte Senden ab.
    // Kein Empfänger-Nachweis: Ein Broadcast besitzt keine Anwendungsbestätigung.
    unsigned senden(const EmpfindenPaket::Zustand &z) {
        if(!modus)return 0;
        if(modus==1)return 16;
        uint8_t paket[EmpfindenPaket::bytes];
        if(!EmpfindenPaket::packe(z,paket))return 16|8|32;
#ifdef ARDUINO_ARCH_ESP32
        const uint8_t rundruf[6]={255,255,255,255,255,255};
        if(esp_now_send(rundruf,paket,sizeof(paket))!=ESP_OK)return 16|8|32;
#endif
        return 16|8;
    }
};
