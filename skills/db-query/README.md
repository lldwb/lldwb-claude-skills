# db-query

数据库查询（psycopg2，PostgreSQL 协议，可连 GaussDB 等 PG 兼容库，多环境）。生产只读（脚本拦截 + 会话只读 + 账号只读三重保障），测试环境可读写但写操作须用户确认并 `--allow-write`。

## 使用

用户要求查业务数据、核对数据状态、定位数据问题、验证修复前后数据时自动触发；也可显式要求"用 db-query skill 查某表在某条件下的数据"。

首次使用先在本地创建配置（含账号密码，不入库）：按加载顺序取 ① `--config <路径>`；② 项目级 `<项目根>/.claude/db-query.config.json`（脚本从当前工作目录向上查找）；③ skill 同级默认 `db-query.config.json`；模板见 `references/config.example.json`。

**边界**：需要写生产数据时不执行（生产只读，脚本拦截），改为给出只读查询结论与可执行的修复 SQL；从日志定位根因用 `log-diagnose`，代码缺陷修复用 `bug-fix`。

## 能力

- 安全铁律：生产只读三重保障、测试写操作须用户确认并 `--allow-write`、单条语句、控制数据量（默认 limit 100）、禁 `select *`，只读判定覆盖副作用形态（`EXPLAIN ANALYZE <写语句>`、`SELECT ... INTO <表>`、`nextval` 等按写处理）
- 多环境、多项目：`--env` 切换环境；配置按 显式路径 → 项目级 → skill 默认 的顺序加载，不同项目可接不同数据库
- 结果自动落盘为 `.txt`/`.json`（`<输出根>/<env>/<时间戳>-<摘要>`），输出根按配置来源归属，可用 `--out-dir` 覆盖
- 配套工具：查询结果转批量 UPDATE 修复 SQL（`gen-fix-sql.py`）、修复脚本逐条试跑（`run-sql-file.py`）、跨环境表数据同步（`sync-table.py`），均继承同一安全铁律
- 常见场景：核对单据状态/del_flag/审批流，结合 `log-diagnose` 佐证根因，修复前后数据验证，`information_schema` 结构确认

## 文件

- `SKILL.md` — 技能指令（唯一入口）
- `scripts/db-query.py` — 查询脚本（参数 `--env` / `--sql` / `--sql-file` / `--limit` / `--connect` / `--list-envs` / `--allow-write` / `--json` / `--config` / `--out-dir`）
- `scripts/db_common.py` — 公共模块（配置加载、建连、SQL 读写判定），供配套脚本复用
- `scripts/gen-fix-sql.py` — 查询结果 → 批量 UPDATE 修复 SQL（不连库）
- `scripts/run-sql-file.py` — SQL 文件逐条执行试跑（生产只读拦截、失败回滚）
- `scripts/sync-table.py` — 跨环境表数据同步（源只读、目标结构校验+清理+插入）
- `references/config.example.json` — 配置模板（复制为 `db-query.config.json` 并填凭据，不入库）

## 依赖

- Python 3：`pip install -r requirements.txt`（`psycopg2-binary`，其余脚本仅用标准库）
- 本地创建 `db-query.config.json`（含数据库账号密码，gitignored），按 `references/config.example.json` 模板填写
