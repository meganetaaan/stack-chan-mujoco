#ifndef STACKCHAN_POWER_SEQUENCE_H
#define STACKCHAN_POWER_SEQUENCE_H
#include <stdint.h>
/* Pure sequencing core. Inputs must be electrically/timing qualified elsewhere. */
enum power_state {
    POWER_CLEAR_RESET = 0, POWER_CLEAR_QUALIFY,
    POWER_WAIT_PERMISSION_LOW, POWER_WAIT_PERMISSION_HIGH,
    POWER_START, POWER_RUN
};
enum power_input {
    P_IN_HEALTH = 1u << 0, P_IN_LEFT_SOURCE = 1u << 1,
    P_IN_RIGHT_SOURCE = 1u << 2, P_IN_LEFT_PG = 1u << 3,
    P_IN_RIGHT_PG = 1u << 4, P_IN_ARMED = 1u << 5,
    P_IN_PERMISSION = 1u << 6, P_IN_CLR_LOW = 1u << 7,
    P_IN_HOLD_DONE = 1u << 8, P_IN_STARTUP_EXPIRED = 1u << 9
};
enum power_output {
    P_OUT_ENABLE = 1u << 0, P_OUT_CLEAR = 1u << 1,
    P_OUT_RESET_LOW_VALID = 1u << 2, P_OUT_STARTUP_TIMER_RUN = 1u << 3
};
/* Initialize state to POWER_CLEAR_RESET; never initialize directly to WAIT. */
uint8_t power_sequence_outputs(uint8_t state, uint16_t inputs);
uint8_t power_sequence_next(uint8_t state, uint16_t inputs);
#endif
