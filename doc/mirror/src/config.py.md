# 配置合并与校验

**读取配置**

- `Config.load()` 返回库内默认值。`Config.load(path)` 读取调用方指定的 TOML，在各段合并已填写的字段。同名 `[style]` 项以整项替换[^source]。
- 调用方将结果传给 `Console(config=...)`。加载时校验配置段、字段类型、数值范围和样式引用，使用未知样式名会报告具体字段[^source]<sup>,</sup>[^console]。

| 配置段 | 读取的内容 |
| --- | --- |
| `[display]` | 颜色模式、备用列宽、详细输出 |
| `[progress]` | 是否启用动画、延迟、刷新间隔、轨道宽度与样式 |
| `[style]` | 前景色、加粗、暗色组成的具名样式 |
| `[status]` | 每种状态标记使用的样式 |
| `[report]` | 报告标题、表头、辅助文字和方向使用的样式 |

**改值示例**

- 将下例保存为 `console.toml`。加载后刷新间隔为 0.2 秒，`success` 变成仅加粗的样式，报告标题及原有引用该样式的状态一起生效。未指定的字段沿用默认值[^source]。

```toml
[progress]
refresh_seconds = 0.2

[style.success]
bold = true

[report]
heading = "success"
```

- 用 `Console(Config.load("console.toml"))` 创建采用这份配置的输出实例。配置可以传给多个 `Console` 实例[^source]<sup>,</sup>[^console]。

## 参考资料

[^source]: [默认值、合并逻辑与合法取值校验](../../../src/config.py)
[^console]: [调用方传入配置的输出实例](console.py.md)
