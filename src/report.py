"""把调用者准备的上下文、表格和说明排成终端与文本共用的报告。

文件说明见 doc/files/util/lib/python/vecorge-console/src/report.py.md。
"""

from dataclasses import dataclass
from textwrap import wrap

from ._text import paint, single_line, width


@dataclass(frozen=True)
class Cell:
    """方向由调用者给出，颜色由报告配置选择。"""

    text: str
    tone: str | None = None

    def __post_init__(self):
        if self.tone not in (None, 'positive', 'negative', 'mixed'):
            raise ValueError(f'unknown report tone: {self.tone!r}')


@dataclass
class Table:
    title: str
    headers: tuple[str, ...]
    rows: list
    right: tuple[int, ...] = ()
    header_right: tuple[int, ...] | None = None

    def _lines(self, styles):
        cells = [[Cell(single_line(value.text), value.tone) if isinstance(value, Cell)
                  else Cell(single_line(value)) for value in row] for row in self.rows]
        header = [Cell(single_line(label)) for label in self.headers]
        sizes = [max(width(cell.text) for cell in column)
                 for column in zip(header, *cells, strict=True)]

        def row_text(row, right, style=''):
            fields = []
            for index, cell in enumerate(row):
                padding = ' ' * (sizes[index] - width(cell.text))
                text = paint(cell.text, styles.get(cell.tone, style)) if cell.text else ''
                fields.append(padding + text if index in right else text + padding)
            return '  ' + ' | '.join(fields).rstrip()

        header_right = self.right if self.header_right is None else self.header_right
        divider = '  ' + '-+-'.join('-' * size for size in sizes)
        return [paint(single_line(self.title), styles.get('heading', '')),
                row_text(header, header_right, styles.get('column_header', '')),
                paint(divider, styles.get('muted', '')),
                *(row_text(row, self.right) for row in cells)]


@dataclass
class Report:
    title: str
    context: list
    tables: list[Table]
    notes: tuple[str, ...] = ()
    subtitle: str = ''
    context_width: int | None = None
    note_width: int = 78

    def render(self) -> str:
        """为 report.txt 返回有末尾换行的纯文本。"""
        return self._render({})

    def _render(self, styles):
        title = ' ' + single_line(self.title)
        subtitle = '   ' + single_line(self.subtitle) if self.subtitle else ''
        heading = styles.get('heading', '')
        muted = styles.get('muted', '')
        rule = paint('=' * max(78, width(title + subtitle)), muted)
        lines = [rule, paint(title, heading) + paint(subtitle, muted), rule, '', paint('Context', heading)]
        context = [(single_line(name), single_line(value)) for name, value in self.context]
        label_width = self.context_width
        if label_width is None:
            label_width = max((width(name) for name, _ in context), default=0)
        for name, value in context:
            padding = ' ' * (max(0, label_width - width(name)) + 2)
            lines.append('  ' + paint(name, muted) + padding + value)
        for table in self.tables:
            lines.extend(['', *table._lines(styles)])
        if self.notes:
            lines.extend(['', paint('Note', heading)])
            for note in self.notes:
                lines.extend(wrap(single_line(note), width=self.note_width, initial_indent='  • ',
                                  subsequent_indent='    ', break_long_words=False,
                                  break_on_hyphens=False))
        return '\n'.join(lines) + '\n'
