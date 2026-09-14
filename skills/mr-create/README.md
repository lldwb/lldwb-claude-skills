# mr-create

生成合并请求（MR/PR）的标准工作流：解析并校验源/目标分支 → 综合提交记录与用户补充说明自动生成描述 → 用户确认后经 `gh` / `glab` 创建。不合并、不删分支、不改代码、不 `--force`、不推送目标分支。

## 使用

用户要求"生成合并请求""把当前分支提个 MR / PR""按指定源分支和目标分支建 MR 并自动写描述""这条分支帮我提 PR"时自动触发；也可显式要求"用 mr-create skill 提 MR"。

```bash
# 源分支默认当前分支，目标分支默认探测 origin/HEAD → main / master
python <skill 目录>/scripts/prepare-mr.py

# 显式指定
python <skill 目录>/scripts/prepare-mr.py --source <源分支> --target <目标分支>
```

**边界**：工作区改动尚未提交、要先落成本地提交用 `commit-create`；只评审已存在的提交或合并请求质量用 `commit-review`。

## 能力

- 分支解析与前置校验：源分支默认当前分支；目标分支默认探测 `origin/HEAD` → `main` / `master`（不猜默认主分支名）；校验不通过（非 git 仓库 / 分支不存在 / 源与目标同一提交 / 无共同祖先 / 无有效差异）即退出、不产出素材——**防空合并请求**
- 取数落盘：仓库与远端（平台识别 + 可用 CLI）、分支与 merge-base、领先提交数与 `--shortstat`、按目录聚合的变更范围、提交记录（保留标题与正文）、文件清单、diff（默认截断 400 行 + 完整 `raw.diff`）
- 远端状态：源分支未推送 / 已推送但本地领先 / upstream 一致 / 仅存于远端 / 同名分支提交不一致，只报事实不判定
- 描述生成：四段式（变更背景/目的、主要改动点、影响范围、测试验证情况），仓库存在模板时以模板章节为准
- 创建通道：GitHub `compare` 链接、GitLab `merge_requests/new` 链接、`gh` / `glab` 命令模板（含 `--head` 跳过推送交互、`glab --fill` 会顺带 push 等已知坑）；无 CLI 时输出描述与手工创建链接
- 模板探测：`.github/PULL_REQUEST_TEMPLATE*`、`.gitlab/merge_request_templates/*`（大小写不敏感文件系统按 normcase 去重）
- 安全边界：创建前展示标题与完整描述待确认；不 merge / 不删分支 / 不 `--force` / 不改代码 / 不推送目标分支；源分支未推送时先征得同意再 `push -u`

## 文件

- `SKILL.md` — 技能指令（唯一入口）
- `scripts/prepare-mr.py` — 分支校验与素材取数脚本（只取数不判定，不创建合并请求）

## 依赖

- Python 3（运行 `scripts/prepare-mr.py`，仅用标准库）
- git
- 可选：`gh`（GitHub）/ `glab`（GitLab）——缺失时技能输出描述与手工创建链接，功能不阻断
