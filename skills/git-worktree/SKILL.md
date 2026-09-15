---
name: git-worktree
description: 管理 Git worktree：在项目平级的统一目录下创建（自带智能默认分支名与基础分支）、列出状态、删除与清理无效引用，并支持在 worktree 之间迁移未提交改动或 stash、自动复制被 gitignore 的环境文件、按项目实际 IDE 命令打开。当用户要求"开一个 worktree""在独立目录里做这个需求""并行开发两个分支互不干扰""把当前未提交的改动挪到另一个 worktree""清理失效的 worktree 记录"时使用。边界：多模块并行改造的编排（worktree + 子代理 + 合并）用 module-batch；经 opencode CLI 中转的并行编排用 opencode-batch；分支清理用 git-clean-branches。
---

# 管理 Git worktree

## 角色

你是 worktree 管理员：按统一目录约定创建 / 列出 / 删除 worktree，并处理「环境文件补齐」与「未提交内容迁移」两类收尾工作。执行前先确认当前仓库状态与目标路径，破坏性动作（删除目录）先确认。

## 适用与边界

**适用**：

- 在独立目录里开发一个分支，与当前工作目录互不干扰（同时改多个分支 / 一个需求跑一条分支）；
- 需要把当前未提交的改动或 stash 迁移到某个 worktree；
- 清理失效的 worktree 记录、列出各 worktree 的分支与状态。

**不适用（改用其他技能）**：

- 多模块并行改造的**编排**（建 worktree + 派发子代理 + 审查 + 合并）→ `module-batch`；经 opencode CLI 中转的 → `opencode-batch`；
- 清理已合并 / 过期分支 → `git-clean-branches`；回滚分支到历史版本 → `git-rollback`。

## 要求

1. **统一目录**：worktree 一律建在 `<worktree 根目录>`（默认 `<主仓库同级目录>/.zcf/<项目名>/`，项目已有约定的按项目约定替换，如 `<项目根>/.worktrees/`），**不要**散落在仓库内部。
2. **始终用绝对路径**：先在主仓库算出绝对路径再创建——在已有 worktree 内创建新 worktree 时，相对路径会产生 `../.zcf/<项目名>/.zcf/<项目名>/<名>` 之类的嵌套。
3. **先查冲突**：目标目录已存在、或目标分支已被其他 worktree 检出时，先报告并询问，不覆盖、不抢占。
4. **删除要确认**：`remove` 会删除整个目录（含其中未提交的改动），执行前先确认目标目录干净（`git status --porcelain` 为空），有残留先停下问用户。
5. **不越界**：不删分支（`remove` 只删工作目录，分支保留）、不改写历史、不自动 push；需要这些动作时转对应技能。

## 命令

| 命令 | 作用 |
|---|---|
| `add <名> [-b <分支>] [-o] [--track] [--detach] [--lock]` | 在 `<worktree 根目录>/<名>` 创建 worktree |
| `list` | 列出所有 worktree 及其分支与状态 |
| `remove <名\|路径>` | 删除指定 worktree（目录与 git 引用一并清理） |
| `prune` | 清理孤立的 worktree 记录（目录已被手工删除的情况） |
| `migrate <目标> --from <源>` | 把未提交改动从源迁移到目标 worktree |
| `migrate <目标> --stash` | 把当前 stash 应用到目标 worktree |

## 执行步骤

### 0. 环境检查与路径计算

```bash
git rev-parse --is-inside-work-tree   # 确认在 Git 仓库内
```

主仓库路径推导（在已有 worktree 内执行时也能算回主仓库）：

```bash
git_common_dir=$(git rev-parse --git-common-dir)
toplevel=$(git rev-parse --show-toplevel)
if [ "$git_common_dir" != "$toplevel/.git" ]; then
  MAIN_REPO=$(dirname "$git_common_dir")   # 在 worktree 内 → 从 git-common-dir 推导
else
  MAIN_REPO="$toplevel"                     # 在主仓库内
fi
PROJECT=$(basename "$MAIN_REPO")
WORKTREE_BASE="$MAIN_REPO/../.zcf/$PROJECT"   # ← <worktree 根目录>，按项目约定可替换
```

后续一律使用绝对路径 `"$WORKTREE_BASE/<名>"`。

### 1. `add`：创建

1. 解析智能默认：未给 `-b` 时用 `<名>` 作新分支名；基础分支取 `main` → `master` 中存在的第一个（可用项目约定覆盖）；未给 `<名>` 时用分支名作目录名。
2. 查冲突：目录已存在 → 停下询问；分支已被检出 → 提示以 `--detach` 或换分支名。
3. 创建：

   ```bash
   git worktree add -b <分支> "<WORKTREE_BASE>/<名>" <基础分支>
   ```

4. **补齐环境文件**：扫描主仓库 `.gitignore`，若其中列出了 `.env` / `.env.*` 且主仓库存在对应文件，复制到新 worktree（跳过 `.env.example` 等模板文件，保持原权限与时间戳），并报出复制清单。
5. **IDE 打开**（可选）：用户带 `-o` 或确认后，用项目实际的 IDE 命令打开该目录（如 `code <路径>` / `cursor <路径>` / `idea <路径>`）；命令不在 PATH 时跳过并提示路径，**不报错中断**。
6. 报出：worktree 路径、分支名、基础分支、复制的环境文件。

### 2. `list` / `prune`

```bash
git worktree list          # 路径 + HEAD + 分支
git worktree prune         # 清理目录已被手工删除的无效记录
```

`list` 输出时逐条标出：分支、当前 HEAD、目录是否存在（不存在则建议 `prune`）。

### 3. `remove`：删除

1. `git -C "<路径>" status --porcelain` 确认干净；有未提交改动 → 停下询问（先提交 / migrate / 用户确认丢弃）。
2. 删除：`git worktree remove "<路径>"`（有残留时 git 会拒绝，不要用 `--force` 绕过，除非用户明确确认丢弃）。
3. 复核：`git worktree list` 确认记录已消失；**分支保留**，如需删分支转 `git-clean-branches`。

### 4. `migrate`：内容迁移

1. 校验源：`git -C "<源>" status --porcelain` 非空，否则无需迁移。
2. 校验目标：`git -C "<目标>" status --porcelain` 为空，避免覆盖目标已有改动。
3. 展示将迁移的文件清单，确认后执行：优先 `git -C "<源>" stash push -u` → `git -C "<目标>" stash pop`；跨机 / 跨目录不便 stash 时用 `git diff` + `git apply`（保留补丁文件备查）。
4. 复核：源工作区已干净、目标出现对应改动；冲突时停下交用户处理，不自行取舍。

## 验证

- 创建后 `git worktree list` 同时可见主仓库与新 worktree，且新 worktree 的分支与基础分支正确。
- 新 worktree 内 `git status` 干净、`git log -1` 的提交与基础分支一致。
- 声明的环境文件确实已复制（逐个 `ls` 核对），未把模板文件（`.env.example`）复制过去。
- `remove` 后目录消失、`git worktree list` 无残留记录、被删除 worktree 的分支仍在（`git branch --list <分支>`）。
- `migrate` 后源工作区干净、目标改动与预期一致。

**判定口径**：上述与本次操作相关的项逐项通过方可声明完成；不通过时停下报告，**不静默放行**。

## 任务目标

按统一目录约定完成 worktree 的创建 / 列出 / 删除 / 迁移：路径不嵌套、环境文件已补齐、删除前目录干净且分支保留、迁移不覆盖目标已有改动。

## 注意事项

- **任务跟踪按环境能力可选**：环境提供 `TodoWrite` / `Task*` 工具时用原生任务清单跟踪（完成一项勾一项、收尾核对无未勾选项），否则退回对话内文本清单或落盘勾选（`.tasks/` 下 `- [x]`、未完成项写明处置）——不硬性依赖任一形态。

- **路径嵌套防护**：在 worktree 内再建 worktree 时，相对路径会拼出双层 `.zcf`；始终用绝对路径。
- **删除前先看目录**：`remove` 删除的是整个工作目录——先 `git status`，未提交内容要么迁移要么确认丢弃，不要直接 `--force`。
- **`list` 的常见异常**：目录被手工 `rm -rf` 后 `list` 仍显示记录（prune 可清理）；目录存在但分支被删（`git worktree repair` 或重建）。
- **性能与磁盘**：worktree 共享主仓库的 `.git`，不额外复制历史；但构建产物与依赖目录（如 `node_modules/`、`target/`）**不共享**，首次使用需各自安装。
- **跨平台**：路径含空格时全程加引号；Windows 下不要用 `~` 展开。
- **确认请求无应答时**：`list` / `add` 等可逆动作按原计划继续；`remove`（删目录）属不可逆动作，停下等待确认并在汇报中标明"该决策未获用户确认"。

## 输入

要执行的操作与对象（可选）：操作类型（add / list / remove / prune / migrate）、worktree 名或路径、分支名、基础分支、迁移源：
