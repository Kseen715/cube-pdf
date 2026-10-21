"""Main window. Deliberately simple: pick files, tick languages, press one button."""

from __future__ import annotations

import ctypes
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QObject, QSettings, Qt, QUrl, Signal
from PySide6.QtGui import QColor, QDesktopServices, QFont, QIcon, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QCheckBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ocr_app import APP_NAME, INPUT_EXTENSIONS, LANGUAGES, OUTPUT_SUFFIX, ipc
from ocr_app.bundle import asset
from ocr_app.winjob import KillOnCloseJob

# OCRmyPDF progress step -> (what we tell the user, start %, end %) of one file
STAGES = {
    'Scanning contents': ('Изучаю файл', 0, 10),
    'OCR': ('Распознаю текст', 10, 80),
    'Image processing': ('Обрабатываю страницы', 10, 80),
    'JBIG2': ('Сжимаю картинки', 80, 88),
    'Recompressing JPEGs': ('Сжимаю картинки', 80, 88),
    'Deflating JPEGs': ('Сжимаю картинки', 80, 88),
    'PNGs': ('Сжимаю картинки', 80, 88),
    'PDF/A conversion': ('Сохраняю документ', 88, 95),
    'Linearizing': ('Сохраняю документ', 88, 95),
    'Checking output': ('Проверяю результат', 95, 100),
}
PAGE_STAGES = {'Scanning contents', 'OCR', 'Image processing'}

ERRORS = {
    'encrypted': 'Файл защищён паролем. Снимите пароль и попробуйте ещё раз.',
    'has_text': (
        'В файле уже есть текст. Чтобы распознать его заново, нажмите '
        '«Дополнительные настройки» и отметьте «Распознать заново».'
    ),
    'output_access': (
        'Не получилось сохранить результат. Наверное, файл «{output}» открыт '
        'в другой программе. Закройте его и попробуйте ещё раз.'
    ),
    'bad_input': 'Файл повреждён, или это не PDF и не картинка.',
    'missing_dependency': 'Программа собрана неправильно: не найден её компонент.',
    'too_big': 'Файл слишком большой: не хватило памяти компьютера.',
    'other': 'Что-то пошло не так.',
    'crash': 'Распознавание неожиданно прервалось.',
}

GREEN = QColor('#43a047')
RED = QColor('#e53935')

STYLE = """
QLabel#title { font-size: 20pt; font-weight: bold; }
QLabel#step { font-size: 14pt; font-weight: bold; margin-top: 8px; }
QLabel#hint { color: palette(placeholder-text); }
QPushButton#drop {
    font-size: 14pt; padding: 22px;
    border: 3px dashed palette(mid); border-radius: 12px;
}
QPushButton#drop:hover { border-color: palette(highlight); }
QPushButton#start {
    font-size: 20pt; font-weight: bold; padding: 14px;
    color: white; background: #2e7d32; border: none; border-radius: 10px;
}
QPushButton#start:hover { background: #388e3c; }
QPushButton#start[running="true"] { background: #c62828; }
QPushButton#start[running="true"]:hover { background: #d32f2f; }
QCheckBox { font-size: 13pt; spacing: 8px; }
QCheckBox::indicator { width: 22px; height: 22px; }
QProgressBar {
    min-height: 28px; font-size: 11pt; text-align: center;
    border: 1px solid palette(mid); border-radius: 6px;
}
QProgressBar::chunk { background: #43a047; border-radius: 5px; }
"""


def output_path(source: Path) -> Path:
    return source.with_name(f'{source.stem}{OUTPUT_SUFFIX}.pdf')


def worker_command(payload: str) -> list[str]:
    if getattr(sys, 'frozen', False):
        return [sys.executable, '--worker', payload]
    return [sys.executable, '-m', 'ocr_app', '--worker', payload]


def show_in_explorer(path: Path) -> None:
    subprocess.Popen(f'explorer /select,"{path}"')


@dataclass
class Task:
    source: Path
    item: QListWidgetItem
    state: str = 'waiting'  # waiting, running, done, failed, cancelled
    started: float = 0.0
    error: str = ''
    details: str = ''

    @property
    def output(self) -> Path:
        return output_path(self.source)


class WorkerRun(QObject):
    """One worker process. Signals arrive in the GUI thread."""

    message = Signal(dict)
    finished = Signal(int)

    def __init__(self, job: dict) -> None:
        super().__init__()
        self._tmp = tempfile.mkdtemp(prefix='ocr_app_')
        env = os.environ.copy()
        # Leftovers of a killed job stay in our folder, which we delete afterwards
        env.update(TMP=self._tmp, TEMP=self._tmp, PYINSTALLER_SUPPRESS_SPLASH_SCREEN='1')
        if not getattr(sys, 'frozen', False):
            env['PYTHONPATH'] = str(Path(__file__).resolve().parent.parent)
        self._proc = subprocess.Popen(
            worker_command(json.dumps(job)),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            env=env,
            creationflags=subprocess.CREATE_NO_WINDOW,
            encoding='utf-8',
            errors='replace',
        )
        self._job: KillOnCloseJob | None = KillOnCloseJob()
        self._job.assign(int(self._proc._handle))  # type: ignore[attr-defined]
        threading.Thread(target=self._pump, daemon=True).start()

    def _pump(self) -> None:
        for line in self._proc.stdout:  # type: ignore[union-attr]
            message = ipc.parse(line)
            if message is None and line.strip():
                message = {'event': 'log', 'level': 'OUTPUT', 'msg': line.rstrip()}
            if message:
                self.message.emit(message)
        code = self._proc.wait()
        job, self._job = self._job, None
        if job:
            job.close()
        shutil.rmtree(self._tmp, ignore_errors=True)
        self.finished.emit(code)

    def cancel(self) -> None:
        if self._job:
            self._job.terminate()


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.settings = QSettings('ocrmypdf-app', 'ocr-app')
        self.tasks: list[Task] = []
        self.run: WorkerRun | None = None
        self.current: Task | None = None
        self.batch: list[Task] = []
        self.batch_started = 0.0
        self.file_percent = 0.0
        self.cancelling = False
        self.log_lines: list[str] = []

        self.setWindowTitle(APP_NAME)
        self.setWindowIcon(QIcon(str(asset('app.ico'))))
        self.setAcceptDrops(True)
        self.resize(720, 820)
        self._build_ui()
        self._load_settings()
        self._refresh()

    # --- layout -----------------------------------------------------------

    def _build_ui(self) -> None:
        root = QWidget()
        layout = QVBoxLayout(root)
        layout.setContentsMargins(24, 18, 24, 18)
        layout.setSpacing(8)
        self.setCentralWidget(root)

        title = QLabel('Сделать PDF, в котором можно искать текст')
        title.setObjectName('title')
        title.setWordWrap(True)
        layout.addWidget(title)
        hint = QLabel(
            'Программа читает текст на сканах и фотографиях документов. '
            'Исходный файл не меняется: рядом с ним появится новый, '
            f'с «{OUTPUT_SUFFIX}» в конце названия.'
        )
        hint.setObjectName('hint')
        hint.setWordWrap(True)
        layout.addWidget(hint)

        layout.addWidget(self._step('1. Выберите файлы'))
        self.drop = QPushButton(
            'Нажмите сюда, чтобы выбрать файлы\nили перетащите их в это окно'
        )
        self.drop.setObjectName('drop')
        self.drop.setCursor(Qt.CursorShape.PointingHandCursor)
        self.drop.clicked.connect(self.pick_files)
        layout.addWidget(self.drop)

        self.list = QListWidget()
        self.list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.list.setMinimumHeight(120)
        self.list.setStyleSheet('QListWidget { font-size: 12pt; }')
        self.list.itemDoubleClicked.connect(self._item_activated)
        layout.addWidget(self.list, 1)
        QShortcut(QKeySequence.StandardKey.Delete, self.list, self.remove_selected)

        row = QHBoxLayout()
        self.list_hint = QLabel('Двойной щелчок по готовому файлу откроет его.')
        self.list_hint.setObjectName('hint')
        row.addWidget(self.list_hint, 1)
        self.clear_btn = QPushButton('Очистить список')
        self.clear_btn.clicked.connect(self.clear_list)
        row.addWidget(self.clear_btn)
        layout.addLayout(row)

        layout.addWidget(self._step('2. На каком языке текст в документе?'))
        langs = QHBoxLayout()
        self.lang_boxes: dict[str, QCheckBox] = {}
        for code, label in LANGUAGES.items():
            box = QCheckBox(label)
            box.toggled.connect(lambda checked, b=box: self._lang_toggled(b, checked))
            self.lang_boxes[code] = box
            langs.addWidget(box)
        langs.addStretch(1)
        layout.addLayout(langs)
        lang_hint = QLabel('Можно отметить несколько. Не уверены — оставьте как есть.')
        lang_hint.setObjectName('hint')
        layout.addWidget(lang_hint)

        self.more_btn = QPushButton()
        self.more_btn.setFlat(True)
        self.more_btn.setStyleSheet('text-align: left; padding: 2px;')
        self.more_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.more_btn.clicked.connect(lambda: self._show_more(not self.more.isVisible()))
        layout.addWidget(self.more_btn)
        self.more = QWidget()
        more_layout = QVBoxLayout(self.more)
        more_layout.setContentsMargins(24, 0, 0, 0)
        self.deskew_box = QCheckBox('Выпрямлять кривые (наклонённые) страницы')
        self.force_box = QCheckBox('Распознать заново, даже если в файле уже есть текст')
        more_layout.addWidget(self.deskew_box)
        more_layout.addWidget(self.force_box)
        layout.addWidget(self.more)

        layout.addWidget(self._step('3. Нажмите кнопку'))
        self.start_btn = QPushButton()
        self.start_btn.setObjectName('start')
        self.start_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.start_btn.clicked.connect(self.start_or_stop)
        layout.addWidget(self.start_btn)

        self.status = QLabel()
        self.status.setWordWrap(True)
        self.status.setStyleSheet('font-size: 12pt;')
        layout.addWidget(self.status)
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        layout.addWidget(self.progress)

    @staticmethod
    def _step(text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName('step')
        return label

    def _show_more(self, visible: bool) -> None:
        self.more.setVisible(visible)
        arrow = '▾' if visible else '▸'
        self.more_btn.setText(f'{arrow} Дополнительные настройки')

    # --- settings ---------------------------------------------------------

    def _load_settings(self) -> None:
        langs = self.settings.value('languages', ['rus', 'eng'], type=list)
        if not any(code in LANGUAGES for code in langs):
            langs = ['rus', 'eng']
        for code, box in self.lang_boxes.items():
            box.setChecked(code in langs)
        self.deskew_box.setChecked(self.settings.value('deskew', False, type=bool))
        self.force_box.setChecked(self.settings.value('force', False, type=bool))
        self._show_more(self.settings.value('show_more', False, type=bool))

    def _save_settings(self) -> None:
        self.settings.setValue('languages', self.languages())
        self.settings.setValue('deskew', self.deskew_box.isChecked())
        self.settings.setValue('force', self.force_box.isChecked())
        self.settings.setValue('show_more', self.more.isVisible())

    def languages(self) -> list[str]:
        return [code for code, box in self.lang_boxes.items() if box.isChecked()]

    def _lang_toggled(self, box: QCheckBox, checked: bool) -> None:
        if not checked and not self.languages():
            box.setChecked(True)  # at least one language must stay selected
            self.status.setText('Нужно оставить хотя бы один язык.')

    # --- file list --------------------------------------------------------

    def pick_files(self) -> bool:
        start_dir = self.settings.value('last_dir', str(Path.home() / 'Documents'))
        patterns = ' '.join(f'*{ext}' for ext in sorted(INPUT_EXTENSIONS))
        files, _ = QFileDialog.getOpenFileNames(
            self, 'Выберите файлы', start_dir,
            f'PDF и картинки ({patterns});;Все файлы (*)',
        )
        if files:
            self.settings.setValue('last_dir', str(Path(files[0]).parent))
            self.add_paths([Path(f) for f in files])
        return bool(files)

    def add_paths(self, paths: list[Path]) -> None:
        known = {str(t.source).casefold() for t in self.tasks}
        rejected = []
        for path in self._expand(paths):
            if path.suffix.lower() not in INPUT_EXTENSIONS:
                rejected.append(path.name)
                continue
            if str(path).casefold() in known:
                continue
            known.add(str(path).casefold())
            task = Task(path, QListWidgetItem())
            self.tasks.append(task)
            self.list.addItem(task.item)
            self._paint(task)
            if self.run:
                self.batch.append(task)  # joins the queue that is running now
        if rejected:
            self.status.setText('Пропущены (это не PDF и не картинки): ' + ', '.join(rejected))
        elif not self.run:
            self.status.setText('')
        self._refresh()

    @staticmethod
    def _expand(paths: list[Path]):
        for path in paths:
            if path.is_dir():
                for child in sorted(path.rglob('*')):
                    if (child.is_file() and child.suffix.lower() in INPUT_EXTENSIONS
                            and not child.stem.endswith(OUTPUT_SUFFIX)):
                        yield child
            elif path.is_file():
                yield path

    def remove_selected(self) -> None:
        for item in self.list.selectedItems():
            task = self._task_for(item)
            if task and task.state != 'running':
                self._remove(task)
        self._refresh()

    def clear_list(self) -> None:
        for task in list(self.tasks):
            if task.state != 'running':
                self._remove(task)
        self.status.setText('')
        self.progress.setValue(0)
        self._refresh()

    def _remove(self, task: Task) -> None:
        self.tasks.remove(task)
        if task in self.batch:
            self.batch.remove(task)
        self.list.takeItem(self.list.row(task.item))

    def _task_for(self, item: QListWidgetItem) -> Task | None:
        return next((t for t in self.tasks if t.item is item), None)

    def _paint(self, task: Task, percent: int | None = None) -> None:
        text = {
            'waiting': 'ждёт',
            'running': f'в работе… {percent or 0}%',
            'done': f'✔ готово → {task.output.name}',
            'failed': '✖ не получилось (двойной щелчок — подробности)',
            'cancelled': 'остановлено',
        }[task.state]
        task.item.setText(f'{task.source.name}   —   {text}')
        task.item.setToolTip(str(task.source) + (f'\n\n{task.error}' if task.error else ''))
        color = {'done': GREEN, 'failed': RED}.get(task.state)
        task.item.setForeground(color if color else self.list.palette().text().color())

    def _item_activated(self, item: QListWidgetItem) -> None:
        task = self._task_for(item)
        if not task:
            return
        if task.state == 'done' and task.output.exists():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(task.output)))
        elif task.state == 'failed':
            self._error_box(task)

    # --- running ----------------------------------------------------------

    def start_or_stop(self) -> None:
        if self.run:
            self.cancelling = True
            self.batch = [self.current] if self.current else []
            self.status.setText('Останавливаю…')
            self.run.cancel()
            return
        pending = [t for t in self.tasks if t.state != 'done']
        if not pending:
            if not self.pick_files():
                return
            pending = [t for t in self.tasks if t.state != 'done']
            if not pending:
                return
        self._save_settings()
        self.batch = pending
        self.batch_started = time.time()
        self.cancelling = False
        for task in pending:
            task.state, task.error, task.details = 'waiting', '', ''
            self._paint(task)
        self._next()

    def _next(self) -> None:
        task = next((t for t in self.batch if t.state == 'waiting'), None)
        if task is None or self.cancelling:
            self._batch_finished()
            return
        self.current = task
        self.file_percent = 0.0
        task.state = 'running'
        task.started = time.time()
        self._paint(task, 0)
        self.list.scrollToItem(task.item)
        job = {
            'input': str(task.source),
            'output': str(task.output),
            'languages': self.languages(),
            'deskew': self.deskew_box.isChecked(),
            'force': self.force_box.isChecked(),
        }
        self.log_lines = []
        try:
            self.run = WorkerRun(job)
        except OSError as exc:
            self._task_failed(task, 'crash', str(exc))
            self._next()
            return
        self.run.message.connect(self._on_message)
        self.run.finished.connect(self._on_finished)
        self._set_status('Запускаю…')
        self._refresh()

    def _on_message(self, message: dict) -> None:
        task = self.current
        if task is None:
            return
        event = message.get('event')
        if event == 'log':
            self.log_lines.append(f"{message.get('level')}: {message.get('msg')}")
        elif event == 'progress':
            desc = message.get('desc') or ''
            label, start, end = STAGES.get(desc, ('Обрабатываю', self.file_percent, self.file_percent))
            done, total = message.get('done') or 0, message.get('total') or 0
            fraction = min(done / total, 1.0) if total else 0.0
            self.file_percent = max(self.file_percent, start + (end - start) * fraction)
            if desc in PAGE_STAGES and total:
                label += f': страница {min(int(done) + 1, int(total))} из {int(total)}'
            self._set_status(label)
            self._paint(task, int(self.file_percent))
        elif event == 'error':
            task.error = ERRORS.get(message.get('kind', 'other'), ERRORS['other'])
            task.error = task.error.format(output=task.output.name)
            task.details = message.get('detail', '') + '\n\n' + message.get('trace', '')

    def _on_finished(self, code: int) -> None:
        task, self.current, self.run = self.current, None, None
        if task is not None:
            if self.cancelling:
                task.state = 'cancelled'
                self._remove_partial_output(task)
            elif code == 0 and task.output.exists():
                task.state = 'done'
            else:
                self._task_failed(task, 'crash' if not task.error else None)
            self._paint(task)
        self._next()

    def _task_failed(self, task: Task, kind: str | None, detail: str = '') -> None:
        task.state = 'failed'
        if kind:
            task.error = ERRORS[kind]
            task.details = detail
        task.details += '\n\nЖурнал:\n' + '\n'.join(self.log_lines[-200:])
        self._paint(task)

    @staticmethod
    def _remove_partial_output(task: Task) -> None:
        try:
            if task.output.stat().st_mtime >= task.started:
                task.output.unlink()
        except OSError:
            pass

    def _set_status(self, text: str) -> None:
        if not self.current:
            return
        index = self.batch.index(self.current) if self.current in self.batch else 0
        count = len(self.batch)
        prefix = f'Файл {index + 1} из {count}: ' if count > 1 else ''
        self.status.setText(f'{prefix}{self.current.source.name}\n{text}…')
        overall = (index + self.file_percent / 100) / max(count, 1)
        self.progress.setValue(int(overall * 100))

    def _batch_finished(self) -> None:
        batch, self.batch = self.batch, []
        self._refresh()
        if self.cancelling:
            self.cancelling = False
            self.status.setText('Остановлено.')
            self.progress.setValue(0)
            return
        done = [t for t in batch if t.state == 'done']
        failed = [t for t in batch if t.state == 'failed']
        self.progress.setValue(100 if done and not failed else 0)
        minutes, seconds = divmod(int(time.time() - self.batch_started), 60)
        took = f'{minutes} мин {seconds} с' if minutes else f'{seconds} с'
        self.status.setText(
            f'Готово за {took}. Получилось: {len(done)}'
            + (f', не получилось: {len(failed)}' if failed else '') + '.'
        )
        QApplication.alert(self)
        if len(batch) == 1 and failed:
            self._error_box(failed[0])
        elif done:
            self._done_box(done, failed)
        elif failed:
            QMessageBox.warning(
                self, APP_NAME,
                'Ни один файл не получилось распознать.\n'
                'Дважды щёлкните по файлу в списке, чтобы узнать причину.',
            )

    def _done_box(self, done: list[Task], failed: list[Task]) -> None:
        box = QMessageBox(self)
        box.setWindowTitle(APP_NAME)
        box.setIcon(QMessageBox.Icon.Information)
        if len(done) == 1:
            text = f'Готово! Новый файл:\n\n{done[0].output.name}\n\nОн лежит рядом с исходным.'
        else:
            text = f'Готово! Распознано файлов: {len(done)}.\nНовые файлы лежат рядом с исходными.'
        if failed:
            text += (
                f'\n\nНе получилось: {len(failed)}. '
                'Дважды щёлкните по красному файлу в списке, чтобы узнать причину.'
            )
        box.setText(text)
        open_btn = box.addButton('Открыть файл', QMessageBox.ButtonRole.AcceptRole) if len(done) == 1 else None
        folder_btn = box.addButton('Показать в папке', QMessageBox.ButtonRole.ActionRole)
        box.addButton('Закрыть', QMessageBox.ButtonRole.RejectRole)
        box.exec()
        if open_btn is not None and box.clickedButton() is open_btn:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(done[0].output)))
        elif box.clickedButton() is folder_btn:
            show_in_explorer(done[0].output)

    def _error_box(self, task: Task) -> None:
        box = QMessageBox(self)
        box.setWindowTitle(APP_NAME)
        box.setIcon(QMessageBox.Icon.Warning)
        box.setText(f'Не получилось распознать файл\n«{task.source.name}».\n\n{task.error}')
        if task.details.strip():
            box.setDetailedText(task.details.strip())
        box.exec()

    def _refresh(self) -> None:
        running = self.run is not None
        self.start_btn.setText('■  ОСТАНОВИТЬ' if running else '▶  НАЧАТЬ РАСПОЗНАВАНИЕ')
        self.start_btn.setProperty('running', running)
        self.start_btn.style().unpolish(self.start_btn)
        self.start_btn.style().polish(self.start_btn)
        for widget in (*self.lang_boxes.values(), self.deskew_box, self.force_box):
            widget.setEnabled(not running)
        self.clear_btn.setEnabled(bool(self.tasks))
        if not running and not self.tasks:
            self.progress.setValue(0)

    # --- window events ----------------------------------------------------

    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event) -> None:
        paths = [Path(u.toLocalFile()) for u in event.mimeData().urls() if u.isLocalFile()]
        self.add_paths(paths)
        event.acceptProposedAction()

    def closeEvent(self, event) -> None:
        if self.run:
            answer = QMessageBox.question(
                self, APP_NAME, 'Распознавание ещё идёт. Остановить его и закрыть программу?',
            )
            if answer != QMessageBox.StandardButton.Yes:
                event.ignore()
                return
            self.cancelling = True
            self.run.cancel()
        self._save_settings()
        event.accept()


def _close_splash() -> None:
    try:
        import pyi_splash  # type: ignore[import-not-found]

        pyi_splash.close()
    except ImportError:
        pass


def main(args: list[str]) -> int:
    # Own taskbar group and icon instead of python.exe's
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('ocrmypdf-app.gui')
    app = QApplication(sys.argv[:1])
    app.setFont(QFont('Segoe UI', 11))
    app.setStyleSheet(STYLE)
    window = MainWindow()
    window.show()
    _close_splash()
    if args:
        window.add_paths([Path(a) for a in args])
    return app.exec()
