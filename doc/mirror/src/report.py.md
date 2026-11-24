# 报告数据与表格排版

**由调用方提供数据**

- `Report` 接收标题、上下文、表格和说明。`Cell` 可给单元格指定 `positive`、`negative`、`mixed` 等呈现角色，方向来自调用方[^source]。
- `Table` 用表头和所有数据的可见宽度决定列宽。各行字段数与表头一致，列号从零开始。`right=(1,)` 让第二列右对齐，`header_right` 可独立选择表头对齐[^source]。
- 比如已算得候选的速度比是 1.25 倍，调用者将该文本和视为正向的角色传给表格[^source]。

```python
from vecorge_console import Cell, Report, Table

rows = [("candidate", Cell("1.25x", "positive"))]
table = Table("Summary", ("method", "speedup"), rows, right=(1,))
report = Report("Comparison", [("samples", 3)], [table])
assert "1.25x" in report.render()
```

**两种输出方式**

- `Report.render()` 返回带末尾换行的纯文本，适合直接存入日志。`Console.report(report)` 将同一版式写向实际输出流，着色所用的角色由 `Config.report` 配置[^source]<sup>,</sup>[^console]<sup>,</sup>[^config]。

## 参考资料

[^source]: [报告字段、表格列宽和文本渲染](../../../src/report.py)
[^console]: [报告怎样写入终端或重定向输出](console.py.md)
[^config]: [报告角色和颜色配置](config.py.md)
