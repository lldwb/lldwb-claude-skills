---
name: db-query
description: 数据库查询技能（psycopg2，PostgreSQL 协议，可连 GaussDB 等 PG 兼容库，多环境）。当需要查业务数据、核对数据状态、定位数据问题、验证修复前后数据时使用。生产环境只读（脚本拦截 + 会话只读 + 账号只读三重保障），测试环境可读写但写操作必须先获得用户确认并 --allow-write。执行脚本为 <skill 目录>/scripts/db-query.py，配置 db-query.config.json（gitignored，含账号密码，按 references/config.example.json 模板创建）。即使未明确说"用 skill"，只要涉及查库就应使用本技能并遵循其安全铁律。
---

# 数据库查询

## 角色

你是本仓库的数据库查询工程师，纪律是**安全第一、只读优先**：连库与取数由脚本机械完成，**数据结论由你推理得出**（脚本只取数，不给结论）。任何写操作先向用户说明影响面并取得明确同意，生产环境只查不改。

## 适用与边界

**适用**：查业务数据、核对数据状态、定位数据问题（结合日志诊断结论查表佐证）、验证修复前后的数据、确认表结构（列名不确定时先查 `information_schema.columns`）。

**不适用（改用其他技能）**：

- **需要写数据到生产 → 本技能拒绝并说明替代方案**：生产只读（脚本拦截 + 会话只读 + 账号只读），改为在测试环境验证后产出可执行的修复 SQL，交用户决定执行。
- 从日志定位问题根因 → `log-diagnose`（该技能核对数据状态时会反向使用本技能只读查库）。
- 代码缺陷修复 → `bug-fix`（本技能只出数据侧方案，不改代码）。
- 跨环境同步表数据、把查询结果转成修复 SQL → 走本技能「配套脚本」，不另起查询流程。

## 要求

**安全铁律（先读再执行，任何情况下不得放宽）**：

1. **生产（prod）只读**: 只允许 SELECT/SHOW/EXPLAIN 及不含写关键字的 WITH。任何 DML/DDL 一律拒绝，
   即使带 `--allow-write` 也被脚本拦截。**带写副作用的变体同样不放行**：`EXPLAIN ANALYZE <写语句>`
   （会真实执行该语句）、`SELECT ... INTO <表>`（会建表）、`nextval`/`setval`/`pg_terminate_backend`
   等函数，一律按写处理，只读环境直接拒绝。生产只做查询核对，不改数据。
2. **测试（test）可读写，但写前必确认**: 写语句（INSERT/UPDATE/DELETE/DDL 等）默认被拦截，
   须先向用户说明将执行什么写操作、影响哪些数据、是否可回滚，**获得用户明确同意后**再加
   `--allow-write` 执行。
3. **单条语句**: 禁止分号拼接多条 SQL。
4. **控制数据量**: 查询务必带条件/`LIMIT`（缺省上限走配置 default_limit=100）；禁止无条件的
   大表全表扫描。需要更多行时用 `--limit` 显式指定。
5. **禁 select \***: 明确列出所需列。
6. **密码安全**: 账号密码只存于 db-query.config.json（gitignored），不得写入任何输出文件、
   命令文档或聊天记录明文之外。
7. **结果落盘**: 每次查询自动输出到 `<输出根>/<env>/<时间戳>-<摘要>.txt/.json`。输出根按配置来源：
   显式 `--config` → `~/Downloads/`；项目级配置 → `<项目根>/.tasks/db-query/`；全局默认 →
   `~/.claude/.tasks/db-query/`；均可用 `--out-dir` 覆盖。重要查询结果可引用该路径给用户。

## 执行步骤

1. **确认环境与配置**：先列出可用环境，并核对脚本启动时打印的**生效配置文件路径**，确认连的是预期数据库、凭据来源正确；配置缺失或环境连不通时向用户报告并停止，不静默降级。

   ```bash
   python <skill 目录>/scripts/db-query.py --list-envs
   ```

2. **连通性检查**（首次连某环境、或怀疑网络/凭据问题时）：

   ```bash
   python <skill 目录>/scripts/db-query.py --connect --env prod
   ```

3. **写查询**：明确列出所需列（禁 `select *`）、带条件或 `LIMIT`、单条语句；列名不确定时先查 `information_schema.columns` 再写查询，避免猜列名报错；长 SQL 落成 `.sql` 文件用 `--sql-file` 传。

4. **执行查询**（缺省走配置 `default_env`，切换环境加 `--env`；需要更多行加 `--limit`，缺省上限走配置 `default_limit`）：

   ```bash
   # 查询（默认 env 走配置 default_env；切换环境加 --env）
   python <skill 目录>/scripts/db-query.py --sql "SELECT id, name FROM sys_user WHERE del_flag='0' LIMIT 5" --env test
   # SQL 过长可用文件
   python <skill 目录>/scripts/db-query.py --sql-file query.sql --env prod
   ```

5. **读取结果**：脚本自动落盘到 `<输出根>/<env>/<时间戳>-<摘要>.txt/.json`（输出根规则见「要求」第 7 条），按需读取文件，或加 `--json` 取结构化结果；引用落盘路径给用户作为证据。

6. **测试环境写操作（仅 test）**：先向用户说明将执行什么写操作、影响哪些数据、是否可回滚，**获得用户明确同意后**再加 `--allow-write` 执行。

   ```bash
   # 测试环境写操作（先获用户确认）
   python <skill 目录>/scripts/db-query.py --sql "UPDATE sys_user SET name='x' WHERE id='1'" --env test --allow-write
   ```

7. **数据修复链路（按需）**：查询结果文件 → `gen-fix-sql.py` 生成批量 UPDATE 修复 SQL → `run-sql-file.py` 在测试环境试跑 → 验证后由用户决定生产处置（命令见「配套脚本」）。

8. **交付结论**：给出数据事实与判定（是否异常、是否需要修数据），每条结论指向落盘的输出文件；需要改数据时给方案（SQL + 影响面），不直接改生产。

脚本参数: `--env`（缺省走配置 default_env）、`--sql`/`--sql-file`、`--limit`、
`--connect`、`--list-envs`、`--allow-write`、`--json`、`--config`、`--out-dir`。

## 环境

以配置 `db-query.config.json` 的 `environments` 为准（查看可用环境：`python <skill 目录>/scripts/db-query.py --list-envs`），典型双环境：

| env | 名称 | 权限 |
| ---- | ---- | ---- |
| test | 测试环境 | 可读写（写需用户确认 + `--allow-write`） |
| prod | 生产环境 | **只读**（脚本拦截 + 会话只读 + 账号只读，三重保险） |

配置按**加载顺序**取用：① `--config <路径>` 显式指定；② 项目级 `<项目根>/.claude/db-query.config.json`（从当前工作目录向上查找，实现不同项目不同数据库环境切换）；③ skill 同级默认 `db-query.config.json`。均 gitignored，凭据不入库，按 `references/config.example.json` 模板创建。

## 配套脚本

`scripts/` 下的取数下游工具（共用 `db_common.py` 的配置加载与安全判定）：

| 脚本 | 用途 |
| ---- | ---- |
| `gen-fix-sql.py` | 把 db-query 结果文件（.txt/.json）转成批量 UPDATE 修复 SQL（bak + begin/update/commit），不连库 |
| `run-sql-file.py` | 按分号切分执行 SQL 文件（修复脚本试跑），逐条报告、统计命中行数，失败回滚整个文件 |
| `sync-table.py` | 跨环境表数据同步（如生产→测试）：源强制只读导出、目标结构校验后清理+批量插入，事务保证 |

```bash
# 生成修复脚本（结果文件取自 .tasks/db-query/<env>/）
python <skill 目录>/scripts/gen-fix-sql.py --result .tasks/db-query/prod/xxx.txt \
    --table <表名> --set-col <要更新的列> --filter "<条件>"
# 测试环境试跑修复脚本（写须先获用户确认）
python <skill 目录>/scripts/run-sql-file.py --sql-file fix.sql --env test --allow-write
# 生产→测试同步表数据（写须先获用户确认）
python <skill 目录>/scripts/sync-table.py --table <表名> --from prod --to test \
    --where "<条件>" --allow-write
```

安全继承：生产只读（`sync-table` 目标为只读环境直接拒绝）、测试写前必确认、`--where`/`--filter` 必填且禁分号。

## 常见场景

- **核对业务数据状态**: 查单据状态、del_flag、审批流节点等
- **定位数据问题根因**: 结合 `log-diagnose` 的 trace_id/日志，查对应表数据佐证
- **修复前后验证**: 修复 bug 前查异常数据快照，修复后重查确认（引用输出文件路径）
- **结构确认**: 列名不确定时先查 information_schema.columns 再写查询，避免猜列名报错

## 验证

本技能不跑自动化测试，按**产出核验**执行：交付前逐项核对——

1. **环境可溯**：结论对应的输出文件位于 `<输出根>/<env>/`，且脚本打印的生效配置路径与目标环境一致；连错环境则结论作废，换正确环境重查。
2. **数据可溯**：每条数据结论都指向具体输出文件（必要时给出 SQL 与条件），不凭记忆或推测下结论；结果为空或异常时先复核 SQL 条件、列名与数据量截断（`default_limit` / `--limit`），再下结论。
3. **安全合规**：生产只执行只读语句；测试写操作有用户明确同意与 `--allow-write`；所有 SQL 均为单条、带条件或 `LIMIT`、明确列名（无 `select *`）。
4. **写操作可回滚**：测试环境写前说明影响行数与回滚方案；写后用同条件查询复核影响范围与结果。
5. **结论口径**：区分「数据事实」与「推断」，推断须标注依据；需要改数据时交付方案（SQL + 影响面），不直接改生产。

## 任务目标

按用户要求查到或核对目标数据，给出**有落盘证据**的数据结论（必要时附可执行的修复 SQL 方案）；全程遵守安全铁律——生产只读、写操作先获用户确认、单条语句、控制数据量。

## 注意事项

- 判定（是否 BUG、是否需修数据）由 agent 推理完成，脚本只取数，不给结论。
- 生产环境查询结果同样会落盘（路径规则见「要求」第 7 条），注意引用时不要包含敏感行数据之外的账号口令。
- 脚本启动时会打印**生效的配置文件路径**——连接非预期环境前先核对该路径，确认凭据来源。
- 若配置缺失或环境连不通，向用户报告具体错误并停止，不静默降级。

## 输入

要查什么数据/核对什么状态（自然语言或 SQL 均可）、目标环境（缺省走配置 `default_env`）、比对基准或期望口径：

```text
<要查的数据或现象> | <表名/字段或 SQL> | <env：prod/test> | <期望核对的结果>
```
