# mr-create

生成合并请求（MR/PR）的标准工作流：解析并校验源/目标分支 → 综合提交记录与用户补充说明自动生成描述 → 确认后经 `gh` / `glab` 创建。

## 使用

用户要求"生成合并请求""把当前分支提个 MR / PR""按指定源分支和目标分支建 MR 并自动写描述"时自动触发；也可显式要求"用 mr-create skill 提 MR"。

```
# 源分支默认当前分支，目标分支默认探测 origin/HEAD → main / master
python <skill 目录>/scripts/prepare-mr.py

# 显式指定
python <skill 目录>/scripts/prepare-mr.py --source <源分支> --target <目标分支>
```

## 能力

- 分支解析：源分支默认当前分支；目标分支默认探测 `origin/HEAD` → `main` / `master`（要求先确认默认主分支名，不猜）
- 前置校验（不通过即退出、不产出素材）：是 git 仓库 / 分支存在 / 源与目标非同一提交 / 有共同祖先 / 存在有效差异——**防空合并请求**
- 取数落盘：仓库与远端（平台识别 + 可用 CLI）、分支与 merge-base、领先提交数与 `--shortstat`、按目录聚合的变更范围、提交记录（`--pretty=medium`，保留标题与正文空行）、文件清单、diff（默认截断 400 行 + 完整 `raw.diff`）
- 远端状态：源分支未推送 / 已推送但本地领先 / upstream 一致 / 仅存于远端 / 同名分支提交不一致，只报事实不判定
- 创建通道：GitHub `compare` 链接、GitLab `merge_requests/new` 链接、`gh` / `glab` 命令模板（含 `--head` 跳过推送交互、`glab --fill` 会顺带 push 等已知坑）
- 模板探测：`.github/PULL_REQUEST_TEMPLATE*`、`.gitlab/merge_request_templates/*`（大小写不敏感文件系统按 normcase 去重）
- 描述生成：四段式（变更背景/目的、主要改动点、影响范围、测试验证情况），有模板时以模板章节为准
- 安全边界：创建前展示标题与完整描述待确认；不 merge / 不删分支 / 不 `--force` / 不改代码；源分支未推送时先征得同意再 `push -u`

## 文件

- `SKILL.md` — 技能指令（唯一入口）
- `scripts/prepare-mr.py` — 分支校验与素材取数脚本（只取数不判定，不创建合并请求）

## 依赖

- git
- 可选：`gh`（GitHub）/ `glab`（GitLab）——缺失时技能输出描述与手工创建链接，功能不阻断
