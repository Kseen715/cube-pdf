// The interface in German; see ru.js

export default {
    'theme.group': 'Farbschema',
    'theme.sakura': 'Sakura',
    'theme.sakura-dark': 'Sakura · Dunkel',
    'theme.wine': 'Wein',
    'theme.wine-dark': 'Wein · Dunkel',
    'theme.rust': 'Rost',
    'theme.rust-dark': 'Rost · Dunkel',
    'locale.group': 'Sprache der Oberfläche',

    'intro.desktop': 'Das Programm liest den Text auf Scans und Fotos ' +
        'von Dokumenten. Die Originaldatei bleibt unverändert: Daneben ' +
        'entsteht eine neue, mit „{suffix}“ am Ende des Namens.',
    'intro.android': 'Das Programm liest den Text auf Scans und Fotos ' +
        'von Dokumenten. Die Originaldatei bleibt unverändert: Das ' +
        'fertige PDF wird im Ordner „Downloads“ gespeichert.',
    'intro.web': 'CUBE-PDF erkennt den Text auf Scans und Fotos von ' +
        'Dokumenten (OCR) mit Tesseract. Die Erkennung läuft direkt auf ' +
        'Ihrem Gerät: Die Dateien werden nirgendwohin gesendet und ' +
        'verlassen es nicht. Das fertige PDF, in dem sich Text suchen ' +
        'und kopieren lässt, laden Sie mit der Schaltfläche ' +
        '„Herunterladen“ neben dem Dateinamen herunter.',
    'native': 'Die App für Windows und Linux erkennt schneller als der ' +
        'Browser. Herunterladen können Sie sie auf der',
    'native.link': 'Release-Seite auf GitHub',

    'files.title': 'Dateien',
    'files.clear': 'Liste leeren',
    'files.count': {
        one: '{count} Datei',
        other: '{count} Dateien',
    },
    'files.done': '{count} fertig',
    'files.failed': '{count} mit Fehler',
    'files.rejected': 'Übersprungen (weder PDF noch Bild): {names}',
    'drop.title': 'Dateien oder einen Ordner hierher ziehen',
    'drop.titleTouch': 'Dateien auswählen',
    'drop.click': 'oder klicken, um sie auszuwählen.',
    'drop.types': 'Geeignet sind PDF, JPG, PNG und TIFF.',
    'drop.again': 'Dateien hinzufügen',
    'filter.supported': 'PDF und Bilder',
    'filter.all': 'Alle Dateien',

    'settings': 'Einstellungen der Erkennung',
    'languages.title': 'Sprache des Textes',
    'languages.note': 'Mehrere sind möglich. Im Zweifel so lassen, wie ' +
        'es ist.',
    'languages.keepOne': 'Mindestens eine Sprache muss ausgewählt ' +
        'bleiben.',
    'language.rus': 'Russisch',
    'language.eng': 'Englisch',
    'language.deu': 'Deutsch',
    'language.ita': 'Italienisch',
    'processing.title': 'Bearbeitung',
    'processing.deskew': 'Schiefe Seiten gerade richten',
    'processing.force': 'Neu erkennen, auch wenn die Datei schon Text ' +
        'enthält',
    'start': 'Erkennung starten',
    'stop': 'Anhalten',

    'status.file': 'Datei {index} von {count}: ',
    'status.stopping': 'Wird angehalten…',
    'status.stopped': 'Angehalten.',
    'status.summary': 'Fertig in {took}. Erfolgreich: {done}.',
    'status.summaryFailed': 'Fertig in {took}. Erfolgreich: {done}, ' +
        'fehlgeschlagen: {failed}.',
    'time.minutes': '{minutes} min {seconds} s',
    'time.seconds': '{seconds} s',

    'stage.start': 'Wird gestartet',
    'stage.scan': 'Datei wird untersucht',
    'stage.ocr': 'Text wird erkannt',
    'stage.save': 'Dokument wird gespeichert',
    'stage.other': 'Wird bearbeitet',
    'stage.page': '{stage}: Seite {page} von {total}',

    'task.waiting': 'Wartet',
    'task.done': 'Fertig',
    'task.failed': 'Fehler',
    'task.cancelled': 'Angehalten',
    'task.reason': 'Grund',
    'task.willBe': 'Wird zu {output}',
    'task.savedAs': 'Gespeichert als {output}',
    'task.pages': ' S.',
    'task.log': 'Protokoll:',
    'action.open': 'Öffnen',
    'action.download': 'Herunterladen',

    'error.encrypted': 'Die Datei ist mit einem Passwort geschützt. ' +
        'Entfernen Sie das Passwort und versuchen Sie es noch einmal.',
    'error.has_text': 'Die Datei enthält schon Text. Um sie neu zu ' +
        'erkennen, wählen Sie „Neu erkennen“ unter „Bearbeitung“.',
    'error.output_access': 'Das Ergebnis konnte nicht gespeichert ' +
        'werden. Wahrscheinlich ist die Datei „{output}“ in einem ' +
        'anderen Programm geöffnet. Schließen Sie sie und versuchen Sie ' +
        'es noch einmal.',
    'error.bad_input': 'Die Datei ist beschädigt, oder sie ist weder ' +
        'PDF noch Bild.',
    'error.missing_dependency': 'Das Programm ist fehlerhaft gebaut: ' +
        'Ein Bestandteil fehlt.',
    'error.too_big': 'Die Datei ist zu groß: Der Arbeitsspeicher hat ' +
        'nicht gereicht.',
    'error.other': 'Etwas ist schiefgegangen.',
    'error.crash': 'Die Erkennung wurde unerwartet abgebrochen.',

    'dialog.close': 'Schließen',
    'dialog.yes': 'Ja',
    'dialog.no': 'Nein',
    'dialog.details': 'Details',
    'dialog.openFile': 'Datei öffnen',
    'dialog.reveal': 'Im Ordner zeigen',
    'done.one': 'Fertig! Die neue Datei:\n\n{output}\n\n{where}',
    'done.many': 'Fertig! Erkannte Dateien: {count}.\n{where}',
    'done.someFailed': 'Fehlgeschlagen: {count}. {hint}',
    'done.failedHint': 'Warum, zeigt die Schaltfläche „Grund“ in der ' +
        'Dateiliste.',
    'done.allFailed': 'Keine der Dateien konnte erkannt werden.\n{hint}',
    'done.error': 'Die Datei\n„{name}“\nkonnte nicht erkannt werden.' +
        '\n\n{error}',
    'where.besideOne': 'Sie liegt neben dem Original.',
    'where.besideMany': 'Die neuen Dateien liegen neben den Originalen.',
    'where.downloadsOne': 'Sie ist im Ordner „Downloads“ gespeichert.',
    'where.downloadsMany': 'Die neuen Dateien sind im Ordner ' +
        '„Downloads“ gespeichert.',
    'close.running': 'Die Erkennung läuft noch. Anhalten und das ' +
        'Programm schließen?',

    'update.title': 'Update',
    'update.available': 'Eine neue Version ist erschienen',
    'update.question': 'Eine neue Version ist erschienen: {from} → ' +
        '{to}.\n\n{question}',
    'update.install': 'Herunterladen und installieren?',
    'update.openPage': 'Die Seite öffnen, auf der sie zum Download ' +
        'steht?',
    'update.whenDone': 'Das Programm lässt sich aktualisieren, wenn die ' +
        'Erkennung fertig ist.',
    'update.downloading': 'Update wird heruntergeladen…',
    'update.downloadingPercent': 'Update wird heruntergeladen… ' +
        '{percent} %',
    'update.failed': 'Das Update konnte nicht installiert werden. Sie ' +
        'können es auf der Release-Seite auf GitHub selbst herunterladen.',

    'about.link': 'Über das Programm und Lizenzen',
    'about.title': 'Über {app}',
    'about.license': 'Dies ist freie Software: Sie können sie unter den ' +
        'Bedingungen der GNU Affero General Public License, Version 3 ' +
        'oder (nach Ihrer Wahl) jeder späteren Version, weitergeben und ' +
        'verändern.',
    'about.warranty': 'Das Programm wird <b>ohne jede Gewährleistung</b> ' +
        'verbreitet, sogar ohne die implizite Gewährleistung der ' +
        'Marktreife oder der Eignung für einen bestimmten Zweck.',
    'about.source': 'Quellcode:',
    'about.inside': 'Enthalten: Tesseract, Leptonica, MuPDF, ' +
        'Ghostscript, zlib und weitere freie Komponenten. Ihre Lizenzen ' +
        'und wo es ihren Quellcode gibt, zeigt die Schaltfläche ' +
        '„{notices}“.',
    'about.licenseFile': 'Lizenz des Programms',
    'about.noticesFile': 'Komponenten Dritter',
    'about.missing': 'Datei nicht gefunden: {name}',
};
