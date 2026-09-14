# commit-review

提交评审：对指定修订号（commit sha/分支/tag）的提交质量给出有依据的明确结论（存在问题/无问题），只检查不改代码。

## 使用

用户要求"评审某个提交/PR 的质量""检查提交是否符合规范""排查某次提交引入的问题"时自动触发；也可显式要求"用 commit-review skill 评审 <修订号>"。

**边界**：需要落地修复评审发现的问题用 `bug-fix`；只是把工作区改动提交到本地用 `commit-create`。

## 能力

- 先取数（`scripts/check-commit.py`）再探索调用链，不局限于 diff
- 七个核查维度：逻辑与边界、依赖影响面、分层与耦合、契约变更影响面、废弃 API、风格与仓库约定一致性、提交信息规范（细则见 `references/review-checklist.md`）
- 问题按「严重 / 规范 / 建议」分级，结论可审计（每条判断指回 diff 行 / `文件:行` / 命令输出）
- 只检查不改代码，不自动修复、不自动提交，结论只有「存在问题 / 无问题」两种
- merge 提交按第一父级取数；diff 超长时读 `raw.diff` 取完整改动

## 文件

- `SKILL.md` — 技能指令（唯一入口）
- `references/review-checklist.md` — 逐维核查清单（怎么查 / 命中后怎么写进结论 / 分级 / 项目扩展钩子）
- `scripts/check-commit.py` — git 取数脚本（输出 `<sha>.summary.txt` + `<sha>.raw.diff`，参数 `--out-dir`）

## 依赖

- Python 3、git
