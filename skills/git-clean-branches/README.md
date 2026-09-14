# git-clean-branches

安全查找并清理已合并或过期的 Git 分支。默认只读预览（dry-run），需用户确认后才执行删除；支持保护分支清单、自定义基准分支与远程分支清理。

## 使用

用户要求"清理已合并分支""删掉长期没动的分支""仓库分支太多整理一下"时**显式调用**（本技能禁用模型自动触发，含删除操作）。

```bash
/git-clean-branches --dry-run                 # 预览将要清理的分支，不执行任何删除
/git-clean-branches --stale 90                # 清理已合并到基准且超过 90 天未动的本地分支
/git-clean-branches --base release/v2.1 --remote --yes   # 清理已合并到 release/v2.1 的本地与远程分支
/git-clean-branches --force outdated-feature  # 强删一个未合并的本地分支（危险）
```

**参数**：`--base <分支>`（基准，默认 `main`/`master`）、`--stale <天数>`（过期阈值）、`--remote`（含远程）、`--dry-run`（默认）、`--yes`（跳过逐条确认）、`--force`（`-D` 强删未合并分支）。

## 能力

- 预检：`git fetch --all --prune` 同步远端 → 确定基准 → 读保护清单
- 盘点：已合并分支（`git branch --merged`，含远程时 `-r`）+ 过期分支（`git for-each-ref` 按提交日期筛）
- 报告：分「已合并」「过期」两段列出，无 `--yes` 时到此结束等确认
- 执行：本地 `git branch -d`（`--force` 时 `-D`）、远程 `git push origin --delete`，逐条报结果
- 收尾：复核剩余分支；被 worktree 占用的分支提示转 `git-worktree` 处置

## 保护分支

防止误删重要分支，在仓库 Git 配置里登记保护清单（支持通配符），命令自动读取：

```bash
git config --add branch.cleanup.protected develop
git config --add branch.cleanup.protected 'release/*'
git config --get-all branch.cleanup.protected
```

未配置时使用默认保护清单：当前 HEAD、`main`、`master`、`develop`、`release/*`。

## 安全边界

- **默认 dry-run**：未经用户确认不删除任何分支；用户未应答时只输出清单。
- **保护分支与未合并分支不动**：`--force` 仅在用户显式要求并逐条确认后使用。
- **远程删除单独确认**：影响协作者，需用户明确要求。
- **范围外**：删 tag、改写历史、`reflog expire` / `gc --prune=now` / `filter-repo` 不做。

## 文件

- `SKILL.md` — 技能指令（唯一入口）

## 依赖

- git（`fetch` / `branch` / `for-each-ref` / `push --delete`）
