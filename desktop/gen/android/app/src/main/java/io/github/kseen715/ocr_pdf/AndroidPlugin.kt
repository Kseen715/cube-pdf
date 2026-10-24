// The Android side of desktop/src/android.rs: what needs the Android APIs.
// Its commands run on the thread of the Rust code that calls them, which
// is never the main one, so they may copy files.
package io.github.kseen715.ocr_pdf

import android.app.Activity
import android.content.ContentValues
import android.content.Intent
import android.net.Uri
import android.provider.MediaStore
import android.provider.OpenableColumns
import androidx.activity.result.ActivityResult
import androidx.core.content.FileProvider
import app.tauri.annotation.ActivityCallback
import app.tauri.annotation.Command
import app.tauri.annotation.InvokeArg
import app.tauri.annotation.TauriPlugin
import app.tauri.plugin.Invoke
import app.tauri.plugin.JSArray
import app.tauri.plugin.JSObject
import app.tauri.plugin.Plugin
import java.io.File
import java.io.IOException

// The programs mk/apk.mk packs as libraries, in the native library folder
private const val CORE = "libocr_pdf_core.so"
private const val GS = "libocr_pdf_gs.so"
// The language models mk/apk.mk puts into the APK's assets
private const val TESSDATA = "tessdata"
private const val PDF = "application/pdf"
private const val APK = "application/vnd.android.package-archive"
// The FileProvider of AndroidManifest.xml, which shares the updates
private const val FILES = ".files"
// What the picker offers, as web/js/config.js INPUT_EXTENSIONS
private val INPUT_TYPES = arrayOf(PDF, "image/jpeg", "image/png", "image/tiff")

@InvokeArg
class ImportArgs {
    lateinit var uri: String
    lateinit var path: String
}

@InvokeArg
class SaveArgs {
    lateinit var path: String
    lateinit var name: String
}

@InvokeArg
class OpenArgs {
    lateinit var uri: String
}

@InvokeArg
class InstallArgs {
    lateinit var path: String
}

@TauriPlugin
class AndroidPlugin(private val activity: Activity) : Plugin(activity) {
    private val resolver get() = activity.contentResolver

    // Fails the invoke instead of the app when work throws
    private fun answer(invoke: Invoke, work: () -> JSObject?) {
        try {
            invoke.resolve(work())
        } catch (e: Exception) {
            invoke.reject(e.message ?: e.toString())
        }
    }

    @Command
    fun paths(invoke: Invoke) = answer(invoke) {
        val libraries = activity.applicationInfo.nativeLibraryDir
        JSObject().apply {
            put("core", "$libraries/$CORE")
            put("gs", "$libraries/$GS")
            put("tessdata", tessdata().path)
            put("cache", activity.cacheDir.path)
        }
    }

    // The core reads the models from files, so they are copied out of the
    // APK once per installed version of the app
    private fun tessdata(): File {
        val installed = activity.packageManager
            .getPackageInfo(activity.packageName, 0).lastUpdateTime
        val folder = File(activity.filesDir, "$TESSDATA-$installed")
        if (folder.isDirectory) return folder

        activity.filesDir.listFiles()?.filter {
            it.name.startsWith("$TESSDATA-")
        }?.forEach { it.deleteRecursively() }
        val part = File(activity.filesDir, "$TESSDATA.part")
        part.deleteRecursively()
        part.mkdirs()
        for (name in activity.assets.list(TESSDATA).orEmpty()) {
            activity.assets.open("$TESSDATA/$name").use { input ->
                File(part, name).outputStream().use { input.copyTo(it) }
            }
        }
        if (!part.renameTo(folder)) throw IOException("cannot write $folder")
        return folder
    }

    @Command
    fun pick(invoke: Invoke) {
        val intent = Intent(Intent.ACTION_OPEN_DOCUMENT).apply {
            addCategory(Intent.CATEGORY_OPENABLE)
            type = "*/*"
            putExtra(Intent.EXTRA_MIME_TYPES, INPUT_TYPES)
            putExtra(Intent.EXTRA_ALLOW_MULTIPLE, true)
        }
        startActivityForResult(invoke, intent, "picked")
    }

    @ActivityCallback
    fun picked(invoke: Invoke, result: ActivityResult) = answer(invoke) {
        val data = result.data
        val uris = mutableListOf<Uri>()
        if (result.resultCode == Activity.RESULT_OK && data != null) {
            val clip = data.clipData
            if (clip != null) {
                for (i in 0 until clip.itemCount)
                    uris.add(clip.getItemAt(i).uri)
            } else {
                data.data?.let { uris.add(it) }
            }
        }

        val files = JSArray()
        for (uri in uris) {
            files.put(JSObject().apply {
                put("uri", uri.toString())
                put("name", displayName(uri))
            })
        }
        JSObject().apply { put("files", files) }
    }

    private fun displayName(uri: Uri): String {
        val column = arrayOf(OpenableColumns.DISPLAY_NAME)
        resolver.query(uri, column, null, null, null)?.use { row ->
            if (row.moveToFirst() && !row.isNull(0)) return row.getString(0)
        }
        return uri.lastPathSegment ?: uri.toString()
    }

    @Command
    fun importFile(invoke: Invoke) = answer(invoke) {
        val args = invoke.parseArgs(ImportArgs::class.java)
        val input = resolver.openInputStream(Uri.parse(args.uri))
            ?: throw IOException("cannot read ${args.uri}")
        input.use { from ->
            File(args.path).outputStream().use { from.copyTo(it) }
        }
        null
    }

    // Into Downloads, which needs no permission since Android 10. A name
    // that is taken gets a number from Android, so the answer has the name
    // the file really got.
    @Command
    fun saveFile(invoke: Invoke) = answer(invoke) {
        val args = invoke.parseArgs(SaveArgs::class.java)
        val values = ContentValues().apply {
            put(MediaStore.Downloads.DISPLAY_NAME, args.name)
            put(MediaStore.Downloads.MIME_TYPE, PDF)
            put(MediaStore.Downloads.IS_PENDING, 1)
        }
        val uri = resolver.insert(MediaStore.Downloads.EXTERNAL_CONTENT_URI,
            values) ?: throw IOException("Downloads refused ${args.name}")
        try {
            val output = resolver.openOutputStream(uri)
                ?: throw IOException("cannot write $uri")
            output.use { out ->
                File(args.path).inputStream().use { it.copyTo(out) }
            }
            values.clear()
            values.put(MediaStore.Downloads.IS_PENDING, 0)
            resolver.update(uri, values, null, null)
        } catch (e: Exception) {
            resolver.delete(uri, null, null)
            throw e
        }
        JSObject().apply {
            put("uri", uri.toString())
            put("name", displayName(uri))
        }
    }

    @Command
    fun openFile(invoke: Invoke) = answer(invoke) {
        val args = invoke.parseArgs(OpenArgs::class.java)
        val view = Intent(Intent.ACTION_VIEW)
            .setDataAndType(Uri.parse(args.uri), PDF)
            .addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
        activity.startActivity(Intent.createChooser(view, null))
        null
    }

    // An update that desktop/src/update.rs downloaded. The installer asks
    // the user, the first time also for the right to install apps from
    // CUBE-PDF, and replaces the app when it has the same signature.
    @Command
    fun installApk(invoke: Invoke) = answer(invoke) {
        val args = invoke.parseArgs(InstallArgs::class.java)
        val authority = activity.packageName + FILES
        val uri = FileProvider.getUriForFile(activity, authority,
            File(args.path))
        val install = Intent(Intent.ACTION_VIEW)
            .setDataAndType(uri, APK)
            .addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
        activity.startActivity(install)
        null
    }
}
