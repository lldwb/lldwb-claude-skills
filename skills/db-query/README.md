# db-query

数据库查询（psycopg2，PostgreSQL 协议，可连 GaussDB 等 PG 兼容库，多环境）。生产只读（SQL 白名单 + 会话只读 + 账号只读三重保障），测试可读写但写操作须用户确认并 `--allow-write`。

## 使用

用户要求查业务数据、核对数据状态、定位数据问题、验证修复前后数据时自动触发。

## 能力

- 安全铁律：生产只读、测试写前必确认、单条语句、控制数据量（默认 limit 100）、禁 `select *`、密码只存 gitignored 配置、结果落盘
- 配套工具：查询结果转修复 SQL（`gen-fix-sql.py`）、修复脚本逐条试跑（`run-sql-file.py`）、跨环境表数据同步（`sync-table.py`），均继承同一安全铁律
- 常见场景：核对单据状态/del_flag/审批流、结合 `log-diagnose` 佐证根因、修复前后数据验证、information_schema 结构确认

## 文件

- `SKILL.md` — 技能指令（唯一入口）
- `scripts/db-query.py` — 查询脚本（参数 `--env` / `--sql` / `--sql-file` / `--limit` / `--connect` / `--allow-write` / `--config` / `--out-dir`）
- `scripts/db_common.py` — 公共模块（配置加载、建连、SQL 读写判定），供配套脚本复用
- `scripts/gen-fix-sql.py` — 查询结果 → 批量 UPDATE 修复 SQL（不连库）
- `scripts/run-sql-file.py` — SQL 文件逐条执行试跑（生产只读拦截、失败回滚）
- `scripts/sync-table.py` — 跨环境表数据同步（源只读、目标结构校验+清理+插入）
- `references/config.example.json` — 配置模板（复制为 `db-query.config.json` 并填凭据，不入库）

## 配置（不同项目不同环境）

按加载顺序取用：① `--config <路径>`；② 项目级 `<项目根>/.claude/db-query.config.json`（脚本从当前工作目录向上查找）；③ skill 同级默认。项目级配置适合不同项目接不同数据库的场景，全局默认兜底。

## 依赖

- Python 3、`pip install psycopg2-binary`
- 本地创建 `db-query.config.json`（含数据库账号密码）
