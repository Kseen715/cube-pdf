"""Message boxes and the About dialog."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QMessageBox,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
)

from ocr_app import APP_NAME, SOURCE_URL
from ocr_app.bundle import legal_file
from ocr_app.tasks import Task
from ocr_app.widgets import close_buttons, open_file, show_in_explorer

# The AGPL asks every interactive program to show these notices
ABOUT = (
    '<p><b>{name}</b><br>Copyright © 2026 Denis Korenev</p>'
    '<p>Это свободная программа: её можно распространять и изменять на '
    'условиях GNU Affero General Public License версии 3 или (по вашему '
    'выбору) любой более поздней версии.</p>'
    '<p>Программа распространяется <b>без каких-либо гарантий</b>, в том '
    'числе без гарантий товарной пригодности и пригодности для определённой '
    'цели.</p>'
    '<p>Исходный код: <a href="{url}">{url}</a></p>'
    '<p>Внутри: OCRmyPDF, Tesseract, Ghostscript, Qt, Python и другие '
    'свободные компоненты. Их лицензии и где взять их исходный код — по '
    'кнопке «Сторонние компоненты».</p>'
)
LEGAL_FILES = [
    ('Лицензия программы', 'LICENSE'),
    ('Сторонние компоненты', 'THIRD-PARTY-NOTICES.txt'),
]


def _message_box(
    parent: QWidget, icon: QMessageBox.Icon, text: str
) -> QMessageBox:
    box = QMessageBox(parent)
    box.setWindowTitle(APP_NAME)
    box.setIcon(icon)
    box.setText(text)
    return box


def _done_text(done: list[Task], failed: list[Task]) -> str:
    if len(done) == 1:
        text = (
            f'Готово! Новый файл:\n\n{done[0].output.name}\n\n'
            'Он лежит рядом с исходным.'
        )
    else:
        text = (
            f'Готово! Распознано файлов: {len(done)}.\n'
            'Новые файлы лежат рядом с исходными.'
        )
    if failed:
        text += (
            f'\n\nНе получилось: {len(failed)}. Дважды щёлкните по красному '
            'файлу в списке, чтобы узнать причину.'
        )
    return text


def show_done(parent: QWidget, done: list[Task], failed: list[Task]) -> None:
    box = _message_box(
        parent, QMessageBox.Icon.Information, _done_text(done, failed)
    )
    open_button = None
    if len(done) == 1:
        open_button = box.addButton(
            'Открыть файл', QMessageBox.ButtonRole.AcceptRole
        )
    folder_button = box.addButton(
        'Показать в папке', QMessageBox.ButtonRole.ActionRole
    )
    box.addButton('Закрыть', QMessageBox.ButtonRole.RejectRole)

    box.exec()

    clicked = box.clickedButton()
    if open_button is not None and clicked is open_button:
        open_file(done[0].output)
    elif clicked is folder_button:
        show_in_explorer(done[0].output)


def show_error(parent: QWidget, task: Task) -> None:
    text = (
        f'Не получилось распознать файл\n«{task.source.name}».\n\n{task.error}'
    )
    box = _message_box(parent, QMessageBox.Icon.Warning, text)
    if task.details.strip():
        box.setDetailedText(task.details.strip())
    box.exec()


def show_all_failed(parent: QWidget) -> None:
    QMessageBox.warning(
        parent,
        APP_NAME,
        'Ни один файл не получилось распознать.\n'
        'Дважды щёлкните по файлу в списке, чтобы узнать причину.',
    )


def show_about(parent: QWidget) -> None:
    dialog = QDialog(parent)
    dialog.setWindowTitle(f'О программе — {APP_NAME}')
    dialog.setMinimumWidth(560)
    layout = QVBoxLayout(dialog)

    text = QLabel(ABOUT.format(name=APP_NAME, url=SOURCE_URL))
    text.setTextFormat(Qt.TextFormat.RichText)
    text.setWordWrap(True)
    text.setOpenExternalLinks(True)
    layout.addWidget(text)

    buttons = close_buttons(dialog)
    for title, name in LEGAL_FILES:
        button = buttons.addButton(
            title, QDialogButtonBox.ButtonRole.ActionRole
        )
        button.clicked.connect(
            lambda _checked=False, n=name: _show_legal_file(dialog, n)
        )
    layout.addWidget(buttons)

    dialog.exec()


def _show_legal_file(parent: QWidget, name: str) -> None:
    path = legal_file(name)
    try:
        text = path.read_text(encoding='utf-8')
    except OSError:
        text = f'Файл не найден: {path}'

    dialog = QDialog(parent)
    dialog.setWindowTitle(name)
    dialog.resize(760, 640)
    layout = QVBoxLayout(dialog)

    view = QPlainTextEdit(text)
    view.setReadOnly(True)
    view.setFont(QFont('Consolas', 10))
    layout.addWidget(view)
    layout.addWidget(close_buttons(dialog))

    dialog.exec()
