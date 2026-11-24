# 逐文件说明

- `src/` 安装后对应 Python 包 `vecorge_console`。从[源码安装并检查导入](pyproject.toml.md#安装与检查)，再查[包入口](src/__init__.py.md)里的公开类型[^packaging]。
- 版本及接口变化见[版本记录](../changelog/README.md)。
- 接入其他项目时使用[终端技能](../../.agents/skills/vecorge-console/SKILL.md)。运行示例与自动检查见[演示及验收指南](../../.agents/skills/vecorge-console/references/integration.md)。
- 在库源码中可直接查看[演示程序](../../examples/demo.py)、[显示配置](../../examples/workbench.toml)、[演示退出码配置](../../examples/exit-codes.toml)和[自动验收用例](../../tests/test_demo.py)。

**输入与呈现**

- [配置合并与校验](src/config.py.md)说明默认值来自哪里，一份 TOML 怎样影响样式。
- [终端输出接口](src/console.py.md)说明状态、失败详情和报告由哪个输出流接收。
- [等待行与计数进度](src/progress.py.md)用已知总量的例子说明首帧、更新和清理。
- [报告数据与表格排版](src/report.py.md)说明调用方怎样传入列和数值，终端怎样排版。
- [ANSI 过滤与终端列宽](src/_text.py.md)说明分块控制序列的读取与宽度计算。
- [Python 缓存忽略规则](.gitignore.md)给出检查字节码缓存是否被忽略的命令。

## 参考资料

[^packaging]: [打包配置中的发行名和源码映射](../../pyproject.toml)
