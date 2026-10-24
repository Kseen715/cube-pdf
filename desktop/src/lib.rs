// The app shell: one window with the page from web/ and the plugins it
// uses. The OCR itself runs in ocr-pdf-core. On the desktop the page starts
// it as a sidecar through the shell plugin (web/js/engine-desktop.js); on
// Android, which has no such plugin, through android.rs. Both download and
// install their updates through update.rs.

#[cfg(target_os = "android")]
mod android;
mod update;

#[cfg(not(target_os = "android"))]
use tauri::{Builder, Wry};

/// Files the app was started with, for example dropped onto its icon
#[cfg(not(target_os = "android"))]
#[tauri::command]
fn startup_paths() -> Vec<String> {
    std::env::args().skip(1).collect()
}

#[cfg(not(target_os = "android"))]
fn platform(builder: Builder<Wry>) -> Builder<Wry> {
    builder
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_shell::init())
        .invoke_handler(tauri::generate_handler![
            startup_paths,
            update::update_package,
            update::install_update
        ])
}

#[cfg(target_os = "android")]
use android::platform;

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    platform(tauri::Builder::default())
        .run(tauri::generate_context!())
        .expect("the window could not start");
}
