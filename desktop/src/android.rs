// Android: the page has no shell plugin there, so these commands start
// ocr-pdf-core for it (web/js/engine-android.js). Android only lets an app
// run programs from its native library folder, so the APK carries
// ocr-pdf-core and Ghostscript as libocr_pdf_core.so and libocr_pdf_gs.so
// (mk/apk.mk). What needs the Android APIs, such as that folder, the file
// picker and Downloads, is in AndroidPlugin.kt.

use std::fs;
use std::io::{BufRead, BufReader, Read};
use std::path::{Path, PathBuf};
use std::process::{Child, Command, Stdio};
use std::sync::Mutex;
use std::thread;

use serde::{de::DeserializeOwned, Deserialize, Serialize};
use tauri::ipc::Channel;
use tauri::plugin::{PluginHandle, TauriPlugin};
use tauri::{AppHandle, Builder, Manager, Wry};

const PLUGIN_PACKAGE: &str = "io.github.kseen715.ocr_pdf";
const PLUGIN_CLASS: &str = "AndroidPlugin";
// The exit code run_core reports when the core was stopped or never ran
const STOPPED: i32 = -1;

struct Device(PluginHandle<Wry>);

// The running core, so that cancel_core can kill it
#[derive(Default)]
struct Running {
    child: Option<Child>,
    cancelled: bool,
}

#[derive(Deserialize)]
struct Paths {
    core: String,
    gs: String,
    tessdata: String,
    cache: String,
}

#[derive(Serialize, Deserialize)]
struct Picked {
    name: String,
    uri: String,
}

#[derive(Deserialize)]
struct PickResult {
    files: Vec<Picked>,
}

#[derive(Serialize)]
struct Import<'a> {
    uri: &'a str,
    path: &'a str,
}

#[derive(Serialize)]
struct Save<'a> {
    path: &'a str,
    name: &'a str,
}

// A result in Downloads, under the name it got there
#[derive(Clone, Serialize, Deserialize)]
struct Saved {
    uri: String,
    name: String,
}

#[derive(Serialize)]
struct Open {
    uri: String,
}

#[derive(Deserialize)]
struct Nothing {}

// What run_core tells the page. The end comes through the same channel as
// the lines, so the page has seen every line when it learns the end.
#[derive(Clone, Serialize)]
#[serde(tag = "kind", rename_all = "camelCase")]
enum Event {
    // A line the core wrote, to stdout (JSON messages) or stderr
    Line { stderr: bool, text: String },
    // Its exit code, and the result in Downloads when the code is 0
    Finished { code: i32, saved: Option<Saved> },
}

// A failure outside the core, with the kind of explanation the user gets
// for it (web/js/tasks.js)
#[derive(Serialize)]
struct Failure {
    kind: &'static str,
    detail: String,
}

fn failure<E: ToString>(kind: &'static str) -> impl Fn(E) -> Failure {
    move |error| Failure { kind, detail: error.to_string() }
}

fn call<T: DeserializeOwned>(
    app: &AppHandle,
    command: &str,
    args: impl Serialize,
) -> Result<T, String> {
    let device = app.state::<Device>();
    device.0.run_mobile_plugin(command, args).map_err(|e| e.to_string())
}

fn utf8(path: &Path) -> String {
    path.to_string_lossy().into_owned()
}

// The page waits for these, so they run off the main thread
async fn blocking<T: Send + 'static>(
    job: impl FnOnce() -> Result<T, Failure> + Send + 'static,
) -> Result<T, Failure> {
    tauri::async_runtime::spawn_blocking(job)
        .await
        .map_err(failure("crash"))?
}

/// The system's file picker. The files stay where they are; run_core
/// copies one when its turn comes.
#[tauri::command]
async fn pick_files(app: AppHandle) -> Result<Vec<Picked>, Failure> {
    blocking(move || {
        let picked: PickResult =
            call(&app, "pick", ()).map_err(failure("other"))?;
        Ok(picked.files)
    })
    .await
}

/// Shows a result from Downloads in the app the user picks
#[tauri::command]
fn open_result(app: AppHandle, uri: String) -> Result<(), Failure> {
    call::<Nothing>(&app, "openFile", Open { uri }).map_err(failure("other"))?;
    Ok(())
}

/// Recognizes the file at input (a content:// URI) and saves the result
/// to Downloads as output, telling on_event how it goes
#[tauri::command]
async fn run_core(
    app: AppHandle,
    input: String,
    output: String,
    options: Vec<String>,
    on_event: Channel<Event>,
) -> Result<(), Failure> {
    app.state::<Mutex<Running>>().lock().unwrap().cancelled = false;
    blocking(move || recognize(&app, &input, &output, &options, &on_event))
        .await
}

/// Stops run_core: before the core starts, or by killing it, which also
/// kills its Ghostscript
#[tauri::command]
fn cancel_core(app: AppHandle) {
    let state = app.state::<Mutex<Running>>();
    let mut running = state.lock().unwrap();
    running.cancelled = true;
    if let Some(child) = running.child.as_mut() {
        let _ = child.kill();
    }
}

// The core works in a folder of the app's cache, emptied for every file.
// The input is copied there first: the core cannot read content:// URIs.
fn recognize(
    app: &AppHandle,
    input: &str,
    output: &str,
    options: &[String],
    on_event: &Channel<Event>,
) -> Result<(), Failure> {
    let paths: Paths = call(app, "paths", ()).map_err(failure("crash"))?;
    let work = PathBuf::from(&paths.cache).join("run");
    let _ = fs::remove_dir_all(&work);
    fs::create_dir_all(&work).map_err(failure("other"))?;
    let source = utf8(&work.join("input"));
    let result = utf8(&work.join(output));
    let import = Import { uri: input, path: &source };
    call::<Nothing>(app, "importFile", import).map_err(failure("other"))?;

    let mut args: Vec<String> = vec!["run".into()];
    for (flag, value) in [
        ("--input", source),
        ("--output", result.clone()),
        ("--tessdata", paths.tessdata),
        ("--gs", paths.gs),
    ] {
        args.extend([flag.into(), value]);
    }
    args.extend_from_slice(options);
    let code = run_program(app, &paths.core, &args, &work, on_event)
        .map_err(failure("crash"))?;

    let mut saved = None;
    if code == 0 {
        let save = Save { path: &result, name: output };
        let done = call(app, "saveFile", save);
        saved = Some(done.map_err(failure("output_access"))?);
    }
    let _ = fs::remove_dir_all(&work);
    let _ = on_event.send(Event::Finished { code, saved });
    Ok(())
}

// Runs program with args, sending what it writes to on_event; its
// temporary files go to temp. Returns its exit code.
fn run_program(
    app: &AppHandle,
    program: &str,
    args: &[String],
    temp: &Path,
    on_event: &Channel<Event>,
) -> Result<i32, String> {
    let state = app.state::<Mutex<Running>>();
    let (stdout, stderr) = {
        let mut running = state.lock().unwrap();
        if running.cancelled {
            return Ok(STOPPED);
        }
        let mut child = Command::new(program)
            .args(args)
            .env("TMPDIR", temp)
            .stdin(Stdio::null())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .spawn()
            .map_err(|e| format!("{program}: {e}"))?;
        let pipes = (child.stdout.take(), child.stderr.take());
        running.child = Some(child);
        pipes
    };

    let errors = on_event.clone();
    let stderr = thread::spawn(move || send_lines(stderr, true, &errors));
    send_lines(stdout, false, on_event);
    let _ = stderr.join();

    let child = state.lock().unwrap().child.take();
    let status = child.map(|mut child| child.wait());
    Ok(match status {
        Some(Ok(status)) => status.code().unwrap_or(STOPPED),
        _ => STOPPED,
    })
}

fn send_lines(
    pipe: Option<impl Read>,
    stderr: bool,
    on_event: &Channel<Event>,
) {
    let Some(pipe) = pipe else { return };
    for text in BufReader::new(pipe).lines().map_while(Result::ok) {
        let _ = on_event.send(Event::Line { stderr, text });
    }
}

fn plugin() -> TauriPlugin<Wry> {
    tauri::plugin::Builder::new("android")
        .setup(|app, api| {
            let handle =
                api.register_android_plugin(PLUGIN_PACKAGE, PLUGIN_CLASS)?;
            app.manage(Device(handle));
            Ok(())
        })
        .build()
}

pub fn platform(builder: Builder<Wry>) -> Builder<Wry> {
    builder
        .plugin(plugin())
        .manage(Mutex::new(Running::default()))
        .invoke_handler(tauri::generate_handler![
            pick_files,
            open_result,
            run_core,
            cancel_core
        ])
}
