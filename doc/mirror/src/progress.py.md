# 等待行与计数进度

## 旋转器与进度条

- 旋转器占行首一格。下面十个点阵字符从左到右循环，每次重绘显示一个。等待下一项完成时，旋转器继续换帧，计数保持在上一项[^source]。

```text
⠋ ⠙ ⠹ ⠸ ⠼ ⠴ ⠦ ⠧ ⠇ ⠏
```

- **80 列终端。** 下面从等待阶段和四个计数值各取一帧。终端每次在当前行重绘。第一帧还在准备任务，总量确定后出现轨道和计数。`Working` 是活动名，`Checking samples` 是当前操作，右端的 `00:02` 表示已经过两秒[^demo]。

```text
⠋ Working  Preparing tasks                                                00:00
⠸ Working  [                    ] [0/3]  Checking samples                 00:01
⠼ Working  [=====>              ] [1/3]  Checking samples                 00:02
⠇ Working  [============>       ] [2/3]  Checking samples                 00:02
⠙ Working  [====================] [3/3]  Checking samples                 00:02
```

- 方括号内的轨道默认有 20 格。`_render_line()` 用 `done * bar_width // total` 算出已填格数。完成 1 项时填 6 格，前五格用 `=`，第六格用 `>` 标出前沿，其余 14 格留空。三项全部完成后，20 格都显示 `=`[^source]<sup>,</sup>[^defaults]。
- **40 列终端。** 同样是 `[1/3]`，这一帧占 39 列，末列留空。轨道收起，计数保留，标签中间用 `…` 缩略，耗时仍靠右[^source]。

```text
⠼ Working [1/3]  Checkin…samples  00:02
```

- 在已安装本库的 Python 环境中，从仓库根目录运行演示，即可看到这些字符在同一行更新[^demo]。

```bash
python examples/demo.py progress
```

## 总量与完成数

- `Console.progress(label)` 在总量未知时显示等待。取得总量后用 `update(total=...)` 切换为计数，通过 `update(done=...)` 提交累计完成数。总量须为正整数，完成数从零开始，已知总量时允许到该总数[^source]<sup>,</sup>[^console]。
- 下例给出三个样本中第一项完成时的更新。进入时的 `delay_seconds=0` 允许在支持重绘的终端立即绘制首帧[^source]。

```python
import time
from vecorge_console import Console

with Console().progress("Preparing tasks", delay_seconds=0) as progress:
    progress.update(total=3, label="Checking samples")
    progress.update(done=1)
    time.sleep(0.25)
```

## 刷新与收尾

- 每个 `Console` 同时管理一条活动进度。默认延迟 0.5 秒、每 0.1 秒刷新，帧写向支持重绘的标准错误流（stderr）。`activity` 可覆盖旋转器旁的活动名[^defaults]<sup>,</sup>[^console]<sup>,</sup>[^source]。
- `_render_line()` 先按终端宽度减一列排版，再为轨道和标签上色[^source]。
- `pause()` 清除当前帧，退出暂停后从新的静默起点恢复刷新。退出进度上下文会停止刷新线程并擦除活动帧[^source]。

## 参考资料

[^source]: [计数边界、帧布局与进度上下文](../../../src/progress.py)
[^console]: [进度启用、输出流与普通文本协调](../../../src/console.py)
[^defaults]: [进度默认值](../../../src/config.py)
[^demo]: [从等待切换到三个样本的进度演示](../../../examples/demo.py)
