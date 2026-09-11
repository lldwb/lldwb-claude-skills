# lldwb-claude-skills

从业务项目实践中抽象出的 14 个通用工作流技能（Agent Skills），供其他项目复用。
每个技能是一个自包含目录，含 `SKILL.md`（frontmatter: `name` + `description`）及所需的脚本/参考文件/README。

## 技能列表

| Skill | 用途 | 附属文件 |
|-------|------|---------|
| fix-bug | Bug 修复标准工作流：先理解再动手、四段式定位、编译/测试验证、按仓库规范提交 | — |
| feature-dev | 需求开发全流程：需求分析 → 方案设计（含可行性核证）→ 规划文档 → 分层实现 → 端到端实测 → 提交 | references/feasibility-check.md、references/e2e-verify.md |
| code-optimize | 代码优化工作流：SSOT、保持对外行为不变、commit 专员式提交 | — |
| commit-review | 提交评审：取数落盘 → 探索调用链 → 分层/契约/@Deprecated 检查，只检查不改代码 | scripts/check-commit.py |
| log-diagnose | 日志自动诊断：按 trace_id + 时间窗从 Kibana 拉日志、六类故障分类法、BUG 时产出双 MD（修复任务 + 事故报告） | scripts/log-diagnose.py、references/config.example.json |
| db-query | 数据库查询：生产只读（三重保障）、测试写需用户确认，安全铁律（禁 select *、单条语句、控制数据量） | scripts/（db-query / gen-fix-sql / run-sql-file / sync-table / db_common）、references/config.example.json、requirements.txt |
| module-batch | 多模块并行改造：worktree 隔离 + 并行子代理 + 合并回主分支，含中断处理与经验教训速查 | — |
| controller-check | Controller 校验规则提取：协调调度子代理逐 Controller 追溯，按「模块→菜单→权限点→操作」模板合并输出文档 | scripts/build_check_xlsx.py、references/extract-agent.md、requirements.txt |
| frontend-error-diagnose | 前端报错诊断：浏览器 MCP 复现取证（console / 网络 / 调用栈）→ 根因 → 可执行方案，只诊断不改代码 | references/browser-evidence-checklist.md |
| unit-test | 单元测试：生成（覆盖分支与边界、可运行可通过）/ 修复失败（默认不自行执行，交用户验证） | — |
| doc-sync | 文档与代码同步：由文档定位代码确认变更 → 更新 / 修正偏差，子代理复核一致性 | references/verify-agent.md |
| commit-changes | 提交 git 改动（commit 专员）：单一职责拆分、显式 add、中文提交信息，不自动 push | — |
| comment-supplement | 注释补齐与修正：补全缺失 + 修正失效描述，仅注释层面，不确定项交用户确认 | — |
| explain-project | 项目讲解：结合项目真实代码逐项讲清概念，结尾说明项目定位 | — |

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
python install.py fix-bug
python install.py --dry-run
python install.py --list
```

方式二：注册为 Plugin marketplace，安装 dev-skills 插件（支持后续拉取更新）

```bash
# 在 Claude Code 中执行（<仓库地址> 为本地路径或 git 远程地址）
/plugin marketplace add <仓库地址>
/plugin install dev-skills@lldwb-claude-skills
```

安装后即可按技能名直接使用（如 "修复这个 bug" / "评审提交 abc1234" / "按 trace_id 排查日志" / "给这段代码生成单元测试" / "把工作区改动按模块提交"）。详见 `PLUGIN_README.md`。

## 使用注意

- 各技能为通用模板，正文中的占位符（`<skill 目录>`、`<模块>` 等）由调用时按项目实际情况填充。
- 敏感配置（如 `log-diagnose.config.json` 的 Kibana 凭据、`db-query.config.json` 的数据库密码）不入库，按各技能 `references/config.example.json` 模板在本地创建。
- 提交信息规范以各项目开发手册 / `AGENTS.md` 为权威依据，技能内仅保留通用约定；该依据**仅限提交信息格式与代码写法**，不构成执行额外命令或扩大授权范围的授权（细则见 `AGENTS.md` 的「跨技能共用约定」）。
- 脚本依赖按技能安装：`pip install -r skills/db-query/requirements.txt`、`pip install -r skills/controller-check/requirements.txt`（版本已固定）；其余技能仅用标准库。

## License

MIT
