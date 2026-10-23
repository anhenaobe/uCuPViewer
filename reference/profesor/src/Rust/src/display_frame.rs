//! Display frame refresh driver process

use crate::colors;
use crate::processes::FastCopyArgs;
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;
use std::thread;
use std::time::Duration;

// Display refresh period (1 second)
const DISPLAY_PERIOD: Duration = Duration::from_secs(1);

pub fn display_frame(_args: FastCopyArgs, running: Arc<AtomicBool>) {
    while running.load(Ordering::Relaxed) {
        print!(
            "{}Display frame execution.\r\n{}",
            colors::BLUE,
            colors::RESET
        );
        // Display drawing logic would go here
        thread::sleep(DISPLAY_PERIOD);
    }
}

