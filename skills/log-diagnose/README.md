# log-diagnose

日志自动诊断：按 trace_id + 时间窗从 Kibana（多环境，`--env` 切换）拉取日志，定位错误根因；六类故障分类法；判定为 BUG（含查询超时引发报错）时产出修复任务 MD 与独立事故报告 MD 两份文档。

## 使用

用户给出 trace_id / 日志片段要求排查线上问题、定位错误根因、判断是否 bug 时自动触发。

## 能力

- 取数：`scripts/log-diagnose.py <trace_id> <time> [--env ...]`（Kibana internal search API）
- 分类法：BUG / 业务阻断 / 权限阻断 / 工作流阻断（上溯 cause 可升格）/ 基础设施性能 / 第三方系统失败
- 根因必须核对涉及代码当时的 commit（`check-commit.py` 检视）
- 数据佐证：涉及业务数据时用 `db-query` 查库（生产只读）
- 仅 BUG 出 MD（修复任务 + 事故报告），不自动派发修复

## 文件

- `SKILL.md` — 技能指令（唯一入口）
- `scripts/log-diagnose.py` — Kibana 取数脚本（参数 `--config` / `--out-dir`）
- `references/config.example.json` — 配置模板（复制为 `log-diagnose.config.json` 并填凭据，不入库）

## 配置（不同项目不同环境）

按加载顺序取用：① `--config <路径>`；② 项目级 `<项目根>/.claude/log-diagnose.config.json`（脚本从当前工作目录向上查找）；③ skill 同级默认。项目级配置适合不同项目接不同 Kibana 的场景，全局默认兜底。

## 依赖

- Python 3
- 本地创建 `log-diagnose.config.json`（含 Kibana 地址与凭据）
