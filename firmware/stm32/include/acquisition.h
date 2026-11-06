#ifndef ACQUISITION_H
#define ACQUISITION_H
#include <stdint.h>
#include <stdbool.h>
#define ACQUISITION_VALUES 128u
typedef enum { ACQ_IDLE, ACQ_ACQUIRING, ACQ_READY, ACQ_ERROR } acquisition_state_t;
bool acquisition_init(void);
bool acquisition_set_preset(uint32_t hz);
bool acquisition_start(void);
bool acquisition_stop(void);
acquisition_state_t acquisition_get_status(void);
uint32_t acquisition_get_preset(void);
/* Main-context API only. Pointer stays valid until release; ACQ_READY is ADC-only. */
const uint16_t *acquisition_get_window(void);
bool acquisition_release_window(void);
void acquisition_poll(void);
#endif
