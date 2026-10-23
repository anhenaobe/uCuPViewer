//! Frame rendering process

use crate::colors;
use crate::processes::{RenderPack, SyncFrame};
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;
use std::thread;
use std::time::Duration;

// Rendering period (700 milliseconds)
const RENDER_PERIOD: Duration = Duration::from_millis(700);

fn private_render_function(frame: &SyncFrame, daq_size: usize) {
    print!(
        "{}[i] Rendering function executed. Frame size: {}x{}, DAQ buffer size: {}\r\n{}",
        colors::GREEN,
        frame.width,
        frame.height,
        daq_size,
        colors::RESET
    );
}

pub fn renderer(render_pack: RenderPack, running: Arc<AtomicBool>) {
    while running.load(Ordering::Relaxed) {
        print!(
            "{}-> Frame rendering execution.\r\n{}",
            colors::BLUE,
            colors::RESET
        );

        {
            // Acquire locks on frame buffer and DAQ buffer
            let _frame_lock = render_pack.frame_buffer.data.lock().unwrap();
            let mut daq_state = render_pack.daq_data.state.lock().unwrap();

            // Fast render function
            private_render_function(&render_pack.frame_buffer, render_pack.daq_data.size);
            print!(
                "{}[i] Frame rendering performed.\r\n{}",
                colors::GREEN,
                colors::RESET
            );

            thread::sleep(RENDER_PERIOD);
            daq_state.has_new_data = false; // Mark data as processed
        }

        // Wait for DAQ to produce new data or termination signal
        let mut daq_state = render_pack.daq_data.state.lock().unwrap();
        while !daq_state.has_new_data && running.load(Ordering::Relaxed) {
            daq_state = render_pack.daq_data.cond.wait(daq_state).unwrap();
        }
    }
}

