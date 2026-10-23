//! Data acquisition process

use crate::colors;
use crate::processes::SharedDaqBuffer;
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;
use std::thread;
use std::time::Duration;

// Data acquisition period (500 milliseconds)
const DAQ_PERIOD: Duration = Duration::from_millis(500);

fn private_daq_function(_buffer: &[u16], size: usize) {
    print!(
        "{}[i] Data acquisition function executed. Buffer size: {}\r\n{}",
        colors::GREEN,
        size,
        colors::RESET
    );
}

pub fn daq(daq_buffer: SharedDaqBuffer, running: Arc<AtomicBool>) {
    while running.load(Ordering::Relaxed) {
        print!(
            "{}Data acquisition execution.\r\n{}",
            colors::BLUE,
            colors::RESET
        );

        {
            let mut state = daq_buffer.state.lock().unwrap();

            // Implements hardware communication and data dump from microcontroller
            private_daq_function(&state.buffer, daq_buffer.size);
            print!(
                "{}[i] Data acquisition performed.\r\n{}",
                colors::GREEN,
                colors::RESET
            );
            state.has_new_data = true;

            // Signal condition variable that new DAQ data is available
            daq_buffer.cond.notify_one();
        }

        thread::sleep(DAQ_PERIOD);
    }
}

