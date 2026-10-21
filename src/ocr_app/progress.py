"""Turn OCRmyPDF progress messages into a percentage and a label."""

from __future__ import annotations

# OCRmyPDF progress step -> (what we tell the user, start %, end %) of a file
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
UNKNOWN_STAGE_LABEL = 'Обрабатываю'


class FileProgress:
    def __init__(self) -> None:
        self.percent = 0.0

    def update(self, desc: str, done: float, total: float) -> str:
        """Record one progress message; return the label to show."""
        label, start, end = STAGES.get(
            desc, (UNKNOWN_STAGE_LABEL, self.percent, self.percent)
        )
        fraction = min(done / total, 1.0) if total else 0.0

        # Stages share ranges, so a new stage must not move the bar back
        self.percent = max(self.percent, start + (end - start) * fraction)

        if desc in PAGE_STAGES and total:
            page = min(int(done) + 1, int(total))
            label += f': страница {page} из {int(total)}'
        return label
