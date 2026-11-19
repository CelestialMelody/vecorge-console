# 版本记录

本页记录 `vecorge-console` 各版本对调用方可见的接口、配置与呈现变化。
当前构建版本见 [包声明](../../pyproject.toml)。

## 0.3.0

- `Console.format_status()` 和 `Console.format_failure()` 提供无色日志内容。
  `status()` 与 `failure()` 可用 `error=True` 输出到 stderr。
- `Console.progress()` 支持指定阶段名。设置零延迟时立即绘制初始帧。

## 0.2.0

- `Report` 支持副标题、上下文标签宽度和 Note 宽度。表头可独立于数据列指定对齐方式。
- 报告配置新增 `report.column_header` 和 `report.muted`，用于表头、副标题、分隔线和上下文标签。

## 0.1.0

- 提供共享的状态、失败详情、文本转发、旋转器、计数进度和报表接口。
- 支持内置默认样式和项目 TOML。报告可面向终端显示，也可生成纯文本。
