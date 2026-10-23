//! Shared buffer types and synchronized structures

use std::sync::{Arc, Condvar, Mutex};

/// Synchronized frame buffer holding dimensions and mutex-protected pixel data
pub struct SyncFrame {
    pub width: u16,
    pub height: u16,
    pub data: Mutex<Vec<u8>>,
}

impl SyncFrame {
    pub fn new(width: u16, height: u16) -> Self {
        let size = (width as usize) * (height as usize);
        Self {
            width,
            height,
            data: Mutex::new(vec![0u8; size]),
        }
    }
}

pub type SharedFrame = Arc<SyncFrame>;

/// Internal state for data acquisition buffer
pub struct DaqState {
    pub buffer: Vec<u16>,
    pub has_new_data: bool,
}

/// Synchronized DAQ buffer with mutex and condition variable
pub struct DaqBuffer {
    pub state: Mutex<DaqState>,
    pub cond: Condvar,
    pub size: usize,
}

impl DaqBuffer {
    pub fn new(size: usize) -> Self {
        Self {
            state: Mutex::new(DaqState {
                buffer: vec![0u16; size],
                has_new_data: false,
            }),
            cond: Condvar::new(),
            size,
        }
    }
}

pub type SharedDaqBuffer = Arc<DaqBuffer>;

/// Fast copy argument holding source and destination frames
#[derive(Clone)]
pub struct FastCopyArgs {
    pub src: SharedFrame,
    pub dest: SharedFrame,
}

/// Render pack holding frame buffer and DAQ buffer
#[derive(Clone)]
pub struct RenderPack {
    pub frame_buffer: SharedFrame,
    pub daq_data: SharedDaqBuffer,
}

