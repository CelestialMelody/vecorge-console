# 打包声明

**发行名与导入名**

- `pyproject.toml` 定义发行名 `vecorge-console`、当前版本与 Python 3.11 及以上的运行条件。构建使用 setuptools。以下源码映射说明安装后为何从 `vecorge_console` 导入[^package]。

```toml
[tool.setuptools.package-dir]
vecorge_console = "src"
```

- 配置解析依赖 Python 标准库的 `tomllib`。使用方在前置虚拟环境中安装包，再从统一入口导入[^loader]<sup>,</sup>[^exports]。

## 安装与检查

- 激活 Python 虚拟环境后，在仓库根目录执行安装。

```bash
python -m pip install .
```

- 安装完成后运行下例。终端应显示以 `[OK]` 开始的状态行。

```bash
python -c 'from vecorge_console import Console; Console().status("ok", "check", "package")'
```

## 参考资料

[^package]: [发行元数据、构建后端和包目录](../../pyproject.toml)
[^loader]: [配置读取实现](../../src/config.py)
[^exports]: [公开类型的导出](src/__init__.py.md)
