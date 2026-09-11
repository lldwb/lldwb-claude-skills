---
name: db-query
description: 数据库查询技能（psycopg2，PostgreSQL 协议，可连 GaussDB 等 PG 兼容库，多环境）。当需要查业务数据、核对数据状态、定位数据问题、验证修复前后数据时使用。生产环境只读（脚本拦截 + 会话只读 + 账号只读三重保障），测试环境可读写但写操作必须先获得用户确认并 --allow-write。执行脚本为 <skill 目录>/scripts/db-query.py，配置 db-query.config.json（gitignored，含账号密码，按 references/config.example.json 模板创建）。即使未明确说"用 skill"，只要涉及查库就应使用本技能并遵循其安全铁律。
---

# 数据库查询

连接项目数据库查询数据。**先读安全铁律再执行**。

## 环境

以配置 `db-query.config.json` 的 `environments` 为准（查看可用环境：`python <skill 目录>/scripts/db-query.py --list-envs`），典型双环境：

| env | 名称 | 权限 |
| ---- | ---- | ---- |
| test | 测试环境 | 可读写（写需用户确认 + `--allow-write`） |
| prod | 生产环境 | **只读**（脚本拦截 + 会话只读 + 账号只读，三重保险） |

## 安全铁律

配置按**加载顺序**取用：① `--config <路径>` 显式指定；② 项目级 `<项目根>/.claude/db-query.config.json`（从当前工作目录向上查找，实现不同项目不同数据库环境切换）；③ skill 同级默认 `db-query.config.json`。均 gitignored，凭据不入库，按 `references/config.example.json` 模板创建。

1. **生产（prod）只读**: 只允许 SELECT/SHOW/EXPLAIN 及不含写关键字的 WITH。任何 DML/DDL 一律拒绝，
   即使带 `--allow-write` 也被脚本拦截。生产只做查询核对，不改数据。
2. **测试（test）可读写，但写前必确认**: 写语句（INSERT/UPDATE/DELETE/DDL 等）默认被拦截，
   须先向用户说明将执行什么写操作、影响哪些数据、是否可回滚，**获得用户明确同意后**再加
   `--allow-write` 执行。
3. **单条语句**: 禁止分号拼接多条 SQL。
4. **控制数据量**: 查询务必带条件/`LIMIT`（缺省上限走配置 default_limit=100）；禁止无条件的
   大表全表扫描。需要更多行时用 `--limit` 显式指定。
5. **禁 select \***: 明确列出所需列。
6. **密码安全**: 账号密码只存于 db-query.config.json（gitignored），不得写入任何输出文件、
   命令文档或聊天记录明文之外。
7. **结果落盘**: 每次查询自动输出到 `.tasks/db-query/<env>/<时间戳>-<摘要>.txt/.json`，
   重要查询结果可引用该路径给用户。

## 用法

```bash
# 查询（默认 env 走配置 default_env；切换环境加 --env）
python <skill 目录>/scripts/db-query.py --sql "SELECT id, name FROM sys_user WHERE del_flag='0' LIMIT 5" --env test
# SQL 过长可用文件
python <skill 目录>/scripts/db-query.py --sql-file query.sql --env prod
# 连通性检查
python <skill 目录>/scripts/db-query.py --connect --env prod
# 测试环境写操作（先获用户确认）
python <skill 目录>/scripts/db-query.py --sql "UPDATE sys_user SET name='x' WHERE id='1'" --env test --allow-write
```

脚本参数: `--env`（缺省走配置 default_env）、`--sql`/`--sql-file`、`--limit`、
`--connect`、`--list-envs`、`--allow-write`、`--json`、`--config`、`--out-dir`。

## 常见场景

- **核对业务数据状态**: 查单据状态、del_flag、审批流节点等
- **定位数据问题根因**: 结合 `log-diagnose` 的 trace_id/日志，查对应表数据佐证
- **修复前后验证**: 修复 bug 前查异常数据快照，修复后重查确认（引用输出文件路径）
- **结构确认**: 列名不确定时先查 information_schema.columns 再写查询，避免猜列名报错

## 注意事项

- 判定（是否 BUG、是否需修数据）由 agent 推理完成，脚本只取数，不给结论。
- 生产环境查询结果同样会落盘到 `.tasks/db-query/prod/`，注意引用时不要包含敏感行数据之外的账号口令。
- 若配置缺失或环境连不通，向用户报告具体错误并停止，不静默降级。
