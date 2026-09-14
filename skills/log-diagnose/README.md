# log-diagnose

日志自动诊断：按 trace_id + 时间窗从 Kibana（多环境，`--env` 切换）拉取日志，六类故障分类法定位错误根因；判定为 BUG（含查询超时引发报错）时产出修复任务 MD 与独立事故报告 MD 两份文档，不自动派发。

## 使用

用户给出 trace_id / 日志片段要求排查线上问题、定位错误根因、判断是否 bug 时自动触发；也可显式要求"用 log-diagnose skill 排查这个 trace"。

首次使用先在本地创建配置（含 Kibana 地址与凭据，不入库）：按加载顺序取 ① `--config <路径>`；② 项目级 `<项目根>/.claude/log-diagnose.config.json`（脚本从当前工作目录向上查找）；③ skill 同级默认 `log-diagnose.config.json`；模板见 `references/config.example.json`。

**输出路径按配置来源决定**（与配置归属一致）：显式 `--config` → `~/Downloads/<env>/`（不拼 `log-diagnosis` 段）；项目级配置 → `<项目根>/.tasks/log-diagnosis/<env>/`；全局默认 → `~/.claude/.tasks/log-diagnosis/<env>/`；可用 `--out-dir <路径>` 覆盖。

**边界**：需要改代码修复诊断出的缺陷用 `bug-fix`；需要核对业务数据状态用 `db-query`（生产只读）；前端（浏览器侧）报错用 `frontend-error-diagnose`；需要评审提交或核对缺陷由哪次提交引入用 `commit-review`。

## 能力

- 取数：`scripts/log-diagnose.py <trace_id> <time> [--env ...]`（Kibana internal search API；只取数、解析、落盘，不替 agent 下结论）
- 六类分类法：BUG / 业务阻断 / 权限阻断 / 工作流阻断（unwrap 到 BUG 类 cause 可升格）/ 基础设施性能 / 第三方系统失败
- 查询超时（`QueryTimeoutException`、DB 侧取消）已抛错阻断请求 → 判为 BUG；未触发超时、无报错的慢 SQL 仅提示优化
- 判定为 BUG 才产出两份 MD（修复任务 + 独立事故报告），全程不自动派发
- 根因必须核对涉及代码当时的 commit（工作区与线上不一致时以线上版本为准并注明）
- 数据佐证：根因涉及业务数据时用 `db-query` 只读查库核对
- 第三方系统调用失败必须给出三要素：调用地址、请求体、响应体

## 文件

- `SKILL.md` — 技能指令（唯一入口）
- `scripts/log-diagnose.py` — Kibana 取数脚本（参数 `--env` / `--list-envs` / `--config` / `--out-dir` / `--kw`（无 trace_id 时按关键词 + 时间窗检索，可多次指定、AND 组合））
- `references/config.example.json` — 配置模板（复制为 `log-diagnose.config.json` 并填凭据，不入库）

## 依赖

- Python 3（仅标准库，无需三方依赖）
- 本地创建 `log-diagnose.config.json`（含 Kibana 地址与凭据，gitignored），按 `references/config.example.json` 模板填写
