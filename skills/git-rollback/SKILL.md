---
name: git-rollback
description: 交互式把 Git 分支回滚到历史版本：列分支 → 列版本 → 选 reset 或 revert → 二次确认后执行。当用户要求"把分支回滚到某个提交/tag""撤销一批提交""恢复到上一个版本""生成反向提交撤销误推"时使用——默认只读预览（dry-run）；reset 改写历史需用户明确确认、执行前先建备份分支，受保护分支额外确认，不提供 --force、不自动强推也不自动 push。边界：历史与对象清理（reflog expire / gc --prune=now / filter-repo）默认不做；清理分支用 git-clean-branches；提交改动用 commit-create。
disable-model-invocation: true
---

# Git 回滚（分支回滚到历史版本）

## 角色

你是回滚专员：**先列清楚（哪些分支、哪些版本），再让用户选目标与模式，二次确认后才执行**。默认只读预览，不执行任何改动。

## 适用与边界

**适用**：分支回滚到历史提交 / tag；误推的提交需要撤销；补丁发布后发现问题要退回；引导浏览分支历史（纯预览）。

**不适用（改用其他技能）**：

- 清理已合并 / 过期分支 → `git-clean-branches`；
- 创建 / 删除 worktree → `git-worktree`；
- 提交工作区改动 → `commit-create`。

**范围外**：`reflog expire` / `gc --prune=now` / `filter-repo` 等历史与对象清理**默认不做**；确需时先说明不可逆后果并取得明确同意。

## 要求

1. **先预览**：默认 `--dry-run`，只打印将要执行的完整命令，不执行。
2. **模式选择**：
   - `reset`：`git reset --hard <目标>` 改写历史，目标之后的提交将失去分支引用，远端需强推才能同步——**必须用户明确确认**；
   - `revert`：`git revert --no-edit <目标>..HEAD` 生成反向提交，保留历史，可普通 push——**默认推荐**。
3. **执行前建备份分支**：执行 `reset` 前先在当前 HEAD 建 `backup/<分支>-<时间戳>` 并打印还原命令。
4. **受保护分支额外确认**：分支为 `main` / `master` / `release/*` / `production` 等受保护分支且模式为 `reset` 时，说明影响面并再次确认。
5. **不提供 `--force`、不自动强推 / push**：强推命令（`git push --force-with-lease`）仅作为建议输出，由用户自行执行；不自动 push / merge / 建 PR。
6. **只动用户指定的分支**：回滚非当前分支时用 `git branch -f <分支> <目标>`，**不用** `git reset --hard`（它会连带移动当前分支的指针）。

## 参数

| 参数 | 含义 | 默认 |
|---|---|---|
| `--branch <分支>` | 要回滚的分支 | 交互选择 |
| `--target <rev>` | 目标版本（commit hash / tag / reflog 引用） | 交互选择近 `--depth` 条记录 |
| `--mode reset\|revert` | reset = 改写历史；revert = 生成反向提交 | 询问用户，推荐 revert |
| `--depth <n>` | 列出的历史版本条数 | 20 |
| `--dry-run` | 只预览将执行的命令 | **默认开启** |
| `--yes` | 跳过确认直接执行（仅在用户显式传入时） | 不跳过 |

## 执行步骤

1. **同步远端**：`git fetch --all --prune`；失败不阻塞但注明状态可能过期。
2. **列分支**：`git branch -a`，标出当前分支与受保护分支。
3. **选分支**：取 `--branch`；未指定则交互选择。
4. **列版本**：`git log --oneline -n <depth> <分支>` + `git tag --merged <分支>`（取该分支可达的 tag）+ `git reflog -n <depth>`。
5. **选目标**：取 `--target`；未指定则交互选择。
6. **选模式**：取 `--mode`；未指定则询问（说明 reset / revert 差异，推荐 revert）。
7. **出预览**：打印将执行的完整命令序列（含备份分支创建、若需要）；无 `--yes` 时**到此结束**，等待确认。
8. **执行**：
   - `reset`：`git branch backup/<分支>-<时间戳> <分支>`（备份）→ `git switch <分支>` → `git reset --hard <目标>`；**非当前分支改为** `git branch -f <分支> <目标>`（先 `git rev-parse <分支>` 记下原 sha）。
   - `revert`：`git switch <分支>` → `git revert --no-edit <目标>..HEAD`（冲突时停下交用户处理，不自行解决）。
9. **回退提示**：输出撤销本次回滚的命令（reset：`git reset --hard backup/<分支>-<时间戳>`；revert：`git revert --no-edit <新提交>`）与推送建议（revert 用普通 push；reset 用 `git push --force-with-lease`，由用户自行执行）。

## 验证

- 回滚后 `git log --oneline -n 5 <分支>` 与预期一致：reset → 首行等于目标提交；revert → 新增反向提交且原提交仍在。
- 目标分支之外的引用未被移动：`git branch --list` 与 `git reflog show <其他分支>` 复核。
- 备份分支存在（reset 场景）：`git branch --list 'backup/*'`。
- 未自动 push：`git status -sb` 显示本地领先 / 落后，交用户决定。
- 工作区未被意外破坏：`git status --porcelain` 的残留改动与预期一致（reset 前若有未提交改动，已先 stash 或提交）。

**判定口径**：五项均通过方可声明回滚完成；任一项不通过时停下报告，**不静默放行**。

## 任务目标

把用户指定的分支安全地回滚到目标版本：模式与影响面经用户确认、执行前有备份、其他引用未被牵连、未自动 push。

## 注意事项

- **任务跟踪按环境能力可选**：环境提供 `TodoWrite` / `Task*` 工具时用原生任务清单跟踪（完成一项勾一项、收尾核对无未勾选项），否则退回对话内文本清单或落盘勾选（`.tasks/` 下 `- [x]`、未完成项写明处置）——不硬性依赖任一形态。

- **reset vs revert**：reset 改写历史、需强推且可能影响协作者（他人已拉取该分支时其本地历史会分叉）；revert 生成新提交、保留历史、可普通 push。**有协作者的分支优先 revert**。
- **动分支指针前先确认 HEAD**：动非当前分支用 `git branch -f`；`git reset --hard` 只用于当前分支，否则会错误地移动当前分支指针。
- **工作区先清干净**：reset 前若工作区有未提交改动，先提交或 stash——`--hard` 会连同工作区一起还原。
- **大体积二进制 / LFS / 子模块**：回滚前确认 LFS 对象与子模块状态一致，避免回滚后取不到对应版本的对象。
- **CI 影响**：仓库启用流水线时，回滚推送后可能触发构建甚至自动部署——提示用户确认管控策略，避免误部署旧版本。
- **确认请求无应答时**：预览、fetch、列版本等可逆动作继续；回滚（改动历史与工作区）属不可逆动作，停下等待确认并在汇报中标明"该决策未获用户确认"。

## 输入

回滚范围（可选）：分支、目标版本（commit / tag）、模式（reset / revert）、是否已授权执行：
