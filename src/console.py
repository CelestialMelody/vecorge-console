"""状态、错误详情、文本与报告的公共输出入口。

文件说明见 doc/files/util/lib/python/vecorge-console/src/console.py.md。
"""

import os
from pathlib import Path
import sys
import threading
import time

from ._text import AnsiFilter, clip, columns, is_tty, paint, plain, width
from .config import Config, _seconds
from .progress import _Progress


def _status_lines(text, limit):
    if limit < 24:
        return [clip(text, max(0, limit))]
    lines = []
    while text:
        indent = '' if not lines else ' ' * 16
        chunk = clip(text, limit - len(indent))
        if len(chunk) == len(text):
            return [*lines, indent + text]
        cut = chunk.rfind(' ')
        if cut <= 0:
            cut = chunk.rfind('/') + 1 or len(chunk)
        lines.append(indent + text[:cut].rstrip())
        text = text[cut:].lstrip()
    return lines


def _one_line(value):
    return plain(value).replace('\n', ' ').replace('\r', ' ')


class Console:
    """一组输出流及其唯一活动进度行。调用方负责业务状态。"""

    def __init__(self, config=None, *, out=None, err=None, root=None):
        self.config = config if config is not None else Config.load()
        self._out = sys.stdout if out is None else out
        self._err = sys.stderr if err is None else err
        self._root = None if root is None else Path(root).resolve()
        self._lock = threading.RLock()
        self._progress = None
        self._partial = False
        self._text = AnsiFilter()

    def _color(self, stream):
        mode = self.config.display.color
        return mode == 'always' or (
            mode == 'auto' and is_tty(stream) and 'NO_COLOR' not in os.environ
            and os.environ.get('TERM', '').lower() != 'dumb')

    def color_enabled(self, *, error=False):
        """报告所选输出流的有效配色状态。"""
        return self._color(self._err if error else self._out)

    def progress_enabled(self):
        """报告当前 stderr 是否支持进度重绘。"""
        return (self.config.progress.enabled and is_tty(self._err)
                and os.environ.get('TERM', '').lower() != 'dumb')

    def path(self, value):
        path = Path(value).resolve()
        if self._root is not None and path.is_relative_to(self._root):
            return str(path.relative_to(self._root))
        return str(Path('…', *path.parts[-3:]))

    def progress(self, label, total=None, *, activity='Working', delay_seconds=None):
        """新建等待或计数上下文。"""
        if delay_seconds is None:
            delay_seconds = self.config.progress.delay_seconds
        else:
            _seconds(delay_seconds, 'progress delay', zero=True)
        return _Progress(self, label, total, activity, delay_seconds)

    def _write(self, text, *, finish_line=False, error=False):
        if not text:
            return
        with self._lock:
            progress = self._progress
            if progress is not None:
                progress._clear()
            if finish_line:
                if self._partial:
                    self._out.write('\n')
                    if error:
                        self._out.flush()
                self._text = AnsiFilter()
            target = self._err if error else self._out
            target.write(text)
            target.flush()
            self._partial = not text.endswith('\n')
            if progress is not None:
                progress._quiet_since = time.monotonic()

    def write(self, text):
        """转发可见文本，直到换行前保持当前行。"""
        with self._lock:
            self._write(self._text.feed(str(text)))

    def detail(self, text):
        if self.config.display.verbose:
            self.write(text)

    def format_status(self, kind, phase, label, detail=None, elapsed=None):
        """返回用于日志的完整无色状态行。"""
        key = kind.lower()
        if key not in self.config.status:
            raise ValueError(f'unknown status: {kind}')
        marker = f'[{key.upper()}]'
        phase = _one_line(phase)
        padding = ' ' * max(0, 8 - width(phase))
        text = f'{marker:<6} {phase}{padding} {_one_line(label)}'
        if detail:
            text += ': ' + _one_line(detail)
        if elapsed is not None and elapsed >= 1:
            seconds = int(elapsed)
            text += f' ({seconds // 60:02d}:{seconds % 60:02d})'
        return text.rstrip()

    def status(self, kind, phase, label, detail=None, elapsed=None, *, error=False):
        text = self.format_status(kind, phase, label, detail, elapsed)
        marker = f'[{kind.upper()}]'
        target = self._err if error else self._out
        lines = (_status_lines(text, columns(target, self.config.display.fallback_columns) - 1)
                 if is_tty(target) else [text])
        if self.color_enabled(error=error) and lines and lines[0].startswith(marker):
            code = self.config.style[self.config.status[kind.lower()]]
            lines[0] = paint(marker, code) + lines[0][len(marker):]
        self._write('\n'.join(lines) + '\n', finish_line=True, error=error)

    def format_failure(self, command=None, output=None, hint=None):
        """返回用于日志的无色失败详情。"""
        lines = plain(output or '').rstrip().splitlines()
        shown = lines if len(lines) <= 40 else lines[:20] + [
            f'... {len(lines) - 40} lines omitted ...', *lines[-20:]]
        detail = []
        if command:
            detail.append(' ' * 16 + 'command: ' + _one_line(command))
        if lines:
            detail.append(' ' * 16 + f'output ({len(lines)} lines):')
            detail.extend(' ' * 18 + line for line in shown)
        if hint:
            detail.append(' ' * 16 + 'hint: ' + _one_line(hint))
        return detail

    def failure(self, command=None, output=None, hint=None, *, error=False):
        detail = self.format_failure(command, output, hint)
        if detail:
            self._write('\n'.join(detail) + '\n', finish_line=True, error=error)

    def report(self, report):
        """将同版式报告写到实际输出流。重定向报告用纯文本。"""
        styles = {role: self.config.style[name] for role, name in self.config.report.items()
                  } if is_tty(self._out) and self._color(self._out) else {}
        self._write(report._render(styles), finish_line=True)
