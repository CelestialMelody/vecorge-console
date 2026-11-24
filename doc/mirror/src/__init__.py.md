# 包入口

**公开类型**

- 从 `vecorge_console` 导入六个公开类型。`Config` 解析配置，`Console` 向选定的流输出；`Cell`、`Table` 和 `Report` 描述报告数据。`AnsiFilter` 供处理分块文本。公开接口以源文件中的导出清单为准[^entry]。

```python
__all__ = ['AnsiFilter', 'Cell', 'Config', 'Console', 'Report', 'Table']
```

**调用示例**

- 安装完成后，以下代码向默认的标准输出写一条构建状态。`ok` 是库认可的状态，阶段和对象由调用者给出[^console]。

```python
from vecorge_console import Console

Console().status("ok", "build", "example")
```

## 参考资料

[^entry]: [公开类型与导入位置](../../../src/__init__.py)
[^console]: [状态行的输出流与格式](console.py.md)
