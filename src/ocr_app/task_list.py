"""The list of files to recognize, one line per file with its state."""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from pathlib import Path

from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QListWidget,
    QListWidgetItem,
)

from ocr_app import INPUT_EXTENSIONS, OUTPUT_SUFFIX
from ocr_app.tasks import State, Task

STATE_COLORS = {
    State.DONE: QColor('#43a047'),
    State.FAILED: QColor('#e53935'),
}


def _is_input(path: Path) -> bool:
    return path.suffix.lower() in INPUT_EXTENSIONS


def _expand(paths: Iterable[Path]) -> Iterator[Path]:
    # Inside folders, our own results are skipped, so dropping the same
    # folder again does not recognize them a second time
    for path in paths:
        if path.is_dir():
            for child in sorted(path.rglob('*')):
                if (
                    child.is_file()
                    and _is_input(child)
                    and not child.stem.endswith(OUTPUT_SUFFIX)
                ):
                    yield child
        elif path.is_file():
            yield path


def _state_text(task: Task, percent: int | None) -> str:
    return {
        State.WAITING: 'ждёт',
        State.RUNNING: f'в работе… {percent or 0}%',
        State.DONE: f'✔ готово → {task.output.name}',
        State.FAILED: '✖ не получилось (двойной щелчок — подробности)',
        State.CANCELLED: 'остановлено',
    }[task.state]


class TaskList(QListWidget):
    def __init__(self) -> None:
        super().__init__()
        self.tasks: list[Task] = []
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setMinimumHeight(120)
        self.setStyleSheet('QListWidget { font-size: 12pt; }')

    def add(self, paths: Iterable[Path]) -> tuple[list[Task], list[str]]:
        """Return the new tasks and the names of the rejected files."""
        known = {str(task.source).casefold() for task in self.tasks}
        added: list[Task] = []
        rejected: list[str] = []
        for path in _expand(paths):
            key = str(path).casefold()
            if not _is_input(path):
                rejected.append(path.name)
            elif key not in known:
                known.add(key)
                added.append(self._append(path))
        return added, rejected

    def remove_idle(self, tasks: Iterable[Task]) -> list[Task]:
        """Remove every task that is not running; return the removed ones."""
        removed = [t for t in list(tasks) if t.state != State.RUNNING]
        for task in removed:
            self.tasks.remove(task)
            self.takeItem(self.row(task.item))
        return removed

    def selected_tasks(self) -> list[Task]:
        selected = self.selectedItems()
        return [task for task in self.tasks if task.item in selected]

    def task_for(self, item: QListWidgetItem) -> Task | None:
        return next((t for t in self.tasks if t.item is item), None)

    def pending(self) -> list[Task]:
        return [task for task in self.tasks if task.state != State.DONE]

    def paint(self, task: Task, percent: int | None = None) -> None:
        item = task.item
        item.setText(f'{task.source.name}   —   {_state_text(task, percent)}')

        tooltip = str(task.source)
        if task.error:
            tooltip += f'\n\n{task.error}'
        item.setToolTip(tooltip)

        default_color = self.palette().text().color()
        item.setForeground(STATE_COLORS.get(task.state, default_color))

    def _append(self, path: Path) -> Task:
        task = Task(path, QListWidgetItem())
        self.tasks.append(task)
        self.addItem(task.item)
        self.paint(task)
        return task
