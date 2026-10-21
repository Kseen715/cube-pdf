"""Look of the window and small helpers shared by the window and dialogs."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import TypeVar

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QAbstractButton,
    QDialog,
    QDialogButtonBox,
    QLabel,
    QPushButton,
)

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

Button = TypeVar('Button', bound=QAbstractButton)


def label(text: str, style_name: str = '', wrap: bool = False) -> QLabel:
    widget = QLabel(text)
    widget.setObjectName(style_name)
    widget.setWordWrap(wrap)
    return widget


def clickable(button: Button) -> Button:
    button.setCursor(Qt.CursorShape.PointingHandCursor)
    return button


def link_button(text: str = '') -> QPushButton:
    button = clickable(QPushButton(text))
    button.setFlat(True)
    return button


def close_buttons(dialog: QDialog) -> QDialogButtonBox:
    buttons = QDialogButtonBox()
    buttons.addButton('Закрыть', QDialogButtonBox.ButtonRole.RejectRole)
    buttons.rejected.connect(dialog.reject)
    return buttons


def open_file(path: Path) -> None:
    QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))


def show_in_explorer(path: Path) -> None:
    subprocess.Popen(f'explorer /select,"{path}"')
