# 终端接入演示与验收

- 接入程序时先读[终端技能](../SKILL.md)。本页用库自带的演示数据说明怎样查看输出、试配参数和运行库的验收测试。
- 要在调用项目使用这套说明，将整个 `.agents/skills/vecorge-console/` 复制到目标的同名目录，并从目标的 `AGENTS.md` 引用 `SKILL.md`。从调用项目验收时，选择自己真实使用的命令，按[项目入口验收](../SKILL.md#从项目入口验收)核对结果。

## 体验

- 以下路径和命令以 **vecorge-console 库源码根目录** 为起点。该工作副本提供 `examples/demo.py` 和 `tests/test_demo.py`。激活 Python 3.11 或更新版本的虚拟环境，安装当前源码，再用同一个解释器运行演示和测试。

```bash
python -m pip install .
```

- 运行整组演示。

```bash
python examples/demo.py
```

- 默认演示呈现状态行、等待、半行实时输出、计数、失败详情和合成报告。`Reading inputs` 与随后发来的 ` ready` 保持在同一行，换行后恢复进度。失败样例用 45 行诊断展示省略和提示，整组完成后返回 `0`。
- 可用 `status`、`progress`、`failure` 或 `report` 单独选择一项。单跑 `failure` 使用[演示失败退出码](#演示退出码)。把终端窗口缩窄后再看 `status`，长对象名会按当前宽度折行。
- 要体验中断，运行下例。出现 `Press Ctrl+C to interrupt` 后按 Ctrl+C，进度行清除，输出 `[WARN]`，演示返回[中断退出码](#演示退出码)。

```bash
python examples/demo.py interrupt
```

## 显示约定

### 状态与路径

- `status` 演示从下面的状态行开始，随后显示示例文件的路径。可缩窄窗口查看折行。字段对齐、颜色与日志文本按[状态行与路径](../SKILL.md#状态行与路径)核对。

```text
[OK]   build    example
```

### 进度与旋转器

- 在终端运行单项演示。下面是同一次操作从等待到计数的两个时刻。重定向和半行转发按[进度与实时输出](../SKILL.md#进度与实时输出)核对。

```bash
python examples/demo.py progress
```

```text
⠋ Working  Preparing tasks                                                00:00
⠼ Working  [=====>              ] [1/3]  Checking samples                 00:02
```

- 行首循环使用 `⠋ ⠙ ⠹ ⠸ ⠼ ⠴ ⠦ ⠧ ⠇ ⠏`，每帧只占一格。缩到 40 列后，同样完成一个样本时会看到下面这一帧。库源码中的 `doc/mirror/src/progress.py.md` 说明轨道怎样填充、标签如何缩略。

```text
⠼ Working [1/3]  Checkin…samples  00:02
```

### 失败详情

- `failure` 演示给出 45 行合成诊断及退出值。下例用两行表示命令、输出和提示的相对位置。截断与分流见[失败与报告](../SKILL.md#失败与报告)。

```text
[FAIL] test     example: exit 7
                command: sh -c 'exit 7'
                output (2 lines):
                  input file missing
                  verify the input path
                hint: Check the input file
```

### 报告

- `report` 演示将同一组数据交给终端和重定向输出，纯文本如下。列与样式的选择见[报告约定](../SKILL.md#失败与报告)。

```text
==============================================================================
 Console example
==============================================================================

Context
  samples  3

Summary
  method    | elapsed (ms) | speedup
  ----------+--------------+--------
  baseline  |         10.0 |   1.00x
  candidate |          8.0 |   1.25x

Note
  • Synthetic data
```

## 配置与项目接入

- 演示默认从 `examples/workbench.toml` 读取下列报告样式覆盖，其余字段使用库默认值。用 `--config PATH` 指定自己的 TOML。配置如何合并以及哪些值由项目提供，见[选择输出流与配置](../SKILL.md#选择输出流与配置)。

```toml
[report]
muted = "muted"
column_header = "muted"
```

- 在所用配置的 `[display]` 段设 `verbose = true` 后，`status` 演示在相对路径之外显示完整示例路径。

## 演示退出码

- 演示入口读取独立的 `--exit-codes PATH` 配置。省略选项或某个字段时用代码默认值。显示仍由 `--config PATH` 选择。接入方在自己的命令入口定义进程退出值。

| 场景 | 默认退出值 | 取值来源 |
| --- | ---: | --- |
| 正常演示或整组完成 | `0` | 入口的成功返回值 |
| 单跑 `failure` | `7` | `exit_codes.failure` |
| Ctrl+C | `130` | `exit_codes.interrupted` |
| 参数或配置错误 | `2` | CLI 的用法错误 |

- `examples/exit-codes.toml` 覆盖失败值，中断值沿用默认。可配置值为 `1` 至 `255` 的整数。整组演示中的预设失败显示所选值，整组正常完成仍返回 `0`。

```toml
[exit_codes]
failure = 17
```

- 运行后可看到 `[FAIL]` 行里的 `exit 17`。命令本身也返回 `17`。

```bash
python examples/demo.py failure --exit-codes examples/exit-codes.toml
```

## 自动验收

- 从库源码根目录，在安装了当前库的 Python 环境中运行以下命令。伪终端检查在 POSIX 环境运行。

```bash
python -m unittest discover -s tests -v
```

| 场景 | 通过条件 |
| --- | --- |
| stdout 与 stderr 同时重定向 | 输出保留状态和报告文字，两条流均无进度帧和颜色控制序列 |
| 只重定向 stdout | stdout 保留实时文字和完成状态，stderr 的终端进度显示后清行 |
| 单独演示失败 | 使用默认或覆盖的退出值，stderr 保留首尾各 20 行诊断、标注省略数量并显示提示 |
| 读取配置 | 显式样式改变状态色，详细模式显示完整路径，无效样式或退出值报出字段并返回 `2` |
| 80 列伪终端 | 状态和报告使用示例配置的颜色，`NO_COLOR` 下状态保留原有文本 |
| 40 列伪终端 | 长状态行续行对齐，每行最多占 39 个显示列 |
| 等待与计数 | 等待之后可看到 `[1/3]` 及 `[3/3]`，进度清除后显示结果 |
| 实时输出 | 半行收到剩余文字时仍是完整一行，换行后恢复等待 |
| 纯文本报告 | 标题、`Context`、数字列对齐及 `Note` 符合样例 |
| `TERM=dumb` | 仍有结果行，颜色和重绘关闭 |
| Ctrl+C | 活动进度清除后提示中断，返回默认或覆盖的中断值 |

**项目入口复核**

- 库的测试通过后，再从调用项目执行成功、失败、中断和报告重印，按[项目入口验收](../SKILL.md#从项目入口验收)核对输出流、日志和对外退出值。
