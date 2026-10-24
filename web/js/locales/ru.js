// The interface in Russian; i18n.js explains the keys. The About texts
// (about.*) are the notices the AGPL asks for: keep their meaning in every
// language.

export default {
    'theme.group': 'Тема оформления',
    'theme.light': 'Светлая',
    'theme.dark': 'Тёмная',
    'theme.auto': 'Как в системе',
    'locale.group': 'Язык интерфейса',

    'intro.desktop': 'Программа читает текст на сканах и фотографиях ' +
        'документов. Исходный файл не меняется: рядом с ним появится ' +
        'новый, с «{suffix}» в конце названия.',
    'intro.android': 'Программа читает текст на сканах и фотографиях ' +
        'документов. Исходный файл не меняется: готовый PDF ' +
        'сохраняется в папку «Загрузки».',
    'intro.web': 'CUBE-PDF распознаёт текст на сканах и фотографиях ' +
        'документов (OCR) с помощью Tesseract. Распознавание идёт ' +
        'прямо на вашем устройстве: файлы никуда не отправляются и не ' +
        'покидают его. Готовый PDF, в котором можно искать и копировать ' +
        'текст, скачивается кнопкой «Скачать» рядом с названием файла.',
    'native': 'Приложение для Windows и Linux распознаёт быстрее, чем ' +
        'браузер. Скачать его можно на',
    'native.link': 'странице релизов на GitHub',

    'files.title': 'Файлы',
    'files.clear': 'Очистить список',
    'files.count': {
        one: '{count} файл',
        few: '{count} файла',
        many: '{count} файлов',
        other: '{count} файла',
    },
    'files.done': 'готово {count}',
    'files.failed': 'с ошибкой {count}',
    'files.rejected': 'Пропущены (это не PDF и не картинки): {names}',
    'drop.title': 'Перетащите сюда файлы или папку',
    'drop.titleTouch': 'Выберите файлы',
    'drop.click': 'или нажмите, чтобы выбрать.',
    'drop.types': 'Подходят PDF, JPG, PNG и TIFF.',
    'drop.again': 'Добавить файлы',
    'filter.supported': 'PDF и картинки',
    'filter.all': 'Все файлы',

    'settings': 'Настройки распознавания',
    'languages.title': 'Язык текста',
    'languages.note': 'Можно отметить несколько. Не уверены — оставьте ' +
        'как есть.',
    'languages.keepOne': 'Нужно оставить хотя бы один язык.',
    'language.rus': 'Русский',
    'language.eng': 'Английский',
    'language.deu': 'Немецкий',
    'language.ita': 'Итальянский',
    'processing.title': 'Обработка',
    'processing.deskew': 'Выпрямлять наклонённые страницы',
    'processing.force': 'Распознать заново, даже если в файле уже есть ' +
        'текст',
    'start': 'Начать распознавание',
    'stop': 'Остановить',

    'status.file': 'Файл {index} из {count}: ',
    'status.stopping': 'Останавливаю…',
    'status.stopped': 'Остановлено.',
    'status.summary': 'Готово за {took}. Получилось: {done}.',
    'status.summaryFailed': 'Готово за {took}. Получилось: {done}, не ' +
        'получилось: {failed}.',
    'time.minutes': '{minutes} мин {seconds} с',
    'time.seconds': '{seconds} с',

    'stage.start': 'Запускаю',
    'stage.scan': 'Изучаю файл',
    'stage.ocr': 'Распознаю текст',
    'stage.save': 'Сохраняю документ',
    'stage.other': 'Обрабатываю',
    'stage.page': '{stage}: страница {page} из {total}',

    'task.waiting': 'Ждёт',
    'task.done': 'Готово',
    'task.failed': 'Ошибка',
    'task.cancelled': 'Остановлено',
    'task.reason': 'Причина',
    'task.willBe': 'Получится {output}',
    'task.savedAs': 'Сохранён как {output}',
    'task.pages': ' стр.',
    'task.log': 'Журнал:',
    'action.open': 'Открыть',
    'action.download': 'Скачать',

    'error.encrypted': 'Файл защищён паролем. Снимите пароль и ' +
        'попробуйте ещё раз.',
    'error.has_text': 'В файле уже есть текст. Чтобы распознать его ' +
        'заново, отметьте «Распознать заново» в разделе «Обработка».',
    'error.output_access': 'Не получилось сохранить результат. ' +
        'Наверное, файл «{output}» открыт в другой программе. Закройте ' +
        'его и попробуйте ещё раз.',
    'error.bad_input': 'Файл повреждён, или это не PDF и не картинка.',
    'error.missing_dependency': 'Программа собрана неправильно: не ' +
        'найден её компонент.',
    'error.too_big': 'Файл слишком большой: не хватило памяти компьютера.',
    'error.other': 'Что-то пошло не так.',
    'error.crash': 'Распознавание неожиданно прервалось.',

    'dialog.close': 'Закрыть',
    'dialog.yes': 'Да',
    'dialog.no': 'Нет',
    'dialog.details': 'Подробности',
    'dialog.openFile': 'Открыть файл',
    'dialog.reveal': 'Показать в папке',
    'done.one': 'Готово! Новый файл:\n\n{output}\n\n{where}',
    'done.many': 'Готово! Распознано файлов: {count}.\n{where}',
    'done.someFailed': 'Не получилось: {count}. {hint}',
    'done.failedHint': 'Почему — видно по кнопке «Причина» в списке ' +
        'файлов.',
    'done.allFailed': 'Ни один файл не получилось распознать.\n{hint}',
    'done.error': 'Не получилось распознать файл\n«{name}».\n\n{error}',
    'where.besideOne': 'Он лежит рядом с исходным.',
    'where.besideMany': 'Новые файлы лежат рядом с исходными.',
    'where.downloadsOne': 'Он сохранён в папке «Загрузки».',
    'where.downloadsMany': 'Новые файлы сохранены в папке «Загрузки».',
    'close.running': 'Распознавание ещё идёт. Остановить его и закрыть ' +
        'программу?',

    'update.title': 'Обновление',
    'update.available': 'Вышла новая версия',
    'update.question': 'Вышла новая версия: {from} → {to}.\n\n{question}',
    'update.install': 'Скачать и установить её?',
    'update.openPage': 'Открыть страницу, где её можно скачать?',
    'update.whenDone': 'Обновить программу можно, когда распознавание ' +
        'закончится.',
    'update.downloading': 'Скачиваю обновление…',
    'update.downloadingPercent': 'Скачиваю обновление… {percent} %',
    'update.failed': 'Не получилось установить обновление. Его можно ' +
        'скачать вручную на странице релизов на GitHub.',

    'about.link': 'О программе и лицензиях',
    'about.title': 'О программе — {app}',
    'about.license': 'Это свободная программа: её можно распространять ' +
        'и изменять на условиях GNU Affero General Public License версии ' +
        '3 или (по вашему выбору) любой более поздней версии.',
    'about.warranty': 'Программа распространяется ' +
        '<b>без каких-либо гарантий</b>, в том числе без гарантий ' +
        'товарной пригодности и пригодности для определённой цели.',
    'about.source': 'Исходный код:',
    'about.inside': 'Внутри: Tesseract, Leptonica, MuPDF, Ghostscript, ' +
        'zlib и другие свободные компоненты. Их лицензии и где взять их ' +
        'исходный код — по кнопке «{notices}».',
    'about.licenseFile': 'Лицензия программы',
    'about.noticesFile': 'Сторонние компоненты',
    'about.missing': 'Файл не найден: {name}',
};
