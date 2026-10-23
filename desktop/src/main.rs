// The desktop app; the shell itself is in lib.rs, shared with Android

// No console window next to the app on Windows
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

fn main() {
    ocr_pdf_lib::run();
}
