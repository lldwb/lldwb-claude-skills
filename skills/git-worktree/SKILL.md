---
name: git-worktree
description: 管理 Git worktree：在项目平级的统一目录下创建（自带智能默认分支名与基础分支）、列出状态、删除与清理无效引用，并支持在 worktree 之间迁移未提交改动或 stash、自动复制被 gitignore 的环境文件、按项目实际 IDE 命令打开、把 worktree 分支合回当前分支。当用户要求"开一个 worktree""在独立目录里做这个需求""并行开发两个分支互不干扰""把当前未提交的改动挪到另一个 worktree""清理失效的 worktree 记录""把 worktree 的改动合回当前分支"时使用。边界：多模块并行改造的编排（worktree + 子代理 + 合并）用 module-batch；经 opencode CLI 中转的并行编排用 opencode-batch；分支清理用 git-clean-branches。
---

# 管理 Git worktree

## 角色

你是 worktree 管理员：按统一目录约定创建 / 列出 / 删除 worktree，并处理「环境文件补齐」与「未提交内容迁移」两类收尾工作。执行前先确认当前仓库状态与目标路径，破坏性动作（删除目录）先确认。

## 适用与边界

**适用**：

- 在独立目录里开发一个分支，与当前工作目录互不干扰（同时改多个分支 / 一个需求跑一条分支）；
- 需要把当前未提交的改动或 stash 迁移到某个 worktree；
- 清理失效的 worktree 记录、列出各 worktree 的分支与状态；
- **收尾**：用户要求把 worktree 分支的改动合回当前分支、删除 worktree 与分支。

**不适用（改用其他技能）**：

- 多模块并行改造的**编排**（建 worktree + 派发子代理 + 审查 + 合并）→ `module-batch`；经 opencode CLI 中转的 → `opencode-batch`；
- 清理已合并 / 过期分支 → `git-clean-branches`；回滚分支到历史版本 → `git-rollback`。

## 要求

1. **统一目录**：worktree 一律建在 `<worktree 根目录>`（默认 `<主仓库同级目录>/.zcf/<项目名>/`，项目已有约定的按项目约定替换，如 `<项目根>/.worktrees/`），**不要**散落在仓库内部。
2. **始终用绝对路径**：先在主仓库算出绝对路径再创建——在已有 worktree 内创建新 worktree 时，相对路径会产生 `../.zcf/<项目名>/.zcf/<项目名>/<名>` 之类的嵌套。
3. **先查冲突**：目标目录已存在、或目标分支已被其他 worktree 检出时，先报告并询问，不覆盖、不抢占。
4. **删除要确认**：`remove` 会删除整个目录（含其中未提交的改动），执行前先确认目标目录干净（`git status --porcelain` 为空），有残留先停下问用户。
5. **不越界**：不删分支（`remove` 只删工作目录，分支保留）、不改写历史、不自动 push；需要这些动作时转对应技能。
6. **合回先判历史形态**：把 worktree 分支合回当前分支前，先 `git log --oneline --merges` 看仓库历史——纯线性（无合并提交）用 rebase + `--ff-only` 快进，不造合并提交；已有合并提交历史时按仓库规范或用户偏好选 merge 方式。

## 命令

| 命令 | 作用 |
|---|---|
| `add <名> [-b <分支>] [-o] [--track] [--detach] [--lock]` | 在 `<worktree 根目录>/<名>` 创建 worktree |
| `list` | 列出所有 worktree 及其分支与状态 |
| `remove <名\|路径>` | 删除指定 worktree（目录与 git 引用一并清理） |
| `prune` | 清理孤立的 worktree 记录（目录已被手工删除的情况） |
| `migrate <目标> --from <源>` | 把未提交改动从源迁移到目标 worktree |
| `migrate <目标> --stash` | 把当前 stash 应用到目标 worktree |
| `merge` | 把 worktree 分支合回当前分支（用户要求时；判历史形态选合并方式） |

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

### 5. `merge`：合回当前分支（用户要求时）

1. 确认两侧干净：主仓库当前分支 `git status --porcelain` 为空、worktree 已提交干净——未提交内容先提交或 migrate。
2. **判历史形态**：`git log --oneline --merges` 为空 = 纯线性历史；非空 = 已有合并提交。
3. 纯线性历史：先变基再快进，不造合并提交（当前分支期间可能已前进，先拉平）：

   ```bash
   git -C "<worktree 路径>" rebase <当前分支名>
   git merge --ff-only <worktree 分支名>     # 在主仓库当前分支上执行
   ```

4. 已有合并提交历史：按仓库规范或用户偏好选 merge 方式（普通 `git merge` / `--no-ff`），拿不准先问。
5. 验证：`git log --oneline -N` 看合入结果；两棵树相关文件 `git hash-object` 逐一比对一致；重跑该项目验证命令（测试等）。
6. 收尾（用户同时要求删除时）：先 `git worktree remove "<路径>"`，再 `git branch -d <分支>`（`-d` 安全删除，分支未完全合入会拒绝；确认无独有提交才删）。

## 验证

- 创建后 `git worktree list` 同时可见主仓库与新 worktree，且新 worktree 的分支与基础分支正确。
- 新 worktree 内 `git status` 干净、`git log -1` 的提交与基础分支一致。
- 声明的环境文件确实已复制（逐个 `ls` 核对），未把模板文件（`.env.example`）复制过去。
- `remove` 后目录消失、`git worktree list` 无残留记录、被删除 worktree 的分支仍在（`git branch --list <分支>`）。
- `migrate` 后源工作区干净、目标改动与预期一致。
- `merge` 后当前分支含 worktree 分支的全部提交且无合并提交（纯线性历史时）；相关文件两树一致、验证命令通过；`remove` + `branch -d` 后 worktree 记录与分支都不在。

**判定口径**：上述与本次操作相关的项逐项通过方可声明完成；不通过时停下报告，**不静默放行**。

## 任务目标

按统一目录约定完成 worktree 的创建 / 列出 / 删除 / 迁移 / 合回：路径不嵌套、环境文件已补齐、删除前目录干净且分支保留、迁移不覆盖目标已有改动、合回不破坏仓库历史形态（纯线性仓库不造合并提交）。

## 注意事项

- **任务跟踪按环境能力可选**：环境提供 `TodoWrite` / `Task*` 工具时用原生任务清单跟踪（完成一项勾一项、收尾核对无未勾选项），否则退回对话内文本清单或落盘勾选（`.tasks/` 下 `- [x]`、未完成项写明处置）——不硬性依赖任一形态。

- **路径嵌套防护**：在 worktree 内再建 worktree 时，相对路径会拼出双层 `.zcf`；始终用绝对路径。
- **删除前先看目录**：`remove` 删除的是整个工作目录——先 `git status`，未提交内容要么迁移要么确认丢弃，不要直接 `--force`。
- **合回收尾**：rebase 前两侧都须干净；`--ff-only` 失败说明两侧已分叉（先 rebase 再合）；删分支只用 `-d`（`-D` 会丢弃未合入的独有提交）。
- **`list` 的常见异常**：目录被手工 `rm -rf` 后 `list` 仍显示记录（prune 可清理）；目录存在但分支被删（`git worktree repair` 或重建）。
- **性能与磁盘**：worktree 共享主仓库的 `.git`，不额外复制历史；但构建产物与依赖目录（如 `node_modules/`、`target/`）**不共享**，首次使用需各自安装。
- **跨平台**：路径含空格时全程加引号；Windows 下不要用 `~` 展开。
- **Windows 下 `remove` 后目录可能删不干净（实测踩过）**：`git worktree remove` 成功、git 注册已注销、目录内容已删净，但残留一个**空目录**被某进程句柄占住——MSYS 的 `rmdir` / PowerShell `Remove-Item -Recurse -Force` / `cmd rmdir /s /q` 全报「另一个程序正在使用此文件」，先 `tasklist` 排查是否有残留进程（如误把应用本体拉起来的 Electron / 测试子进程）；确认 git 侧干净（`git worktree list` 无记录、目录 `find` 无内容）后，剩下的空目录**等占用进程退出再删即可**，不影响仓库状态，如实报告用户即可，别反复重试删除命令。另注意：`remove` 前先 `cd` 出该 worktree 目录，shell 自身的工作目录就是最常见的占用者（`Permission denied` 首见就是这个）。
- **确认请求无应答时**：`list` / `add` 等可逆动作按原计划继续；`remove`（删目录）属不可逆动作，停下等待确认并在汇报中标明"该决策未获用户确认"。

## 输入

要执行的操作与对象（可选）：操作类型（add / list / remove / prune / migrate / merge）、worktree 名或路径、分支名、基础分支、迁移源、合并目标分支：
