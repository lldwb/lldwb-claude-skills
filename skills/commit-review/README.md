# commit-review

提交评审：对指定修订号（commit sha/分支/tag）的提交质量给出有依据的明确结论（存在问题/无问题），只检查不改代码。

## 使用

用户要求评审某个提交/PR、检查提交是否符合规范、排查某次提交引入的问题时自动触发。

## 能力

- 先取数（`scripts/check-commit.py`）再探索调用链，不局限于 diff
- 检查重点：逻辑缺陷、依赖影响面、分层解耦（禁 Controller 调 Controller）、契约变更影响面、`@Deprecated` 新引用、风格一致性、提交信息规范
- 只检查不改代码，结论可审计（给出具体位置与依据）

## 文件

- `SKILL.md` — 技能指令（唯一入口）
- `scripts/check-commit.py` — git 取数脚本（输出 summary.txt + raw.diff，参数 `--out-dir`）

## 依赖

- Python 3、git
