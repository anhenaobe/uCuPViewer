/* Run on target from debugger after acquisition_init, before normal application.
 * Not a host simulation. Returns failing line, 0 on success. Caller must arrange
 * safe DC inputs. Completion timeout is 2 seconds (slowest window 0.64 s).
 */
#include "acquisition.h"
#include "stm32l4xx_hal.h"
#define CHECK(x) do { if (!(x)) return __LINE__; } while (0)
int acquisition_target_test(void) {
    CHECK(acquisition_get_status() == ACQ_IDLE);
    CHECK(!acquisition_get_window());
    CHECK(!acquisition_release_window());
    CHECK(!acquisition_set_preset(40000));
    CHECK(!acquisition_set_preset(0));
    const uint32_t rates[] = {100, 1000, 10000};
    for (unsigned i = 0; i < 3; ++i) {
        CHECK(acquisition_set_preset(rates[i]));
        CHECK(acquisition_get_preset() == rates[i]);
        for (unsigned repeat = 0; repeat < 2; ++repeat) {
            CHECK(acquisition_start());
            CHECK(acquisition_get_status() == ACQ_ACQUIRING);
            CHECK(!acquisition_get_window());
            CHECK(!acquisition_start());
            CHECK(!acquisition_set_preset(100));
            uint32_t start = HAL_GetTick();
            while (acquisition_get_status() == ACQ_ACQUIRING && HAL_GetTick()-start < 2000) acquisition_poll();
            CHECK(acquisition_get_status() == ACQ_READY);
            const uint16_t *window = acquisition_get_window();
            CHECK(window);
            for (unsigned n = 0; n < ACQUISITION_VALUES; ++n) CHECK(window[n] <= 4095);
            CHECK(!acquisition_start());
            CHECK(!acquisition_stop());
            CHECK(acquisition_release_window());
        }
    }
    CHECK(acquisition_start());
    CHECK(acquisition_stop());
    CHECK(acquisition_get_status() == ACQ_IDLE);
    return 0;
}
