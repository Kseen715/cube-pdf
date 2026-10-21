// The desktop shell: one window with the page from web/ and the plugins it
// uses. The OCR itself runs in the ocr-pdf-core sidecar, which the page
// starts through the shell plugin (see web/js/engine-desktop.js).

// No console window next to the app on Windows
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

/// Files the app was started with, for example dropped onto its icon
#[tauri::command]
fn startup_paths() -> Vec<String> {
    std::env::args().skip(1).collect()
}

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_shell::init())
        .invoke_handler(tauri::generate_handler![startup_paths])
        .run(tauri::generate_context!())
        .expect("the window could not start");
}
