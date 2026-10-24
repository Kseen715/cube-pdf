// The interface in Italian; see ru.js

export default {
    'theme.group': 'Tema',
    'theme.light': 'Chiaro',
    'theme.dark': 'Scuro',
    'theme.auto': 'Come il sistema',
    'locale.group': 'Lingua dell’interfaccia',

    'title': 'Creare un PDF in cui si può cercare il testo',
    'intro.desktop': 'Il programma legge il testo di scansioni e foto di ' +
        'documenti. Il file originale non cambia: accanto ne compare uno ' +
        'nuovo, con «{suffix}» alla fine del nome.',
    'intro.android': 'Il programma legge il testo di scansioni e foto di ' +
        'documenti. Il file originale non cambia: il PDF finito viene ' +
        'salvato nella cartella «Download».',
    'intro.web': 'CUBE-PDF riconosce il testo di scansioni e foto di ' +
        'documenti (OCR) con Tesseract. Il riconoscimento avviene ' +
        'direttamente sul tuo dispositivo: i file non vengono inviati da ' +
        'nessuna parte e non lo lasciano mai. Il PDF finito, in cui si ' +
        'può cercare e copiare il testo, si scarica con il pulsante ' +
        '«Scarica» accanto al nome del file.',
    'native': 'L’app per Windows e Linux riconosce più in fretta del ' +
        'browser. Puoi scaricarla dalla',
    'native.link': 'pagina delle release su GitHub',

    'files.title': 'File',
    'files.clear': 'Svuota l’elenco',
    'files.count': {
        one: '{count} file',
        other: '{count} file',
    },
    'files.done': '{count} pronti',
    'files.failed': '{count} con errore',
    'files.rejected': 'Saltati (non sono PDF né immagini): {names}',
    'drop.title': 'Trascina qui file o una cartella',
    'drop.titleTouch': 'Scegli i file',
    'drop.click': 'oppure fai clic per sceglierli.',
    'drop.types': 'Vanno bene PDF, JPG, PNG e TIFF.',
    'drop.again': 'Aggiungi file',
    'filter.supported': 'PDF e immagini',
    'filter.all': 'Tutti i file',

    'settings': 'Impostazioni del riconoscimento',
    'languages.title': 'Lingua del testo',
    'languages.note': 'Se ne possono scegliere più di una. Nel dubbio, ' +
        'lascia com’è.',
    'languages.keepOne': 'Deve restare scelta almeno una lingua.',
    'language.rus': 'Russo',
    'language.eng': 'Inglese',
    'language.deu': 'Tedesco',
    'language.ita': 'Italiano',
    'processing.title': 'Elaborazione',
    'processing.deskew': 'Raddrizza le pagine storte',
    'processing.force': 'Riconosci di nuovo, anche se il file ha già del ' +
        'testo',
    'start': 'Avvia il riconoscimento',
    'stop': 'Ferma',

    'status.file': 'File {index} di {count}: ',
    'status.stopping': 'Arresto in corso…',
    'status.stopped': 'Fermato.',
    'status.summary': 'Fatto in {took}. Riusciti: {done}.',
    'status.summaryFailed': 'Fatto in {took}. Riusciti: {done}, non ' +
        'riusciti: {failed}.',
    'time.minutes': '{minutes} min {seconds} s',
    'time.seconds': '{seconds} s',

    'stage.start': 'Avvio',
    'stage.scan': 'Esame del file',
    'stage.ocr': 'Riconoscimento del testo',
    'stage.save': 'Salvataggio del documento',
    'stage.other': 'Elaborazione',
    'stage.page': '{stage}: pagina {page} di {total}',

    'task.waiting': 'In attesa',
    'task.done': 'Pronto',
    'task.failed': 'Errore',
    'task.cancelled': 'Fermato',
    'task.reason': 'Motivo',
    'task.willBe': 'Diventerà {output}',
    'task.savedAs': 'Salvato come {output}',
    'task.pages': ' pag.',
    'task.log': 'Registro:',
    'action.open': 'Apri',
    'action.download': 'Scarica',

    'error.encrypted': 'Il file è protetto da password. Togli la ' +
        'password e riprova.',
    'error.has_text': 'Il file ha già del testo. Per riconoscerlo di ' +
        'nuovo, spunta «Riconosci di nuovo» in «Elaborazione».',
    'error.output_access': 'Non è stato possibile salvare il risultato. ' +
        'Probabilmente il file «{output}» è aperto in un altro ' +
        'programma. Chiudilo e riprova.',
    'error.bad_input': 'Il file è danneggiato, oppure non è un PDF né ' +
        'un’immagine.',
    'error.missing_dependency': 'Il programma è stato compilato male: ' +
        'manca un suo componente.',
    'error.too_big': 'Il file è troppo grande: la memoria del computer ' +
        'non è bastata.',
    'error.other': 'Qualcosa è andato storto.',
    'error.crash': 'Il riconoscimento si è interrotto inaspettatamente.',

    'dialog.close': 'Chiudi',
    'dialog.yes': 'Sì',
    'dialog.no': 'No',
    'dialog.details': 'Dettagli',
    'dialog.openFile': 'Apri il file',
    'dialog.reveal': 'Mostra nella cartella',
    'done.one': 'Fatto! Il nuovo file:\n\n{output}\n\n{where}',
    'done.many': 'Fatto! File riconosciuti: {count}.\n{where}',
    'done.someFailed': 'Non riusciti: {count}. {hint}',
    'done.failedHint': 'Il motivo si vede con il pulsante «Motivo» ' +
        'nell’elenco dei file.',
    'done.allFailed': 'Non è stato possibile riconoscere nessun file.' +
        '\n{hint}',
    'done.error': 'Non è stato possibile riconoscere il file\n«{name}».' +
        '\n\n{error}',
    'where.besideOne': 'Si trova accanto all’originale.',
    'where.besideMany': 'I nuovi file si trovano accanto agli originali.',
    'where.downloadsOne': 'È salvato nella cartella «Download».',
    'where.downloadsMany': 'I nuovi file sono salvati nella cartella ' +
        '«Download».',
    'close.running': 'Il riconoscimento è ancora in corso. Fermarlo e ' +
        'chiudere il programma?',

    'update.title': 'Aggiornamento',
    'update.available': 'È uscita una nuova versione',
    'update.question': 'È uscita una nuova versione: {from} → {to}.' +
        '\n\n{question}',
    'update.install': 'Scaricarla e installarla?',
    'update.openPage': 'Aprire la pagina da cui scaricarla?',
    'update.whenDone': 'Il programma si può aggiornare quando il ' +
        'riconoscimento è finito.',
    'update.downloading': 'Download dell’aggiornamento…',
    'update.downloadingPercent': 'Download dell’aggiornamento… ' +
        '{percent} %',
    'update.failed': 'Non è stato possibile installare l’aggiornamento. ' +
        'Puoi scaricarlo a mano dalla pagina delle release su GitHub.',

    'about.link': 'Informazioni e licenze',
    'about.title': 'Informazioni su {app}',
    'about.license': 'Questo è software libero: puoi ridistribuirlo e ' +
        'modificarlo secondo i termini della ' +
        'GNU Affero General Public License versione 3 o (a tua scelta) ' +
        'di qualsiasi versione successiva.',
    'about.warranty': 'Il programma è distribuito <b>senza alcuna ' +
        'garanzia</b>, neppure la garanzia implicita di ' +
        'commerciabilità o di idoneità a un particolare scopo.',
    'about.source': 'Codice sorgente:',
    'about.inside': 'All’interno: Tesseract, Leptonica, MuPDF, ' +
        'Ghostscript, zlib e altri componenti liberi. Le loro licenze, e ' +
        'dove trovarne il codice sorgente, sono dietro il pulsante ' +
        '«{notices}».',
    'about.licenseFile': 'Licenza del programma',
    'about.noticesFile': 'Componenti di terze parti',
    'about.missing': 'File non trovato: {name}',
};
