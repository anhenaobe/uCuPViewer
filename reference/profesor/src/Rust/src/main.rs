#![allow(dead_code)]

mod colors;
mod daq;
mod display_frame;
mod fast_copy;
mod processes;
mod renderer;

use processes::{DaqBuffer, FastCopyArgs, RenderPack, SyncFrame};
use std::sync::atomic::AtomicBool;
use std::sync::Arc;
use std::thread;
use std::time::Duration;

// Startup delay before starting the renderer and display threads (200 milliseconds)
const STARTUP_DELAY: Duration = Duration::from_millis(200);

// Use POSIX signal function from standard C runtime without external crates
extern "C" {
    fn signal(sig: i32, handler: extern "C" fn(i32)) -> usize;
}

const SIGINT: i32 = 2;

extern "C" fn handle_signal(sig: i32) {
    if sig == SIGINT {
        println!("\nSIGINT received. Terminating processes...");
        std::process::exit(0);
    }
}

fn main() {
    // Graceful signal handling using standard C runtime
    unsafe {
        signal(SIGINT, handle_signal);
    }

    print!("Starting processes...\n\r");

    // Frame buffers and DAQ buffer
    let render_buffer = Arc::new(SyncFrame::new(640, 480));
    let draw_buffer = Arc::new(SyncFrame::new(640, 480));
    let daq_buffer = Arc::new(DaqBuffer::new(1024));

    let fast_copy_args = FastCopyArgs {
        src: Arc::clone(&render_buffer),
        dest: Arc::clone(&draw_buffer),
    };

    let render_pack = RenderPack {
        frame_buffer: Arc::clone(&render_buffer),
        daq_data: Arc::clone(&daq_buffer),
    };

    let running = Arc::new(AtomicBool::new(true));

    // 1. Start the DAQ thread first
    let daq_running = Arc::clone(&running);
    let daq_buf = Arc::clone(&daq_buffer);
    let daq_thread = thread::spawn(move || {
        daq::daq(daq_buf, daq_running);
    });

    // Delay a few hundred milliseconds before starting the other threads
    thread::sleep(STARTUP_DELAY);

    // 2. Start display and renderer threads
    let display_running = Arc::clone(&running);
    let display_args = fast_copy_args.clone();
    let display_thread = thread::spawn(move || {
        display_frame::display_frame(display_args, display_running);
    });

    let render_running = Arc::clone(&running);
    let render_pack_clone = render_pack.clone();
    let render_thread = thread::spawn(move || {
        renderer::renderer(render_pack_clone, render_running);
    });

    // Await completion of all threads
    let _ = daq_thread.join();
    let _ = display_thread.join();
    let _ = render_thread.join();
}

