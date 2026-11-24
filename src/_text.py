"""提供 ANSI 控制序列过滤、终端列宽计算和样式应用。

文件说明见 doc/mirror/src/_text.py.md。
"""

import os
import unicodedata


_RESET = '\x1b[0m'


class AnsiFilter:
    """清理跨读取块的 ANSI 序列，保留其间的可见文本。"""

    def __init__(self):
        self.state = 'text'

    def feed(self, text):
        output = []
        for char in text:
            if self.state == 'text':
                if char == '\x1b':
                    self.state = 'escape'
                else:
                    output.append(char)
            elif self.state == 'escape':
                self.state = 'csi' if char == '[' else 'osc' if char == ']' else 'text'
            elif self.state == 'csi':
                if '@' <= char <= '~':
                    self.state = 'text'
            elif self.state == 'osc':
                if char == '\x07':
                    self.state = 'text'
                elif char == '\x1b':
                    self.state = 'osc_end'
            elif self.state == 'osc_end':
                self.state = 'text' if char == '\\' else 'osc'
        return ''.join(output)


def plain(value):
    return AnsiFilter().feed(str(value))


def single_line(value):
    return ' '.join(''.join(ch if unicodedata.category(ch) != 'Cc' else ' '
                            for ch in plain(value)).split())


def _cell(char):
    if unicodedata.combining(char):
        return 0
    return 2 if unicodedata.east_asian_width(char) in ('W', 'F') else 1


def width(text):
    return sum(_cell(ch) for ch in text if ch not in '\r\n')


def clip(text, limit):
    if limit <= 0:
        return ''
    used = 0
    for index, char in enumerate(text):
        used += _cell(char)
        if used > limit:
            return text[:index]
    return text


def middle(text, limit):
    if limit <= 0:
        return ''
    if width(text) <= limit:
        return text
    if limit <= 3:
        return '.' * limit
    left = (limit - 1) // 2
    return clip(text, left) + '…' + clip(text[::-1], limit - left - 1)[::-1]


def columns(stream, fallback):
    try:
        count = os.get_terminal_size(stream.fileno()).columns
    except (AttributeError, OSError, ValueError):
        count = 0
    return count if count > 0 else fallback


def is_tty(stream):
    return bool(getattr(stream, 'isatty', lambda: False)())


def paint(text, code):
    return f'{code}{text}{_RESET}' if code else text
