# 终端输出接口

**选择输出流**

- `Console` 持有配置、两条输出流和一条活动进度。`status()`、`failure()` 默认写标准输出（stdout），传 `error=True` 时写标准错误（stderr）。`format_status()`、`format_failure()` 返回无色文本，供调用方写日志[^source]。
- 下面将两条流换成内存流，演示同一个实例怎样路由状态与诊断[^source]。

```python
from io import StringIO
from vecorge_console import Console

out, err = StringIO(), StringIO()
console = Console(out=out, err=err)
console.status("ok", "build", "example")
console.status("fail", "build", "example", error=True)
assert "[OK]" in out.getvalue()
assert "[FAIL]" in err.getvalue()
```

**排版与协调**

- `status()` 根据目标终端可见宽度折行，续行缩进至对象列。重定向时保留完整状态行，颜色由配置及目标流决定。`failure()` 的输出超过 40 行时显示首尾各 20 行，并标出省略行数[^source]<sup>,</sup>[^config]。
- `write()` 过滤流式输入中的 ANSI 控制序列。普通文字先清活动进度行，完整换行后的静默时间达到显示延迟时可以续画。应用如需直接交给子进程一段终端时间，可暂停进度[^source]<sup>,</sup>[^text]<sup>,</sup>[^progress]。
- `report()` 将调用方已填好的报告输出到 stdout。可着色终端应用报告样式，重定向使用纯文本[^source]<sup>,</sup>[^report]。

## 参考资料

[^source]: [输出流选择、状态行、失败详情与报告](../../../src/console.py)
[^config]: [显示配置的默认值与覆盖](config.py.md)
[^text]: [分块文本的 ANSI 过滤](_text.py.md)
[^progress]: [进度行的恢复与清理](progress.py.md)
[^report]: [报告数据与纯文本渲染](report.py.md)
