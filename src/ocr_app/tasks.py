"""One input file in the list and what has happened to it so far."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from PySide6.QtWidgets import QListWidgetItem

from ocr_app import OUTPUT_SUFFIX

# Worker error kind -> what we tell the user; see worker.ERROR_KINDS
ERROR_MESSAGES = {
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
    'missing_dependency': (
        'Программа собрана неправильно: не найден её компонент.'
    ),
    'too_big': 'Файл слишком большой: не хватило памяти компьютера.',
    'other': 'Что-то пошло не так.',
    'crash': 'Распознавание неожиданно прервалось.',
}


class State(StrEnum):
    WAITING = 'waiting'
    RUNNING = 'running'
    DONE = 'done'
    FAILED = 'failed'
    CANCELLED = 'cancelled'


def output_path(source: Path) -> Path:
    return source.with_name(f'{source.stem}{OUTPUT_SUFFIX}.pdf')


@dataclass
class Task:
    source: Path
    item: QListWidgetItem
    state: State = State.WAITING
    started: float = 0.0
    error: str = ''
    details: str = ''

    @property
    def output(self) -> Path:
        return output_path(self.source)

    def reset(self) -> None:
        self.state = State.WAITING
        self.error = ''
        self.details = ''

    def set_error(self, kind: str, details: str) -> None:
        message = ERROR_MESSAGES.get(kind, ERROR_MESSAGES['other'])
        self.error = message.format(output=self.output.name)
        self.details = details

    def remove_partial_output(self) -> None:
        # An older file with the same name is a previous result, not ours
        try:
            if self.output.stat().st_mtime >= self.started:
                self.output.unlink()
        except OSError:
            pass
