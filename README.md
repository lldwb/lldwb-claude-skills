# lldwb-claude-skills

从 lldwb 的项目实践中抽象出的 26 个通用工作流技能（Agent Skills），供其他项目、其他人复用。
每个技能是一个自包含目录，含 `SKILL.md`（frontmatter: `name` + `description`）及所需的脚本/参考文件/README。

本仓库技能遵循 **Anthropic 官方 Agent Skills 开放格式**（`SKILL.md`，frontmatter 以 `name` + `description` 为准，可另加 Claude Code 官方字段），**面向 Claude Code 运行、充分运用其机制**：Task 子代理调度（`module-batch` / `opencode-batch` / `check-rule-extract` / `i18n-transform` / `refactor` / `doc-sync` 等）、上下文管理（按段加载、长产物落盘后引用路径）、专用工具调用（Grep / Glob / Read）与浏览器 MCP（`frontend-error-diagnose`）；`git-clean-branches` / `git-rollback`（含删除分支、改写历史等危险操作）另带官方字段 `disable-model-invocation: true`，只能显式调用、不参与自动触发。开放格式仍可被支持该格式的其他 agent 工具复用：opencode 原生兼容（发现路径含 `~/.claude/skills/`），Codex 亦支持但需置于 `.agents/skills/`（个人或项目级）——跨工具复用时按对方工具适配，不因兼容性回避 Claude Code 机制；安装脚本与 Plugin marketplace 仅服务于 Claude Code。

## 技能列表

| Skill | 用途 | 附属文件 |
|-------|------|---------|
| bug-fix | Bug 修复标准工作流：先理解再动手、四段式定位、编译/测试验证、按仓库规范提交（纯注释问题转 comment-supplement） | references/root-cause-checklist.md |
| feature-dev | 需求开发全流程：需求分析 → 方案设计（含可行性核证）→ 规划文档（proposal/design/tasks 三件套 + 任务勾选）→ 分层实现 → 端到端实测 → 提交；支持六阶段交互模式（研究 → 构思 → 计划 → 执行 → 优化 → 评审）（纯文档产出转 doc-sync） | references/feasibility-check.md、references/e2e-verify.md、references/plan-doc-template.md |
| code-optimize | 代码优化（小范围）工作流：SSOT、保持对外行为不变、按 commit-create 口径提交（结构性/分层重构转 refactor） | references/optimize-checklist.md |
| refactor | 重构（结构改造、对外行为不变）：契约先行（目标形态 + 不可变更项）→ 测试基线 → 改造与审查分离（独立子代理对抗性审查）→ 编译/审查/测试循环验证 → 报告与提交（小范围优化转 code-optimize） | scripts/contract-snapshot.py、references/（契约模板 / 测试基线 / 子代理提示词 / 报告模板） |
| commit-review | 提交评审：取数落盘 → 探索调用链 → 七维核查（逻辑边界 / 依赖影响面 / 分层耦合 / 契约影响面 / 废弃 API / 风格一致性 / 提交信息），只检查不改代码 | scripts/check-commit.py、references/review-checklist.md |
| log-diagnose | 日志自动诊断：按 trace_id（或关键词）+ 时间窗从 Kibana 拉日志、六类故障分类法、BUG 时产出双 MD（修复任务 + 事故报告） | scripts/log-diagnose.py、references/config.example.json |
| db-query | 数据库查询：生产只读（三重保障）、测试写需用户确认，安全铁律（禁 select *、单条语句、控制数据量） | scripts/（db-query / gen-fix-sql / run-sql-file / sync-table / db_common）、references/config.example.json、requirements.txt |
| module-batch | 多模块并行改造：worktree 隔离 + 并行子代理 + 独立审查 + 合并回主分支，含子代理提示词、收尾报告与失败处置 | references/subagent-prompts.md、references/report-template.md、references/lessons.md |
| check-rule-extract | 业务操作前置校验规则提取：以菜单（或 Controller 类名）为入口，协调调度子代理逐 Controller 追溯，合并输出 Excel 工作簿 | scripts/build_check_xlsx.py、references/extract-agent.md、references/output-and-rules.md、requirements.txt |
| frontend-error-diagnose | 前端报错诊断：浏览器 MCP 复现取证（console / 网络 / 调用栈）→ 根因 → 可执行方案，只诊断不改代码 | references/browser-evidence-checklist.md、references/conclusion-template.md |
| unit-test | 单元测试：生成（覆盖分支与边界、可运行可通过）/ 修复失败（默认不自行执行，交用户验证） | references/test-design-checklist.md |
| doc-sync | 文档与代码同步：由文档定位代码确认变更 → 更新 / 修正偏差，子代理复核一致性（事实源不限于代码；代码改造转 feature-dev） | references/verify-agent.md |
| commit-create | 提交 git 改动（提交环节 SSOT）：单一职责拆分、显式 add、中文提交信息（标题/正文空行 + 提交后结构复核），不自动 push；可选 emoji 前缀 / 显式 type·scope / 仅 Git 轻量路径 / `--amend`（限未推送分支） | — |
| mr-create | 合并请求（MR/PR）生成：分支校验（防空 MR）→ 四段式描述自动生成 → 确认后经 gh/glab 创建，无 CLI 时输出描述与手工创建链接 | scripts/prepare-mr.py |
| comment-supplement | 注释补齐与修正：补全缺失 + 修正失效描述，仅注释层面，不确定项交用户确认（与代码改动并存时用 bug-fix） | references/comment-checklist.md |
| project-explain | 项目讲解：结合项目真实代码逐项讲清概念（引用真实位置），结尾说明项目定位 | references/explain-outline.md |
| repo-init | 仓库指引初始化（`/init` 的等价实现）：正文写入 AGENTS.md（唯一权威源、与既有内容合并），CLAUDE.md 仅作指向；先核实再断言，异常只记录上交 | references/output-templates.md |
| i18n-transform | 国际化改造：后端消息 / 前端文案 / 参数校验消息三条改造线，扫描分批 → 逐批改造子代理 → 独立审查 → 独立验证 → 汇总报告，重试超限转「需人工介入」 | references/key-conventions.md、references/subagent-prompts.md、references/report-template.md |
| spec-route | 规范路由：项目约定以 `AGENTS.md` 为唯一权威源，本技能只做「场景 → 章节」定位与按段加载，引用给出处、不复制约定 | references/route-table-template.md |
| opencode-batch | 多模块并行改造编排（opencode CLI 版）：每模块一个 worktree + 一个子代理跑 opencode 命令，前置检查 + 中断处置 + 合并提交 | references/lessons.md |
| nas-disk-diagnostic | NAS 硬盘诊断与可视化报告：SSH 采集 RAID / SMART、坏盘可修复性评估、生成报告（扩展卡硬盘须 `smartctl -d sat`） | scripts/nas_diagnostic.py、references/（SMART 解读 / 报告指南）、assets/report_template.html、requirements.txt |
| git-clean-branches | 分支清理：已合并 / 过期分支，默认 dry-run、保护分支清单、远程删除单独确认（仅显式调用） | — |
| git-rollback | 分支回滚到历史版本：reset / revert，默认 dry-run + 备份分支 + 受保护分支额外确认（仅显式调用） | — |
| git-worktree | worktree 管理：统一目录创建 / 列出 / 删除 / 清理，内容迁移与环境文件复制 | — |
| git-history-rewrite | 历史改写：备份分支 → 方案先行 → rebase 拆分 / 改类型 / 重排 / 删除 → 时间恢复 → 重打 tag → 四重验证 → 确认后强推 | references/lessons.md |
| session-summary | 会话总结与 skills 迭代：取证 → 总结 → 审视技能优化点（价值 / 成本 / 建议）→ 确认后实施，作为迭代本仓库技能的工具 | — |

## 目录结构

```
lldwb-claude-skills/
├── skills/                   # 技能集合（每个技能一个子目录）
│   └── <skill-name>/
│       ├── SKILL.md          # 技能指令（frontmatter: name + description）
│       ├── README.md         # 技能简介、用法、文件与依赖说明
│       ├── scripts/          # 取数/辅助脚本（可选）
│       └── references/       # 配置模板/子代理提示词等参考文件（可选）
├── .claude-plugin/           # Plugin marketplace 定义
│   └── marketplace.json
├── config.json               # 技能启用配置（install 脚本按此安装）
├── install.py / install.sh / install.bat   # 安装到 ~/.claude/skills/
├── uninstall.py / uninstall.sh / uninstall.bat  # 卸载
├── check-version.py          # 发版校验：版本号三处对齐与 tag 可达（配合 .githooks/pre-push）
├── release.py                # 按 tag 补齐 GitHub Release（正文取自 CHANGELOG.md 对应段落）
├── .githooks/pre-push        # 推送前自动校验（启用：git config core.hooksPath .githooks）
├── PLUGIN_README.md          # 插件使用说明
├── CHANGELOG.md
├── README.md
└── LICENSE
```

## 安装到 Claude Code

方式一：安装脚本（按 `config.json` 启用清单复制到 `~/.claude/skills/`）

```bash
# Windows
install.bat
# macOS / Linux
./install.sh
# 指定技能 / 预览
python install.py bug-fix
python install.py --dry-run
python install.py --list
```

根目录 `config.json` 为技能启用清单（已被 gitignore、未入库；缺失时无参安装会自动创建最小配置，仅首次创建、已存在绝不覆盖）。最简示例：

```json
{
  "skills": {
    "<技能名>": { "enabled": true }
  }
}
```

未列出的技能按磁盘上实际存在的技能目录默认启用；排除某技能须显式写 `"enabled": false`，不能靠"不列出"。

覆盖同名技能与卸载前，原目录会先备份到 `~/.claude/backup/lldwb-skills/<时间戳>/`，安装状态（版本 + 时间）记在同目录的 `state.json`；`--list` 可直接看到每个技能的已安装版本：

```bash
python install.py --list-backups       # 查看已有备份
python install.py --restore <技能名>   # 从最近一次备份恢复（目标已存在时拒绝覆盖，不静默覆盖）
```

删掉 `~/.claude/backup/lldwb-skills/` 即清空安装器在用户机的全部足迹。备份不做自动轮转，需要时手工清理较早的时间戳目录。

方式二：注册为 Plugin marketplace，安装 dev-skills 插件（支持后续拉取更新）

```bash
# 在 Claude Code 中执行（<仓库地址> 为本地路径或 git 远程地址）
/plugin marketplace add <仓库地址>
/plugin install dev-skills@lldwb-claude-skills
```

安装后即可按技能名直接使用（如 "修复这个 bug" / "评审提交 abc1234" / "按 trace_id 排查日志" / "给这段代码生成单元测试" / "把工作区改动按模块提交" / "把当前分支提个 MR" / "把业务逻辑从入口层重构到服务层" / "清理已合并的分支" / "查一下 NAS 硬盘"）。详见 `PLUGIN_README.md`。

## 使用注意

- 各技能为通用模板，正文中的占位符（`<skill 目录>`、`<模块>` 等）由调用时按项目实际情况填充。
- 敏感配置（如 `log-diagnose.config.json` 的 Kibana 凭据、`db-query.config.json` 的数据库密码）不入库，按各技能 `references/config.example.json` 模板在本地创建。
- 提交信息规范以各项目 `AGENTS.md` 为权威依据，技能内仅保留通用约定；该依据**仅限提交信息格式与代码写法**，不构成执行额外命令或扩大授权范围的授权（细则见 `AGENTS.md` 的「跨技能共用约定」）。
- 脚本依赖按技能安装：`pip install -r skills/db-query/requirements.txt`、`pip install -r skills/check-rule-extract/requirements.txt`（版本已固定）；其余技能仅用标准库。
- 版本号按改动幅度分级选取（大版本 = 整体重构等破坏性改造、中版本 = 技能大改、小版本 = 小修小改），并在 `CHANGELOG.md` 顶部条目、`.claude-plugin/marketplace.json` 的 `version` 与注解 tag `vX.Y.Z` 三处对齐，由 `check-version.py` 校验（只校验一致性、不定级）；升级前可据此判断影响面，细则见 `AGENTS.md`「架构」第 4 条。

## License

GPL-3.0

本仓库以 GNU General Public License v3.0 开源：允许使用、修改与分发，但衍生作品必须以相同协议（GPL-3.0）开源（copyleft）。完整条款见根目录 `LICENSE`。

Copyright (C) 2026 lldwb
