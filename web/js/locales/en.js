// The interface in English; see ru.js

export default {
    'theme.group': 'Colour theme',
    'theme.sakura': 'Sakura',
    'theme.sakura-dark': 'Sakura · Dark',
    'theme.wine': 'Wine',
    'theme.wine-dark': 'Wine · Dark',
    'theme.rust': 'Rust',
    'theme.rust-dark': 'Rust · Dark',
    'locale.group': 'Interface language',

    'intro.desktop': 'The program reads the text on scans and photos of ' +
        'documents. The original file stays as it is: a new one appears ' +
        'next to it, with “{suffix}” at the end of its name.',
    'intro.android': 'The program reads the text on scans and photos of ' +
        'documents. The original file stays as it is: the finished PDF ' +
        'is saved to the Downloads folder.',
    'intro.web': 'CUBE-PDF recognizes the text on scans and photos of ' +
        'documents (OCR) with Tesseract. It runs right on your device: ' +
        'files are not sent anywhere and never leave it. The finished ' +
        'PDF, whose text you can search and copy, is downloaded with the ' +
        '“Download” button next to the file’s name.',
    'native': 'The Windows and Linux app recognizes faster than the ' +
        'browser. You can download it from the',
    'native.link': 'releases page on GitHub',

    'files.title': 'Files',
    'files.clear': 'Clear list',
    'files.count': {
        one: '{count} file',
        other: '{count} files',
    },
    'files.done': '{count} done',
    'files.failed': '{count} failed',
    'files.rejected': 'Skipped (not PDFs or images): {names}',
    'drop.title': 'Drop files or a folder here',
    'drop.titleTouch': 'Choose files',
    'drop.click': 'or click to choose.',
    'drop.types': 'PDF, JPG, PNG and TIFF work.',
    'drop.again': 'Add files',
    'filter.supported': 'PDFs and images',
    'filter.all': 'All files',

    'settings': 'Recognition settings',
    'languages.title': 'Language of the text',
    'languages.note': 'You can tick several. Not sure? Leave it as it is.',
    'languages.keepOne': 'At least one language must stay ticked.',
    'language.rus': 'Russian',
    'language.eng': 'English',
    'language.deu': 'German',
    'language.ita': 'Italian',
    'processing.title': 'Processing',
    'processing.deskew': 'Straighten tilted pages',
    'processing.force': 'Recognize again, even if the file already has ' +
        'text',
    'start': 'Start recognition',
    'stop': 'Stop',

    'status.file': 'File {index} of {count}: ',
    'status.stopping': 'Stopping…',
    'status.stopped': 'Stopped.',
    'status.summary': 'Done in {took}. Succeeded: {done}.',
    'status.summaryFailed': 'Done in {took}. Succeeded: {done}, failed: ' +
        '{failed}.',
    'time.minutes': '{minutes} min {seconds} s',
    'time.seconds': '{seconds} s',

    'stage.start': 'Starting',
    'stage.scan': 'Examining the file',
    'stage.ocr': 'Recognizing text',
    'stage.save': 'Saving the document',
    'stage.other': 'Processing',
    'stage.page': '{stage}: page {page} of {total}',

    'task.waiting': 'Waiting',
    'task.done': 'Done',
    'task.failed': 'Error',
    'task.cancelled': 'Stopped',
    'task.reason': 'Why',
    'task.willBe': 'Will become {output}',
    'task.savedAs': 'Saved as {output}',
    'task.pages': ' pp.',
    'task.log': 'Log:',
    'action.open': 'Open',
    'action.download': 'Download',

    'error.encrypted': 'The file is password-protected. Remove the ' +
        'password and try again.',
    'error.has_text': 'The file already has text. To recognize it ' +
        'again, tick “Recognize again” under “Processing”.',
    'error.output_access': 'Could not save the result. The file ' +
        '“{output}” is probably open in another program. Close it and ' +
        'try again.',
    'error.bad_input': 'The file is damaged, or it is not a PDF or an ' +
        'image.',
    'error.missing_dependency': 'The program was built wrong: one of ' +
        'its parts is missing.',
    'error.too_big': 'The file is too big: the computer ran out of ' +
        'memory.',
    'error.other': 'Something went wrong.',
    'error.crash': 'Recognition stopped unexpectedly.',

    'dialog.close': 'Close',
    'dialog.yes': 'Yes',
    'dialog.no': 'No',
    'dialog.details': 'Details',
    'dialog.openFile': 'Open file',
    'dialog.reveal': 'Show in folder',
    'done.one': 'Done! The new file:\n\n{output}\n\n{where}',
    'done.many': 'Done! Files recognized: {count}.\n{where}',
    'done.someFailed': 'Failed: {count}. {hint}',
    'done.failedHint': 'The “Why” button in the file list tells why.',
    'done.allFailed': 'None of the files could be recognized.\n{hint}',
    'done.error': 'Could not recognize the file\n“{name}”.\n\n{error}',
    'where.besideOne': 'It is next to the original.',
    'where.besideMany': 'The new files are next to the originals.',
    'where.downloadsOne': 'It is saved in the Downloads folder.',
    'where.downloadsMany': 'The new files are saved in the Downloads ' +
        'folder.',
    'close.running': 'Recognition is still running. Stop it and close ' +
        'the program?',

    'update.title': 'Update',
    'update.available': 'A new version is out',
    'update.question': 'A new version is out: {from} → {to}.\n\n' +
        '{question}',
    'update.install': 'Download and install it?',
    'update.openPage': 'Open the page where you can download it?',
    'update.whenDone': 'The program can be updated when recognition ' +
        'is over.',
    'update.downloading': 'Downloading the update…',
    'update.downloadingPercent': 'Downloading the update… {percent} %',
    'update.failed': 'Could not install the update. You can download it ' +
        'yourself from the releases page on GitHub.',

    'about.link': 'About and licenses',
    'about.title': 'About {app}',
    'about.license': 'This is free software: you can redistribute and ' +
        'modify it under the terms of the ' +
        'GNU Affero General Public License version 3 or (at your option) ' +
        'any later version.',
    'about.warranty': 'This program comes <b>without any warranty</b>, ' +
        'without even the implied warranty of merchantability or fitness ' +
        'for a particular purpose.',
    'about.source': 'Source code:',
    'about.inside': 'Inside: Tesseract, Leptonica, MuPDF, Ghostscript, ' +
        'zlib and other free components. Their licenses, and where to ' +
        'get their source code, are behind the “{notices}” button.',
    'about.licenseFile': 'Program license',
    'about.noticesFile': 'Third-party components',
    'about.missing': 'File not found: {name}',
};
