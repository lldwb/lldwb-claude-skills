# opencode-batch

多模块并行改造任务编排（opencode CLI 版）：为每个待改造模块建独立 git worktree、各起一个子代理在 worktree 内调用 opencode CLI 执行该模块对应的 opencode 命令，全部完成后合并回主分支并提交。

## 使用

用户要求"用 opencode 批量改造多个模块""每个模块一个 worktree 跑 opencode""并行跑多个 opencode 命令"时自动触发。

**输入三要素**：主分支（默认当前分支）、opencode 命令（默认命令，可逐模块覆盖）、待改造模块列表。

**边界**：不经 opencode CLI、由子代理直接完成改造的通用并行编排用 `module-batch`；单模块结构改造用 `refactor`；缺陷修复用 `bug-fix`。

## 能力

- 阶段 0 前置检查（CLI 可用 / `.opencode` 已跟踪 / 测试凭据可解 / 外部依赖连通 / 主分支就绪 / 模块路径存在 / **命令定义完备** / 公共资源在位）→ 阶段 1 并行子代理（后台执行 + 轮询）→ 阶段 2 合并（先对比改动交集，公共文件冲突取并集）→ 阶段 3 提交与收尾（删 worktree 留分支）
- 命令定义三要素检查：测试命令、失败分类与容错条款、阶段门禁——缺项视为缺陷，先补齐再派发
- 中断处置：EOF 退出 / 挂起 / 构建失败三类根因识别 → 精确终止（按 worktree 路径定位 PID）→ `SendMessage` 通知主会话统一决策
- 失败不静默：单单元失败不影响其他单元，重试 ≤ 2 次，仍失败记「需人工介入」；失败集合收尾对比（前后一致或缩小即未破坏行为）
- 提交规则以 `commit-create` 为 SSOT，本技能只补充「按模块类型分类提交」
- 与 `module-batch` 共用「一个模块 = 一个 worktree = 一个子代理 = 一条分支」纪律，差别在执行引擎（opencode CLI vs 子代理直接执行）

## 文件

- `SKILL.md` — 技能指令（唯一入口）
- `references/lessons.md` — 经验教训速查（示例经验，按项目技术栈替换）

## 依赖

- opencode CLI（`opencode run --auto --command <命令>`）
- 项目内 `.opencode/commands/<命令>.md` 命令定义（含测试命令、容错条款、阶段门禁）
- git（worktree 支持）
- 子代理调度能力（`Agent` 工具，`subagent_type: general-purpose`）
