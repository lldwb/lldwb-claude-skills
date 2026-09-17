# mr-create

生成合并请求（MR/PR）的标准工作流：解析并校验源/目标分支 → 综合提交记录与用户补充说明自动生成描述 → 用户确认后经 `gh` / `glab` 创建。不合并、不删分支、不改代码、不 `--force`、不推送目标分支。

## 使用

用户要求"生成合并请求""把当前分支提个 MR / PR""按指定源分支和目标分支建 MR 并自动写描述""这条分支帮我提 PR"时自动触发；也可显式要求"用 mr-create skill 提 MR"。

取数前建议先 `git fetch origin`：远端才是合并请求的基线，源分支推送状态也取自本地 remote-tracking，不 fetch 时可能过期（fetch 失败则继续取数并注明状态可能过期）。

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
- 远端状态：源分支按状态键逐态报事实——`up-to-date` / `pushed-no-tracking`（一致）、`not-pushed`、`ahead`（本地领先）、`behind`（本地落后）、`diverged`（与 upstream 分叉）、`remote-only`（仅存于远端）、`pushed-diverged`（同名分支提交不一致）、`pushed-unknown`（领先/落后无法判定）；**脚本只报事实不判定**，该不该推送由「推送源分支」表（SKILL.md）按状态键处置
- 描述生成：四段式（变更背景/目的、主要改动点、影响范围、测试验证情况），仓库存在模板时以模板章节为准
- 创建通道：GitHub `compare` 链接、GitLab `merge_requests/new` 链接、`gh` / `glab` 命令模板（含 `--head` 跳过推送交互、`glab --fill` 会顺带 push 等已知坑）；无 CLI 时输出描述与手工创建链接
- 模板探测：`.github/` 下的 `PULL_REQUEST_TEMPLATE.md`（含大小写变体与 `PULL_REQUEST_TEMPLATE/` 子目录）、仓库根 `PULL_REQUEST_TEMPLATE.md`、`.gitlab/merge_request_templates/*.md`（大小写不敏感文件系统按 normcase 去重）
- 安全边界：创建前展示标题与完整描述待确认；不 merge / 不删分支 / 不 `--force` / 不改代码 / 不推送目标分支；只在「本地有分支、远端缺这些提交」（`not-pushed` / `ahead`）时、经用户单独同意后 `push -u`，`remote-only` 不推送，`behind` / `diverged` / `pushed-diverged` / `pushed-unknown` 停下报告

## 文件

- `SKILL.md` — 技能指令（唯一入口）
- `scripts/prepare-mr.py` — 分支校验与素材取数脚本（只取数不判定，不创建合并请求）
- `scripts/selftest.py` — `prepare-mr.py` 的自测（38 项用例，覆盖各失败分支与六种推送状态；**改过 prepare-mr.py 必须重跑**，其中 C36 顺带核对状态键与 SKILL.md 表格一致）

## 依赖

- Python 3（运行 `scripts/prepare-mr.py`，仅用标准库）
- git
- 可选：`gh`（GitHub）/ `glab`（GitLab）——缺失时技能输出描述与手工创建链接，功能不阻断
