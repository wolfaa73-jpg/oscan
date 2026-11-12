#pragma once
#include <stdint.h>
namespace FunkPlan {
constexpr uint32_t dauer=1800, gesamt=10800;
inline unsigned modus(uint32_t takt) {
    if(takt>=3601 && takt<=5400)return 1;
    if(takt>=5401 && takt<=7200)return 2;
    if(takt>=7201 && takt<=9000)return 1;
    return 0;
}
}
