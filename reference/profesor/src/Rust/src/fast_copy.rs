//! Fast frame copying process

use crate::colors;
use crate::processes::FastCopyArgs;
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;
use std::thread;

pub fn fast_copy(buffers: FastCopyArgs, running: Arc<AtomicBool>) {
    while running.load(Ordering::Relaxed) {
        print!(
            "{}-> Fast copy execution:\r\n{}",
            colors::BLUE,
            colors::RESET
        );

        match buffers.src.data.try_lock() {
            Err(_) => {
                print!(
                    "{}[E] Fast copy: skipped due to mutex lock.\r\n{}",
                    colors::RED,
                    colors::RESET
                );
            }
            Ok(src_guard) => {
                match buffers.dest.data.try_lock() {
                    Err(_) => {
                        print!(
                            "{}[E] Fast copy: skipped due to destination mutex lock.\r\n{}",
                            colors::RED,
                            colors::RESET
                        );
                    }
                    Ok(mut dest_guard) => {
                        let len = std::cmp::min(src_guard.len(), dest_guard.len());
                        if len > 0 {
                            dest_guard[..len].copy_from_slice(&src_guard[..len]);
                        }
                        print!(
                            "{}[i] Fast copy: performed successfully.\r\n{}",
                            colors::GREEN,
                            colors::RESET
                        );
                    }
                }
            }
        }

        thread::yield_now();
    }
}

