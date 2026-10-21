"""Main window. Deliberately simple: pick files, tick languages, press start."""

from __future__ import annotations

import ctypes
import sys
import time
from pathlib import Path

from PySide6.QtCore import QSettings
from PySide6.QtGui import QFont, QIcon, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFileDialog,
    QHBoxLayout,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ocr_app import (
    APP_NAME,
    INPUT_EXTENSIONS,
    LANGUAGES,
    OUTPUT_SUFFIX,
    dialogs,
)
from ocr_app.bundle import asset
from ocr_app.progress import FileProgress
from ocr_app.task_list import TaskList
from ocr_app.tasks import State, Task
from ocr_app.widgets import STYLE, clickable, label, link_button, open_file
from ocr_app.worker_process import WorkerProcess

APP_USER_MODEL_ID = 'ocrmypdf-app.gui'
SETTINGS_SCOPE = ('ocrmypdf-app', 'ocr-app')
DEFAULT_LANGUAGES = ['rus', 'eng']
LOG_LINES_IN_DETAILS = 200

START_TEXT = '▶  НАЧАТЬ РАСПОЗНАВАНИЕ'
STOP_TEXT = '■  ОСТАНОВИТЬ'
REJECTED_PREFIX = 'Пропущены (это не PDF и не картинки): '


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.settings = QSettings(*SETTINGS_SCOPE)
        self.run: WorkerProcess | None = None
        self.current: Task | None = None
        self.batch: list[Task] = []
        self.batch_started = 0.0
        self.file_progress = FileProgress()
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

        self._build_header(layout)
        self._build_files_step(layout)
        self._build_languages_step(layout)
        self._build_more_options(layout)
        self._build_start_step(layout)
        self._build_footer(layout)

    def _build_header(self, layout: QVBoxLayout) -> None:
        layout.addWidget(
            label('Сделать PDF, в котором можно искать текст', 'title', True)
        )
        hint = (
            'Программа читает текст на сканах и фотографиях документов. '
            'Исходный файл не меняется: рядом с ним появится новый, '
            f'с «{OUTPUT_SUFFIX}» в конце названия.'
        )
        layout.addWidget(label(hint, 'hint', True))

    def _build_files_step(self, layout: QVBoxLayout) -> None:
        layout.addWidget(label('1. Выберите файлы', 'step'))
        self.drop = clickable(
            QPushButton(
                'Нажмите сюда, чтобы выбрать файлы\n'
                'или перетащите их в это окно'
            )
        )
        self.drop.setObjectName('drop')
        self.drop.clicked.connect(self.pick_files)
        layout.addWidget(self.drop)

        self.task_list = TaskList()
        self.task_list.itemDoubleClicked.connect(self._item_activated)
        layout.addWidget(self.task_list, 1)
        QShortcut(
            QKeySequence.StandardKey.Delete,
            self.task_list,
            self.remove_selected,
        )

        row = QHBoxLayout()
        row.addWidget(
            label('Двойной щелчок по готовому файлу откроет его.', 'hint'), 1
        )
        self.clear_button = QPushButton('Очистить список')
        self.clear_button.clicked.connect(self.clear_list)
        row.addWidget(self.clear_button)
        layout.addLayout(row)

    def _build_languages_step(self, layout: QVBoxLayout) -> None:
        layout.addWidget(label('2. На каком языке текст в документе?', 'step'))
        row = QHBoxLayout()
        self.language_boxes: dict[str, QCheckBox] = {}
        for code, name in LANGUAGES.items():
            box = QCheckBox(name)
            box.toggled.connect(
                lambda checked, b=box: self._language_toggled(b, checked)
            )
            self.language_boxes[code] = box
            row.addWidget(box)
        row.addStretch(1)
        layout.addLayout(row)

        hint = 'Можно отметить несколько. Не уверены — оставьте как есть.'
        layout.addWidget(label(hint, 'hint'))

    def _build_more_options(self, layout: QVBoxLayout) -> None:
        self.more_button = link_button()
        self.more_button.setStyleSheet('text-align: left; padding: 2px;')
        self.more_button.clicked.connect(self._toggle_more)
        layout.addWidget(self.more_button)

        self.more = QWidget()
        more_layout = QVBoxLayout(self.more)
        more_layout.setContentsMargins(24, 0, 0, 0)
        self.deskew_box = QCheckBox('Выпрямлять кривые (наклонённые) страницы')
        self.force_box = QCheckBox(
            'Распознать заново, даже если в файле уже есть текст'
        )
        more_layout.addWidget(self.deskew_box)
        more_layout.addWidget(self.force_box)
        layout.addWidget(self.more)

    def _build_start_step(self, layout: QVBoxLayout) -> None:
        layout.addWidget(label('3. Нажмите кнопку', 'step'))
        self.start_button = clickable(QPushButton())
        self.start_button.setObjectName('start')
        self.start_button.clicked.connect(self.start_or_stop)
        layout.addWidget(self.start_button)

        self.status = label('', wrap=True)
        self.status.setStyleSheet('font-size: 12pt;')
        layout.addWidget(self.status)
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        layout.addWidget(self.progress)

    def _build_footer(self, layout: QVBoxLayout) -> None:
        about_button = link_button('О программе и лицензиях')
        about_button.clicked.connect(self.show_about)
        row = QHBoxLayout()
        row.addStretch(1)
        row.addWidget(about_button)
        layout.addLayout(row)
        QShortcut(QKeySequence.StandardKey.HelpContents, self, self.show_about)

    def _toggle_more(self) -> None:
        self._show_more(not self.more.isVisible())

    def _show_more(self, visible: bool) -> None:
        self.more.setVisible(visible)
        arrow = '▾' if visible else '▸'
        self.more_button.setText(f'{arrow} Дополнительные настройки')

    def show_about(self) -> None:
        dialogs.show_about(self)

    # --- settings ---------------------------------------------------------

    def _load_settings(self) -> None:
        value = self.settings.value
        codes = value('languages', DEFAULT_LANGUAGES, type=list)
        if not any(code in LANGUAGES for code in codes):
            codes = DEFAULT_LANGUAGES
        for code, box in self.language_boxes.items():
            box.setChecked(code in codes)
        self.deskew_box.setChecked(value('deskew', False, type=bool))
        self.force_box.setChecked(value('force', False, type=bool))
        self._show_more(value('show_more', False, type=bool))

    def _save_settings(self) -> None:
        self.settings.setValue('languages', self.languages())
        self.settings.setValue('deskew', self.deskew_box.isChecked())
        self.settings.setValue('force', self.force_box.isChecked())
        self.settings.setValue('show_more', self.more.isVisible())

    def languages(self) -> list[str]:
        boxes = self.language_boxes.items()
        return [code for code, box in boxes if box.isChecked()]

    def _language_toggled(self, box: QCheckBox, checked: bool) -> None:
        if not checked and not self.languages():
            box.setChecked(True)
            self.status.setText('Нужно оставить хотя бы один язык.')

    # --- file list --------------------------------------------------------

    def pick_files(self) -> bool:
        documents = str(Path.home() / 'Documents')
        start_dir = self.settings.value('last_dir', documents)
        patterns = ' '.join(f'*{ext}' for ext in sorted(INPUT_EXTENSIONS))
        files, _ = QFileDialog.getOpenFileNames(
            self,
            'Выберите файлы',
            start_dir,
            f'PDF и картинки ({patterns});;Все файлы (*)',
        )
        if files:
            self.settings.setValue('last_dir', str(Path(files[0]).parent))
            self.add_paths([Path(f) for f in files])
        return bool(files)

    def add_paths(self, paths: list[Path]) -> None:
        added, rejected = self.task_list.add(paths)
        if self.run:
            self.batch += added  # they join the queue that is running now

        if rejected:
            names = ', '.join(rejected)
            self.status.setText(f'{REJECTED_PREFIX}{names}')
        elif not self.run:
            self.status.setText('')
        self._refresh()

    def remove_selected(self) -> None:
        selected = self.task_list.selected_tasks()
        self._forget(self.task_list.remove_idle(selected))
        self._refresh()

    def clear_list(self) -> None:
        self._forget(self.task_list.remove_idle(self.task_list.tasks))
        self.status.setText('')
        self.progress.setValue(0)
        self._refresh()

    def _forget(self, removed: list[Task]) -> None:
        self.batch = [task for task in self.batch if task not in removed]

    def _item_activated(self, item: QListWidgetItem) -> None:
        task = self.task_list.task_for(item)
        if not task:
            return
        if task.state == State.DONE and task.output.exists():
            open_file(task.output)
        elif task.state == State.FAILED:
            dialogs.show_error(self, task)

    # --- running ----------------------------------------------------------

    def start_or_stop(self) -> None:
        if self.run:
            self._stop()
            return

        pending = self.task_list.pending()
        if not pending and self.pick_files():
            pending = self.task_list.pending()
        if pending:
            self._start(pending)

    def _stop(self) -> None:
        self.cancelling = True
        self.batch = [self.current] if self.current else []
        self.status.setText('Останавливаю…')
        self.run.cancel()

    def _start(self, pending: list[Task]) -> None:
        self._save_settings()
        self.batch = pending
        self.batch_started = time.time()
        self.cancelling = False
        for task in pending:
            task.reset()
            self.task_list.paint(task)
        self._next()

    def _next(self) -> None:
        waiting = (t for t in self.batch if t.state == State.WAITING)
        task = next(waiting, None)
        if task is None or self.cancelling:
            self._batch_finished()
            return

        self.current = task
        self.file_progress = FileProgress()
        task.state = State.RUNNING
        task.started = time.time()
        self.task_list.paint(task, 0)
        self.task_list.scrollToItem(task.item)
        self.log_lines = []

        try:
            self.run = WorkerProcess(self._job(task))
        except OSError as exc:
            self._task_failed(task, 'crash', str(exc))
            self._next()
            return
        self.run.message.connect(self._on_message)
        self.run.finished.connect(self._on_finished)
        self._set_status('Запускаю')
        self._refresh()

    def _job(self, task: Task) -> dict:
        return {
            'input': str(task.source),
            'output': str(task.output),
            'languages': self.languages(),
            'deskew': self.deskew_box.isChecked(),
            'force': self.force_box.isChecked(),
        }

    def _on_message(self, message: dict) -> None:
        task = self.current
        if task is None:
            return

        event = message.get('event')
        if event == 'log':
            level, text = message.get('level'), message.get('msg')
            self.log_lines.append(f'{level}: {text}')
        elif event == 'progress':
            self._set_status(
                self.file_progress.update(
                    message.get('desc') or '',
                    message.get('done') or 0,
                    message.get('total') or 0,
                )
            )
            self.task_list.paint(task, int(self.file_progress.percent))
        elif event == 'error':
            detail, trace = message.get('detail', ''), message.get('trace', '')
            task.set_error(message.get('kind', 'other'), f'{detail}\n\n{trace}')

    def _on_finished(self, code: int) -> None:
        task, self.current, self.run = self.current, None, None
        if task is not None:
            if self.cancelling:
                task.state = State.CANCELLED
                task.remove_partial_output()
            elif code == 0 and task.output.exists():
                task.state = State.DONE
            else:
                self._task_failed(task, None if task.error else 'crash')
            self.task_list.paint(task)
        self._next()

    def _task_failed(
        self, task: Task, kind: str | None, details: str = ''
    ) -> None:
        """Mark task failed; kind is None when the worker already said why."""
        task.state = State.FAILED
        if kind:
            task.set_error(kind, details)
        log = '\n'.join(self.log_lines[-LOG_LINES_IN_DETAILS:])
        task.details += f'\n\nЖурнал:\n{log}'
        self.task_list.paint(task)

    def _set_status(self, text: str) -> None:
        task, batch = self.current, self.batch
        if not task:
            return
        count = len(batch)
        index = batch.index(task) if task in batch else 0

        prefix = f'Файл {index + 1} из {count}: ' if count > 1 else ''
        self.status.setText(f'{prefix}{task.source.name}\n{text}…')

        file_fraction = self.file_progress.percent / 100
        overall = (index + file_fraction) / max(count, 1)
        self.progress.setValue(int(overall * 100))

    def _batch_finished(self) -> None:
        batch, self.batch = self.batch, []
        self._refresh()
        if self.cancelling:
            self.cancelling = False
            self.status.setText('Остановлено.')
            self.progress.setValue(0)
            return

        done = [task for task in batch if task.state == State.DONE]
        failed = [task for task in batch if task.state == State.FAILED]
        self.progress.setValue(100 if done and not failed else 0)
        self.status.setText(self._summary(len(done), len(failed)))

        QApplication.alert(self)
        if len(batch) == 1 and failed:
            dialogs.show_error(self, failed[0])
        elif done:
            dialogs.show_done(self, done, failed)
        elif failed:
            dialogs.show_all_failed(self)

    def _summary(self, done: int, failed: int) -> str:
        elapsed = int(time.time() - self.batch_started)
        minutes, seconds = divmod(elapsed, 60)
        took = f'{minutes} мин {seconds} с' if minutes else f'{seconds} с'
        summary = f'Готово за {took}. Получилось: {done}'
        if failed:
            summary += f', не получилось: {failed}'
        return summary + '.'

    def _refresh(self) -> None:
        running = self.run is not None
        button = self.start_button
        button.setText(STOP_TEXT if running else START_TEXT)
        # Qt re-reads [running="true"] in STYLE only after a re-polish
        button.setProperty('running', running)
        button.style().unpolish(button)
        button.style().polish(button)

        options = (
            *self.language_boxes.values(),
            self.deskew_box,
            self.force_box,
        )
        for widget in options:
            widget.setEnabled(not running)
        self.clear_button.setEnabled(bool(self.task_list.tasks))
        if not running and not self.task_list.tasks:
            self.progress.setValue(0)

    # --- window events ----------------------------------------------------

    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event) -> None:
        urls = event.mimeData().urls()
        self.add_paths([Path(u.toLocalFile()) for u in urls if u.isLocalFile()])
        event.acceptProposedAction()

    def closeEvent(self, event) -> None:
        if self.run:
            answer = QMessageBox.question(
                self,
                APP_NAME,
                'Распознавание ещё идёт. Остановить его и закрыть программу?',
            )
            if answer != QMessageBox.StandardButton.Yes:
                event.ignore()
                return
            self.cancelling = True
            self.run.cancel()
        self._save_settings()
        event.accept()


def _close_splash() -> None:
    # pyi_splash exists only inside the built exe
    try:
        import pyi_splash  # type: ignore[import-not-found]
    except ImportError:
        return
    pyi_splash.close()


def main(args: list[str]) -> int:
    # Own taskbar group and icon instead of python.exe's
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
        APP_USER_MODEL_ID
    )
    app = QApplication(sys.argv[:1])
    app.setFont(QFont('Segoe UI', 11))
    app.setStyleSheet(STYLE)

    window = MainWindow()
    window.show()
    _close_splash()
    if args:
        window.add_paths([Path(a) for a in args])
    return app.exec()
