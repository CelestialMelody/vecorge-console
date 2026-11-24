"""实现 Console.progress() 的单行等待、计数进度和刷新。

文件说明见 doc/mirror/src/progress.py.md。
"""

from contextlib import contextmanager
import threading
import time

from ._text import columns, middle, paint, single_line, width


_SPINNER = '⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏'
_ERASE = '\r\x1b[2K'


def _render_line(label, done, total, elapsed_seconds, terminal_width, pulse,
                 bar_width, fill_code, muted_code, activity='Working'):
    """按物理列数排版后加入颜色。末列留空，时间贴右。"""
    available = max(0, terminal_width - 1)
    seconds = max(0, int(elapsed_seconds))
    elapsed = f'{seconds // 60:02d}:{seconds % 60:02d}'
    if not available:
        return ''
    if available <= len(elapsed) + 2:
        return elapsed.rjust(available)[-available:]

    budget = available - len(elapsed) - 2
    head = f'{_SPINNER[pulse % len(_SPINNER)]} {single_line(activity)}'
    label = single_line(label)
    count = ''
    track = ''
    if total is not None:
        count = f'[{done}/{total}]'
        # 窄终端先收去轨道，保留计数、标签和时间。
        # 两个方括号和轨道、计数、标签前的空白共七格。
        track_room = budget - width(head) - len(count) - 7
        if track_room - bar_width >= 8:
            filled = done * bar_width // total
            marks = '=' * filled
            if 0 < filled < bar_width:
                marks = marks[:-1] + '>'
            space = ' ' * (bar_width - filled)
            track = f'[{marks}{space}]'

    tail = f'  {track} {count}' if track else (f' {count}' if count else '')
    if width(head + tail) > budget:
        if count and len(count) <= budget:
            head = middle(head, budget - len(count) - 1)
            tail = (' ' if head else '') + count
        else:
            head, tail = middle(head, budget), ''
    prefix_width = width(head + tail)
    label = middle(label, budget - prefix_width - 2)
    label_width = 2 + width(label) if label else 0
    padding = ' ' * (budget - prefix_width - label_width + 2)
    if track:
        tail = f'  [{paint(marks, fill_code)}{paint(space, muted_code)}] {count}'
    return head + tail + ('  ' + paint(label, muted_code) if label else '') + padding + elapsed


def _validate(done, total):
    if total is not None and (type(total) is not int or total <= 0):
        raise ValueError('progress total must be a positive integer')
    if type(done) is not int or done < 0 or (total is not None and done > total):
        raise ValueError('progress done is outside its valid range')


class _Progress:
    def __init__(self, console, label, total, activity, delay_seconds):
        _validate(0, total)
        self._console = console
        self._activity = activity
        self._delay_seconds = delay_seconds
        self._label, self._total, self._done = label, total, 0
        self._stop = threading.Event()
        self._thread = None
        self._started = 0.0
        self._quiet_since = 0.0
        self._pauses = 0
        self._drawn = False
        self._pulse = 0

    def __enter__(self):
        console = self._console
        try:
            with console._lock:
                if console._progress is not None:
                    raise RuntimeError('a progress line is already active')
                self._started = self._quiet_since = time.monotonic()
                console._progress = self
            if console.progress_enabled():
                if self._delay_seconds == 0:
                    with console._lock:
                        if not console._partial:
                            self._draw(time.monotonic())
                self._thread = threading.Thread(target=self._refresh, daemon=True)
                self._thread.start()
        except BaseException:
            if console._progress is self:
                self.__exit__(None, None, None)
            raise
        return self

    def update(self, *, label=None, done=None, total=None):
        """更新当前值。取得总数后可把等待切换成进度条。"""
        with self._console._lock:
            next_done = self._done if done is None else done
            next_total = self._total if total is None else total
            _validate(next_done, next_total)
            self._done, self._total = next_done, next_total
            if label is not None:
                self._label = label

    @contextmanager
    def pause(self):
        """暂时把终端交给直接输出的子命令。"""
        with self._console._lock:
            self._pauses += 1
            self._clear()
        try:
            yield
        finally:
            with self._console._lock:
                self._pauses -= 1
                self._quiet_since = time.monotonic()

    def _clear(self):
        if self._drawn:
            self._console._err.write(_ERASE)
            self._console._err.flush()
            self._drawn = False

    def _draw(self, now):
        console = self._console
        options = console.config.progress
        color = console.color_enabled(error=True)
        fill = console.config.style[options.fill_style] if color else ''
        muted = console.config.style[options.muted_style] if color else ''
        frame = _render_line(
            self._label, self._done, self._total, now - self._started,
            columns(console._err, console.config.display.fallback_columns),
            self._pulse, options.bar_width, fill, muted, self._activity)
        console._err.write(_ERASE + frame)
        console._err.flush()
        self._drawn = True
        self._pulse += 1

    def _refresh(self):
        console = self._console
        options = console.config.progress
        if self._drawn and self._stop.wait(options.refresh_seconds):
            return
        while not self._stop.is_set():
            wait = options.refresh_seconds
            with console._lock:
                now = time.monotonic()
                delay = self._delay_seconds - (now - self._quiet_since)
                if not self._pauses and not console._partial:
                    if delay > 0:
                        wait = min(wait, delay)
                    else:
                        self._draw(now)
            self._stop.wait(wait)

    def __exit__(self, *_):
        self._stop.set()
        try:
            if self._thread is not None and self._thread.ident is not None:
                self._thread.join()
        finally:
            with self._console._lock:
                self._console._progress = None
                self._clear()
