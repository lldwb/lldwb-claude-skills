# Changelog

## [1.0.0] - 2026-09-11

### 新增
- 初始化 6 个可复用 skills 抽象：fix-bug / code-optimize / commit-review / log-diagnose / module-batch / controller-check（含取数脚本与配置模板）
- 适配 Claude Code：子代理调度改为 Agent 工具（`subagent_type: general-purpose`），新增 `.claude-plugin/marketplace.json` 支持插件安装
- 新增 `db-query` 技能（第 7 个）：数据库查询（生产只读三重保障），log-diagnose / fix-bug 接入查库佐证
- 新增 `db-query` 取数下游配套脚本：修复 SQL 生成（gen-fix-sql.py）、SQL 文件试跑（run-sql-file.py）、跨环境表同步（sync-table.py）
- 新增安装/卸载脚本（install.py / uninstall.py 及 .sh/.bat 包装）、config.json 技能启用配置、PLUGIN_README.md
- 每个技能补充 README.md（简介、用法、文件与依赖说明）

### 变更
- log-diagnose / fix-bug：数据佐证与查库验证环节引用 db-query skill
- module-batch：子代理直接用 Agent 工具执行改造，不再经外部 AI CLI 中转

### 安全
- 敏感凭据（Kibana / 数据库）仅存 gitignored 的本地配置文件，不入库；db-query 生产只读（SQL 白名单 + 会话只读 + 账号只读）
