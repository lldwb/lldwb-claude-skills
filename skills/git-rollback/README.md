# git-rollback

交互式把 Git 分支回滚到历史版本：列分支 → 列版本 → 选 `reset`（改写历史）或 `revert`（生成反向提交）→ 二次确认后执行。默认只读预览。

## 使用

用户要求"把分支回滚到某个提交 / tag""撤销一批提交""生成反向提交撤销误推"时**显式调用**（本技能禁用模型自动触发，含历史改写操作）。

```bash
/git-rollback                                                    # 全交互：选分支 → 选版本 → 选模式 → 确认
/git-rollback --branch feature/x                                 # 指定分支，其余交互
/git-rollback --branch main --target <sha> --mode reset --yes    # 硬回滚（危险，需 --yes 显式授权）
/git-rollback --branch release/v2 --target v2.0.5 --mode revert --dry-run   # 预览反向提交方案
```

**参数**：`--branch <分支>`、`--target <rev>`（commit / tag / reflog 引用）、`--mode reset|revert`、`--depth <n>`（列出条数，默认 20）、`--dry-run`（默认）、`--yes`（跳过确认）。

## 能力

- 预检：`git fetch --all --prune` → 列分支（标出当前分支与受保护分支）→ 列版本（`git log` + 可达 `git tag` + `git reflog`）
- 选择：分支 → 目标 → 模式（reset / revert，推荐 revert）
- 预览：打印将执行的完整命令序列，无 `--yes` 时到此结束
- 执行：reset 先建 `backup/<分支>-<时间戳>` 再 `git reset --hard`；revert 走 `git revert --no-edit <目标>..HEAD`
- 收尾：输出撤销本次回滚的命令 + 推送建议（强推命令由用户自行执行）

## 安全边界

- **默认 dry-run**：只预览不执行；回滚属不可逆动作，用户未应答时停下等待确认。
- **执行前有备份**：reset 前先建备份分支并可打印还原命令。
- **受保护分支额外确认**：`main` / `master` / `release/*` / `production` 等分支执行 reset 时逐次确认。
- **不提供 `--force`、不自动强推 / push**：强推命令仅作建议输出。
- **只动指定分支**：非当前分支用 `git branch -f`，不用 `git reset --hard`。
- **范围外**：`reflog expire` / `gc --prune=now` / `filter-repo` 等历史与对象清理默认不做。

## 文件

- `SKILL.md` — 技能指令（唯一入口）

## 依赖

- git（`fetch` / `branch` / `log` / `tag` / `reflog` / `switch` / `reset` / `revert`）
