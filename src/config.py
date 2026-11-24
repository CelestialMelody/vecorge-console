"""将内置默认值和可选的 TOML 覆盖解析为显示参数与样式。

文件说明见 doc/mirror/src/config.py.md。
"""

from collections.abc import Mapping
from dataclasses import dataclass
import math
from pathlib import Path
import re
import tomllib
from types import MappingProxyType


@dataclass(frozen=True)
class _Display:
    color: str = 'auto'
    fallback_columns: int = 100
    verbose: bool = False


@dataclass(frozen=True)
class _ProgressOptions:
    enabled: bool = True
    delay_seconds: float = .5
    refresh_seconds: float = .1
    bar_width: int = 20
    fill_style: str = 'green'
    muted_style: str = 'dim'


_STYLE = {
    'success': {'fg': '#4c9b6b'},
    'warning': {'fg': '#c78b38'},
    'failure': {'fg': '#dd5955'},
    'muted': {'fg': '#8a93a3'},
    'green': {'fg': 'green'},
    'dim': {'dim': True},
    'bold': {'bold': True},
    'plain': {},
}
_STATUS = {'ok': 'success', 'pass': 'success', 'warn': 'warning', 'fail': 'failure',
           'info': 'muted', 'run': 'muted', 'skip': 'muted'}
_REPORT = {'heading': 'bold', 'muted': 'plain', 'column_header': 'plain',
           'positive': 'success', 'negative': 'failure', 'mixed': 'warning'}
_BASIC_COLORS = {name: 30 + i for i, name in enumerate(
    ('black', 'red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white'))}


def _keys(table, allowed, path):
    if not isinstance(table, Mapping):
        raise ValueError(f'{path} must be a table')
    unknown = table.keys() - allowed
    if unknown:
        raise ValueError(f'unknown {path} key: {", ".join(sorted(map(str, unknown)))}')


def _boolean(value, path):
    if type(value) is not bool:
        raise ValueError(f'{path} must be a boolean')


def _integer(value, path):
    if type(value) is not int or value <= 0:
        raise ValueError(f'{path} must be a positive integer')


def _seconds(value, path, *, zero=False):
    try:
        valid = type(value) in (int, float) and math.isfinite(value)
    except OverflowError:
        valid = False
    if not valid or value < 0 or (not zero and value == 0):
        expected = 'nonnegative' if zero else 'positive'
        raise ValueError(f'{path} must be finite and {expected}')


def _style_codes(styles):
    result = {}
    for name, attributes in styles.items():
        path = f'style.{name}'
        if not isinstance(name, str) or not re.fullmatch(r'[a-zA-Z][a-zA-Z0-9_-]*', name):
            raise ValueError(f'invalid style name: {name!r}')
        _keys(attributes, {'fg', 'bold', 'dim'}, path)
        params = []
        for attribute, code in [('bold', '1'), ('dim', '2')]:
            value = attributes.get(attribute, False)
            _boolean(value, f'{path}.{attribute}')
            if value:
                params.append(code)
        if 'fg' in attributes:
            fg = attributes['fg']
            if isinstance(fg, str) and fg in _BASIC_COLORS:
                params.append(str(_BASIC_COLORS[fg]))
            elif isinstance(fg, str) and re.fullmatch(r'#[0-9a-fA-F]{6}', fg):
                params.extend(['38', '2', *(str(int(fg[i:i + 2], 16)) for i in (1, 3, 5))])
            else:
                raise ValueError(f'{path}.fg must be a named color or #RRGGBB')
        result[name] = '\x1b[' + ';'.join(params) + 'm' if params else ''
    return MappingProxyType(result)


def _reference(name, styles, path):
    if not isinstance(name, str) or name not in styles:
        raise ValueError(f'{path} references unknown style: {name!r}')


@dataclass(frozen=True)
class Config:
    """一次解析出的显示参数和已编译样式。"""

    display: _Display
    progress: _ProgressOptions
    style: Mapping[str, str]
    status: Mapping[str, str]
    report: Mapping[str, str]

    @classmethod
    def load(cls, path: str | Path | None = None) -> 'Config':
        """用 TOML 中填写的字段覆盖默认值。同名 style 以整项替换。"""
        values = {'display': vars(_Display()).copy(), 'progress': vars(_ProgressOptions()).copy(),
                  'style': _STYLE.copy(), 'status': _STATUS.copy(), 'report': _REPORT.copy()}
        if path is not None:
            with Path(path).open('rb') as stream:
                document = tomllib.load(stream)
            _keys(document, values.keys(), 'configuration')
            for section, fields in document.items():
                if section == 'style':
                    if not isinstance(fields, Mapping):
                        raise ValueError('style must be a table')
                else:
                    _keys(fields, values[section].keys(), section)
                values[section].update(fields)
        return cls._resolve(values)

    @classmethod
    def _resolve(cls, values):
        display = _Display(**values['display'])
        if display.color not in ('auto', 'always', 'never'):
            raise ValueError('display.color must be auto, always or never')
        _integer(display.fallback_columns, 'display.fallback_columns')
        _boolean(display.verbose, 'display.verbose')
        progress = _ProgressOptions(**values['progress'])
        _boolean(progress.enabled, 'progress.enabled')
        _seconds(progress.delay_seconds, 'progress.delay_seconds', zero=True)
        _seconds(progress.refresh_seconds, 'progress.refresh_seconds')
        _integer(progress.bar_width, 'progress.bar_width')
        styles = _style_codes(values['style'])
        for key in ('fill_style', 'muted_style'):
            _reference(getattr(progress, key), styles, f'progress.{key}')
        for section in ('status', 'report'):
            for key, name in values[section].items():
                _reference(name, styles, f'{section}.{key}')
        return cls(display, progress, styles,
                   MappingProxyType(values['status']), MappingProxyType(values['report']))
