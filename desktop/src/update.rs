// Updates from the releases of the repository named in Cargo.toml. The page
// finds a newer release and the file of it for this app (web/js/update.js);
// these commands download that file and install it the way the app was
// installed: with its NSIS installer on Windows, with dpkg or rpm through
// pkexec on Linux, with the system's package installer on Android.

use std::fs::{self, File};
use std::io::{Read, Write};
use std::path::{Path, PathBuf};

use tauri::ipc::Channel;
use tauri::AppHandle;

const REPOSITORY: &str = env!("CARGO_PKG_REPOSITORY");
const CHUNK: usize = 1 << 16;

fn text<E: ToString>(error: E) -> String {
    error.to_string()
}

/// The kind of package the app was installed from, as web/js/config.js
/// UPDATE_FILES names it; None when the app cannot install updates itself
#[tauri::command]
pub fn update_package() -> Option<&'static str> {
    platform::package()
}

/// Downloads the file name, of size bytes, of the release tag and installs
/// it; on_percent hears how far the download is
#[tauri::command]
pub async fn install_update(
    app: AppHandle,
    tag: String,
    name: String,
    size: u64,
    on_percent: Channel<u64>,
) -> Result<(), String> {
    let url = release_url(&tag, &name)?;
    tauri::async_runtime::spawn_blocking(move || {
        let folder = platform::download_dir(&app)?;
        fs::create_dir_all(&folder).map_err(text)?;
        let path = folder.join(&name);
        download(&url, &path, size, &on_percent)?;
        platform::install(&app, &path)
    })
    .await
    .map_err(text)?
}

// The page could ask for anything; only plain names keep the download
// among the files of this repository's releases
fn release_url(tag: &str, name: &str) -> Result<String, String> {
    let allowed = |c: char| c.is_ascii_alphanumeric() || "._+-".contains(c);
    let plain = |part: &str| {
        !part.is_empty() && !part.starts_with('.') && part.chars().all(allowed)
    };
    if !plain(tag) || !plain(name) {
        return Err(format!("not a release file: {tag}/{name}"));
    }
    Ok(format!("{REPOSITORY}/releases/download/{tag}/{name}"))
}

// A file of another size than GitHub lists is not installed. ureq fails a
// body that reaches its limit, so the limit is one byte more.
fn download(
    url: &str,
    path: &Path,
    size: u64,
    on_percent: &Channel<u64>,
) -> Result<(), String> {
    let response = ureq::get(url).call().map_err(text)?;
    let body = response.into_body().into_with_config();
    let mut body = body.limit(size + 1).reader();
    let mut file = File::create(path).map_err(text)?;
    let mut buffer = vec![0; CHUNK];
    let (mut done, mut shown) = (0, 0);
    loop {
        let read = body.read(&mut buffer).map_err(text)?;
        if read == 0 {
            break;
        }
        file.write_all(&buffer[..read]).map_err(text)?;
        done += read as u64;
        let percent = done * 100 / size.max(1);
        if percent != shown {
            shown = percent;
            let _ = on_percent.send(percent);
        }
    }

    if done != size {
        return Err(format!("{url}: got {done} of {size} bytes"));
    }
    Ok(())
}

#[cfg(windows)]
mod platform {
    use super::*;
    use std::process::Command;

    pub fn package() -> Option<&'static str> {
        // The installer leaves its uninstaller next to the app; the
        // portable zip has none
        let exe = std::env::current_exe().ok()?;
        exe.with_file_name("uninstall.exe").is_file().then_some("windows")
    }

    pub fn download_dir(_: &AppHandle) -> Result<PathBuf, String> {
        Ok(std::env::temp_dir())
    }

    // The installer replaces the app's files, so the app quits for it. In
    // Tauri's installer.nsi /P shows only the progress and /R starts the
    // new version once it is installed.
    pub fn install(app: &AppHandle, installer: &Path) -> Result<(), String> {
        Command::new(installer)
            .args(["/P", "/R", "/UPDATE"])
            .spawn()
            .map_err(text)?;
        app.exit(0);
        Ok(())
    }
}

#[cfg(target_os = "linux")]
mod platform {
    use super::*;
    use std::process::Command;

    struct Manager {
        kind: &'static str,
        // The tool and its query for the package that owns a file
        owner: [&'static str; 2],
        // The same tool and its command that installs a newer package
        upgrade: [&'static str; 2],
    }

    const MANAGERS: [Manager; 2] = [
        Manager { kind: "deb", owner: ["dpkg", "-S"], upgrade: ["dpkg", "-i"] },
        Manager { kind: "rpm", owner: ["rpm", "-qf"], upgrade: ["rpm", "-U"] },
    ];

    fn manager() -> Option<&'static Manager> {
        let exe = std::env::current_exe().ok()?;
        MANAGERS.iter().find(|manager| {
            let [tool, query] = manager.owner;
            Command::new(tool)
                .arg(query)
                .arg(&exe)
                .output()
                .is_ok_and(|output| output.status.success())
        })
    }

    pub fn package() -> Option<&'static str> {
        manager().map(|manager| manager.kind)
    }

    pub fn download_dir(_: &AppHandle) -> Result<PathBuf, String> {
        Ok(std::env::temp_dir())
    }

    // pkexec asks for the password in the desktop's own dialog. The
    // program's path is taken first: once the package replaced it, the
    // running one no longer has it.
    pub fn install(app: &AppHandle, package: &Path) -> Result<(), String> {
        let exe = std::env::current_exe().map_err(text)?;
        let manager =
            manager().ok_or("the app was not installed from a package")?;
        let [tool, flag] = manager.upgrade;
        let status = Command::new("pkexec")
            .args([tool, flag])
            .arg(package)
            .status()
            .map_err(text)?;
        let _ = fs::remove_file(package);
        if !status.success() {
            return Err(format!("pkexec {tool} {flag}: {status}"));
        }

        Command::new(exe).spawn().map_err(text)?;
        app.exit(0);
        Ok(())
    }
}

#[cfg(target_os = "android")]
mod platform {
    use super::*;

    pub fn package() -> Option<&'static str> {
        Some("android")
    }

    // The folder AndroidPlugin.kt shares with the system's installer
    pub fn download_dir(app: &AppHandle) -> Result<PathBuf, String> {
        Ok(crate::android::cache_dir(app)?.join("updates"))
    }

    pub fn install(app: &AppHandle, apk: &Path) -> Result<(), String> {
        crate::android::install_apk(app, apk)
    }
}
