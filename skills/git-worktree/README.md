# git-worktree

管理 Git worktree：在项目平级的统一目录下创建、列出、删除与清理，并支持未提交内容 / stash 迁移、环境文件自动复制、按项目 IDE 命令打开。

## 使用

用户要求"开一个 worktree""在独立目录里做这个需求""并行开发两个分支互不干扰""把当前未提交的改动挪到另一个 worktree""清理失效的 worktree 记录"时自动触发。

```bash
/git-worktree add feature-ui                      # 从 main/master 创建名为 feature-ui 的新分支
/git-worktree add feature-ui -b feature/new-ui    # 指定分支名
/git-worktree add feature-ui -o                   # 创建后直接用 IDE 打开
/git-worktree list                                # 列出所有 worktree 与状态
/git-worktree remove feature-ui                   # 删除 worktree（保留分支）
/git-worktree prune                               # 清理失效记录
/git-worktree migrate feature-ui --from <源>      # 迁移未提交改动
/git-worktree migrate feature-ui --stash          # 迁移 stash 内容
```

## 能力

- 主仓库路径推导：在 worktree 内执行也能经 `git rev-parse --git-common-dir` 算回主仓库，worktree 统一建在 `<worktree 根目录>`（默认 `<主仓库同级>/.zcf/<项目名>/`，可按项目约定替换）
- 智能默认：分支名缺省用 worktree 名、基础分支取 `main`/`master`、目录名缺省用分支名
- 环境文件补齐：扫描 `.gitignore`，把其中列出的 `.env` / `.env.*` 复制到新 worktree（跳过 `.env.example` 等模板）
- IDE 集成：`-o` 或用项目实际 IDE 命令打开，命令不在 PATH 时跳过不报错
- 内容迁移：worktree 之间迁移未提交改动，或把 stash 应用到目标 worktree（迁移前校验源有内容、目标干净）
- 安全：绝对路径防嵌套、路径 / 分支占用检查、删除前确认目录干净、删除保留分支

## 目录约定

```
<父目录>/
├── <项目>/                  # 主仓库
│   ├── .git/
│   └── src/
└── .zcf/
    └── <项目>/              # worktree 根目录
        ├── <worktree1>/
        └── <worktree2>/
```

## 安全边界

- **`remove` 属不可逆动作**：删除前确认目录干净，有未提交改动时停下询问，不用 `--force` 绕过。
- **不删分支**：`remove` 只删工作目录，分支保留；需要删分支转 `git-clean-branches`。
- **不覆盖目标**：`add` 时目录 / 分支被占用则停下询问；`migrate` 时目标非空则先停下。

## 文件

- `SKILL.md` — 技能指令（唯一入口）

## 依赖

- git（worktree 支持：`git worktree add|list|remove|prune`）
- 可选：项目实际的 IDE 命令行工具（缺失时自动跳过）
