# ANSI 过滤与终端列宽

**分块的控制序列**

- `AnsiFilter.feed()` 接收已解码的字符串。过滤器记住是否刚读到 `ESC`，或是否还在 CSI（控制序列）或 OSC（操作系统命令）内部。每条输入流用自己的实例，才能继续处理横跨读取块的序列[^text]。
- 下面两块把一种设置文字颜色的序列从中间分开。第一块尚无可显示文本，第二块只留下 `ready`[^text]。

```python
from vecorge_console import AnsiFilter

cleaner = AnsiFilter()
assert cleaner.feed("\x1b[3") == ""
assert cleaner.feed("1mready\x1b[0m") == "ready"
```

- `plain()` 用新实例处理完整文本。`single_line()` 将控制字符和连续空白整理为单行，供状态标签和报告表格使用[^text]<sup>,</sup>[^report]。

**可见列宽**

- `width()` 按字符的 Unicode 属性计算显示列，组合字符占零格，Unicode 全宽和宽字符占两格。例如 `中A` 占三格。`clip()` 在列宽上限处截断，`middle()` 在中间插入省略号[^text]。
- `columns()` 先从输出流的文件描述符取终端列数，读取不到时采用配置的备用宽度。`paint()` 负责给排好的文字加样式[^text]<sup>,</sup>[^console]。

## 参考资料

[^text]: [控制序列状态、宽度计算和样式应用](../../../src/_text.py)
[^report]: [报告列如何使用可见宽度](report.py.md)
[^console]: [终端流、折行与配色](console.py.md)
