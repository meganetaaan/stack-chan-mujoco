#include "power_sequence.h"
#define HEALTH_MASK (P_IN_HEALTH | P_IN_LEFT_SOURCE | P_IN_RIGHT_SOURCE)
#define PG_MASK (P_IN_LEFT_PG | P_IN_RIGHT_PG)
#define INPUT_MASK ((1u << 10) - 1u)

static int healthy(uint16_t in) { return (in & HEALTH_MASK) == HEALTH_MASK; }
static int valid(uint8_t state, uint16_t in) {
    return state <= POWER_RUN && (in & ~INPUT_MASK) == 0;
}
static int operating_fault(uint16_t in) {
    return !healthy(in) || !(in & P_IN_PERMISSION) ||
           !(in & P_IN_ARMED) || (in & P_IN_CLR_LOW);
}
uint8_t power_sequence_outputs(uint8_t state, uint16_t in) {
    uint8_t out = 0;
    if (!valid(state, in)) return P_OUT_CLEAR;
    if (state == POWER_CLEAR_RESET || state == POWER_CLEAR_QUALIFY) {
        out = P_OUT_CLEAR;
        if (state == POWER_CLEAR_QUALIFY && healthy(in) && (in & P_IN_CLR_LOW))
            out |= P_OUT_RESET_LOW_VALID;
    }
    if (state == POWER_START) out |= P_OUT_STARTUP_TIMER_RUN;
    if ((state == POWER_START || state == POWER_RUN) && !operating_fault(in)) {
        if (state == POWER_START && !(in & P_IN_STARTUP_EXPIRED)) out |= P_OUT_ENABLE;
        if (state == POWER_RUN && (in & PG_MASK) == PG_MASK) out |= P_OUT_ENABLE;
    }
    return out;
}
uint8_t power_sequence_next(uint8_t state, uint16_t in) {
    if (!valid(state, in)) return POWER_CLEAR_RESET;
    switch (state) {
    case POWER_CLEAR_RESET:
    case POWER_CLEAR_QUALIFY:
        if (!healthy(in) || !(in & P_IN_CLR_LOW)) return POWER_CLEAR_RESET;
        if (state == POWER_CLEAR_RESET)
            return (in & P_IN_HOLD_DONE) ? POWER_CLEAR_RESET : POWER_CLEAR_QUALIFY;
        if ((in & P_IN_HOLD_DONE) && !(in & (P_IN_ARMED | P_IN_PERMISSION)))
            return POWER_WAIT_PERMISSION_LOW;
        return state;
    case POWER_WAIT_PERMISSION_LOW:
    case POWER_WAIT_PERMISSION_HIGH:
        if (!healthy(in)) return POWER_CLEAR_RESET;
        if (!(in & P_IN_PERMISSION)) return POWER_WAIT_PERMISSION_HIGH;
        if (!(in & P_IN_ARMED) || (in & P_IN_CLR_LOW)) return POWER_CLEAR_RESET;
        if (state == POWER_WAIT_PERMISSION_HIGH)
            return (in & P_IN_STARTUP_EXPIRED) ? POWER_CLEAR_RESET : POWER_START;
        return state;
    case POWER_START:
        if (operating_fault(in) || (in & P_IN_STARTUP_EXPIRED)) return POWER_CLEAR_RESET;
        return (in & PG_MASK) == PG_MASK ? POWER_RUN : POWER_START;
    case POWER_RUN:
        return operating_fault(in) || (in & PG_MASK) != PG_MASK ? POWER_CLEAR_RESET : POWER_RUN;
    default:
        return POWER_CLEAR_RESET;
    }
}
