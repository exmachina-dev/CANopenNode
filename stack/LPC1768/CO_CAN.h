#ifndef CO_CAN_H
#define CO_CAN_H

#ifdef CO_HAVE_CONFIG
#include "config.h"
#endif

#ifndef MBED_CAN
#ifndef MBED_CONF_APP_CAN_PORT
    #error "MBED_CONF_APP_CAN_PORT must be defined to select CAN port"
#else
    #define MBED_CAN        MBED_CONF_APP_CAN_PORT
#endif
#endif

#ifndef MBED_CAN
#error "MBED_CAN must be defined to select CAN port"
#endif

#include "mbed.h"

#if (MBED_CAN == 0)
#define MBED_CAN_RX             (p9)
#define MBED_CAN_TX             (p10)
#define MBED_CAN_REG            (LPC_CAN1)
#else
#define MBED_CAN_RX             (p30)
#define MBED_CAN_TX             (p29)
#define MBED_CAN_REG            (LPC_CAN2)
#endif

#define MBED_CHECK_TX_BUFFERS (MBED_CAN_REG->SR & 0x4 || MBED_CAN_REG->SR & 0x400 || MBED_CAN_REG->SR & 0x40000)
#define MBED_CHECK_TX_INTERRUPTS(intStatus) (intStatus & 0x2 || intStatus & 0x200 || intStatus & 0x400)

extern CAN *CANport;

#endif // CO_CAN_H
