# commit-changes

提交工作区改动到本地 git 的标准工作流（commit 专员）：先审查 `git status` / `git diff`，按单一职责拆分提交，显式 `git add` 指定文件，撰写中文提交信息。

## 使用

用户要求"把当前工作区已修改的文件提交到本地仓库""按模块拆分提交""帮我写 commit 信息并提交"时自动触发；也可显式要求"用 commit-changes skill 提交这批改动"。被 `fix-bug` / `code-optimize` 等技能引用的"commit 专员"环节即本技能。

## 能力

- 拆分判定表：按模块拆分 vs 合并一次、格式化与业务改动分离、删除/重命名先确认
- 显式 `git add`（禁用 `-A` / `.`）+ `git diff --staged` 复核暂存内容
- 提交前自检：本地产物混入、敏感信息（凭据/IP/真实数据/本地路径）、未跟踪新文件遗漏
- 提交信息遵循项目规范（Conventional Commits、中文、无署名），fix 类按四段式组织
- 不自动 push / merge / PR，不 `--force`，不绕过钩子

## 文件

- `SKILL.md` — 技能指令（唯一入口）

## 依赖

- git
