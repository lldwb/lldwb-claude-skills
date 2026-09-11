#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库查询脚本（psycopg2，PostgreSQL 协议；可连 GaussDB 等 PG 兼容库）。
只负责按 SQL 取数，不做业务判定（判定由调用方 agent 完成）。

环境（--env 选择，缺省走配置 default_env）:
    测试环境：可读写，但 DML/DDL 默认拦截，须加 --allow-write 显式确认后执行
    生产环境：只读账号 + 只读会话，DML/DDL 一律拒绝

config 结构: { "default_env": "test",
               "environments": { "<env>": { hosts/port/database/schema/username/password/read_only/... } } }

用法:
    python db-query.py --sql "SELECT id, name FROM sys_user WHERE id='1'" [--env test] [--limit 100]
    python db-query.py --sql-file query.sql [--env prod]
    python db-query.py --connect [--env prod]     # 仅测试连通性
    python db-query.py --list-envs

输出（写到 <输出根>/<env>/）:
    <yyyyMMdd-HHmmss>-<摘要>.txt   表格文本（含列头与行列数）
    <yyyyMMdd-HHmmss>-<摘要>.json  行数据（对象数组）
    输出根按配置来源决定: 显式 --config → ~/Downloads；项目级配置 → <项目根>/.tasks/；
    全局默认 → ~/.claude/.tasks/；均可用 --out-dir 覆盖
stdout: 配置文件来源 / 连接信息 / 行列数 / 耗时 / 输出路径
"""
import sys
import os
import json
import time
import re
import argparse
import codecs

# Windows 控制台缺省 GBK，强制 UTF-8 输出环境中文名。
# 提前规避乱码：stdout/stderr 可能被 GBK 控制台消费，或被 AI 以
# UTF-8 捕获；统一按 UTF-8 输出，两处均不乱码；
# reconfigure 不可用时回退到基于底层 buffer 的 UTF-8 写入器兜底。
def _ensure_utf8():
    for name in ("stdout", "stderr"):
        stream = getattr(sys, name, None)
        if stream is None:
            continue
        try:
            stream.reconfigure(encoding="utf-8", errors="backslashreplace")
            continue
        except Exception:
            pass
        try:
            buf = getattr(stream, "buffer", None)
            if buf is not None and hasattr(stream, "write"):
                setattr(sys, name, codecs.getwriter("utf-8")(buf, errors="backslashreplace"))
        except Exception:
            pass


_ensure_utf8()

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CONFIG = os.path.join(SCRIPT_DIR, "..", "db-query.config.json")
GLOBAL_OUT_DIR = os.path.join(os.path.expanduser("~"), ".claude", ".tasks", "db-query")
CONFIG_FILENAME = "db-query.config.json"


def find_project_config():
    """从当前工作目录向上逐级查找项目级配置 <项目根>/.claude/<CONFIG_FILENAME>，命中返回路径，否则 None。
    项目级配置优先于 skill 全局默认，实现不同项目不同数据库环境的切换。"""
    d = os.getcwd()
    while True:
        cand = os.path.join(d, ".claude", CONFIG_FILENAME)
        if os.path.exists(cand):
            return cand
        parent = os.path.dirname(d)
        if parent == d:
            return None
        d = parent
    return None


def resolve_out_root(cfg_path, cfg_src, out_dir_arg):
    """按配置来源决定输出根：--out-dir 显式 > 显式配置(下载目录) > 项目级(项目路径) > 全局(~/.claude)。
    与 log-diagnose 保持一致，避免生产查询结果落在 skill 目录内造成扩散。"""
    if out_dir_arg:
        return os.path.abspath(out_dir_arg)
    if cfg_src == "explicit":
        return os.path.join(os.path.expanduser("~"), "Downloads")
    if cfg_src == "project":
        proj_root = os.path.dirname(os.path.dirname(os.path.abspath(cfg_path)))
        return os.path.join(proj_root, ".tasks", "db-query")
    return GLOBAL_OUT_DIR


def die(msg, code=1):
    print("ERROR: " + msg, file=sys.stderr)
    sys.exit(code)


def load_config(config_path):
    if not os.path.exists(config_path):
        die("配置文件不存在: %s\n请创建它，schema:\n%s" % (
            config_path, json.dumps({
                "default_env": "test",
                "environments": {
                    "test": {
                        "name": "测试环境",
                        "hosts": ["<ip>"], "port": 8000,
                        "database": "<database>", "schema": "<schema>",
                        "username": "<user>", "password": "...",
                        "read_only": False, "default_limit": 100, "statement_timeout": 60
                    },
                    "prod": {
                        "name": "生产环境",
                        "hosts": ["<ip>"], "port": 8000,
                        "database": "<database>", "schema": "<schema>",
                        "username": "<user_read_only>", "password": "...",
                        "read_only": True, "default_limit": 100, "statement_timeout": 60
                    }
                }
            }, indent=2, ensure_ascii=False)))
    with open(config_path, "r", encoding="utf-8-sig") as f:
        cfg = json.load(f)
    # 打印生效的配置来源，便于核对凭据来自哪个文件（配置可由工作目录向上查找得到）
    print("配置文件: %s" % os.path.abspath(config_path))
    return cfg


def list_environments(cfg):
    for key, env in cfg.get("environments", {}).items():
        hosts = env.get("hosts", [])
        print("%s\t%s\t%s@%s:%s/%s\tread_only=%s" % (
            key, env.get("name", ""), env.get("username", ""),
            ",".join(hosts), env.get("port", ""), env.get("database", ""),
            env.get("read_only", True)))
    print("默认环境: %s" % cfg.get("default_env", "prod"))


def resolve_env(cfg, env_name):
    envs = cfg.get("environments", {})
    if not envs:
        die("配置缺少 environments 段")
    if not env_name:
        env_name = cfg.get("default_env", "prod")
    if env_name not in envs:
        die("未知环境 '%s'，可用: %s" % (env_name, ", ".join(envs.keys())))
    return dict(envs[env_name]), env_name


# ---- SQL 安全判定 ----

# 只读语句白名单。EXPLAIN 前缀与 WITH 开头的 CTE 单独判定。
# 注意: 本文件与 db_common.py 各有一份同名判定（db-query.py 自包含），
# 修改安全判定时两处必须同步，且只能收紧、不得放宽。
_READ_ONLY_HEAD_RE = re.compile(
    r"^\s*(?:SELECT|SHOW|DESCRIBE|VALUES|TABLE)\b", re.IGNORECASE)
_WITH_HEAD_RE = re.compile(r"^\s*WITH\b", re.IGNORECASE)
# 写操作关键字（用于判定 WITH 内嵌写 / 报错文案加固）
_WRITE_KW_RE = re.compile(
    r"\b(?:INSERT|UPDATE|DELETE|MERGE|UPSERT|CREATE|ALTER|DROP|TRUNCATE|"
    r"GRANT|REVOKE|COMMENT|CALL|VACUUM|REINDEX|REFRESH|RENAME|COPY|MOVE)\b",
    re.IGNORECASE)
# EXPLAIN 前缀：(ANALYZE, BUFFERS) 选项与 ANALYZE|VERBOSE 关键字剥掉后，
# 按被解释的语句本身判定——EXPLAIN ANALYZE 会真实执行该语句。
_EXPLAIN_HEAD_RE = re.compile(r"^\s*EXPLAIN\b(.*)$", re.IGNORECASE | re.S)
_EXPLAIN_OPTS_RE = re.compile(r"^\s*\((?:[^()]|\([^()]*\))*\)\s*")
_EXPLAIN_KW_RE = re.compile(r"^(?:ANALYZE|ANALYSE|VERBOSE)\b\s*", re.IGNORECASE)
# 只读关键字开头、但带写或敏感副作用的形态，一律按写处理：
#   SELECT ... INTO <table>（建表）、nextval/setval（推进序列）、
#   pg_terminate_backend 等后端管理函数、lo_import/lo_unlink/lo_put（大对象）、
#   dblink_exec（远端执行）、pg_read_file 等（读服务器文件）、
#   FOR UPDATE / FOR SHARE 系列（行锁）
_SIDE_EFFECT_RE = re.compile(
    r"\bINTO\b|\b(?:nextval|setval)\s*\(|pg_terminate_backend|pg_cancel_backend|"
    r"pg_reload_conf|pg_rotate_logfile|pg_switch_wal|pg_create_restore_point|"
    r"pg_stat_reset|lo_import|lo_unlink|lo_put|dblink_exec|"
    r"pg_read_file|pg_read_binary_file|pg_ls_dir|"
    r"\bFOR\s+(?:NO\s+KEY\s+|KEY\s+)?(?:UPDATE|SHARE)\b",
    re.IGNORECASE)


def strip_comments(sql):
    """去除 -- 行注释与 /* */ 块注释，便于语句判定（不处理引号内文本，够用）。"""
    sql = re.sub(r"/\*.*?\*/", " ", sql, flags=re.S)
    sql = re.sub(r"--[^\r\n]*", " ", sql)
    return sql


def is_read_only(sql):
    """去掉注释后判定语句是否只读。

    安全要点（只收紧、不放宽）：
    - EXPLAIN 前缀先剥掉再判定被解释语句——EXPLAIN ANALYZE 会真实执行该语句，
      故 EXPLAIN ANALYZE <写语句> 必须按写处理；
    - 只读关键字开头但带副作用的形态（SELECT ... INTO 建表、nextval/setval、
      pg_terminate_backend、lo_import、dblink_exec 等）一律按写处理。
    """
    head = strip_comments(sql).strip()
    # 剥 EXPLAIN 前缀（含嵌套），上限 4 层防构造性死循环
    for _ in range(4):
        m = _EXPLAIN_HEAD_RE.match(head)
        if not m:
            break
        inner = _EXPLAIN_OPTS_RE.sub("", m.group(1), count=1).strip()
        while True:
            m2 = _EXPLAIN_KW_RE.match(inner)
            if not m2:
                break
            inner = inner[m2.end():].strip()
        if not inner:
            return False  # 只有 EXPLAIN 而无被解释语句：非法，按写处理
        head = inner
    if _READ_ONLY_HEAD_RE.match(head):
        return not _SIDE_EFFECT_RE.search(head)
    if _WITH_HEAD_RE.match(head):
        return not _WRITE_KW_RE.search(head)
    return False


def enforce_write_policy(sql, env_cfg, env_name, allow_write):
    """写策略：生产（read_only）一律拒绝；测试默认拒绝，--allow-write 才放行。"""
    sql = strip_comments(sql).strip().rstrip(";").strip()
    if not sql:
        die("SQL 为空")
    if ";" in sql:
        die("只允许单条 SQL；请勿使用分号拼接多条语句")
    if is_read_only(sql):
        return sql
    if env_cfg.get("read_only"):
        die("环境 '%s'(%s) 为只读，拒绝执行非只读语句。\n"
            "如需修复数据请切换到测试环境（--env test）并获用户确认后加 --allow-write。" %
            (env_name, env_cfg.get("name", "")))
    if not allow_write:
        die("检测到写语句（非 SELECT）。测试环境写操作须先获得用户确认，"
            "确认后加 --allow-write 重新执行。\n语句头部: %s" % sql[:120])
    if not _WRITE_KW_RE.search(sql) and not re.match(r"^\s*(SET|BEGIN|COMMIT|ROLLBACK|RESET)\b", sql, re.I):
        die("无法识别的写语句，已拒绝: %s" % sql[:120])
    print("!! 写模式: 环境 %s(%s)，语句将直接提交（autocommit）" %
          (env_name, env_cfg.get("name", "")))
    return sql


def connect(env_cfg, env_name):
    """依次尝试 hosts 建连，返回 (conn, 描述串)。"""
    try:
        import psycopg2
    except ImportError:
        die("缺少 psycopg2，请先安装: pip install psycopg2-binary")
    hosts = env_cfg.get("hosts") or []
    if not hosts:
        die("环境 '%s' 未配置 hosts" % env_name)
    kwargs = {
        "port": env_cfg.get("port", 8000),
        "dbname": env_cfg.get("database", ""),
        "user": env_cfg.get("username", ""),
        "password": env_cfg.get("password", ""),
        "connect_timeout": 10,
    }
    schema = env_cfg.get("schema")
    if schema:
        # schema 会拼进 libpq 的 options 参数，必须是纯标识符（防注入 -c 选项）
        if not re.match(r"^[A-Za-z_][A-Za-z0-9_$]*$", str(schema)):
            die("配置的 schema 非法（只允许字母/数字/下划线/$，且不以数字开头）: %r" % schema)
        kwargs["options"] = "-c search_path=%s" % schema
    last_err = None
    for host in hosts:
        try:
            kwargs["host"] = host
            conn = psycopg2.connect(**kwargs)
            conn.autocommit = True
            if env_cfg.get("read_only"):
                try:
                    # 会话级只读双保险（只读账号本身已无写权限，失败不阻断）
                    conn.set_session(readonly=True)
                except Exception:
                    pass
            desc = "%s@%s:%s/%s (schema=%s, read_only=%s)" % (
                kwargs["user"], host, kwargs["port"], kwargs["dbname"],
                schema or "-", bool(env_cfg.get("read_only")))
            print("已连接: " + desc)
            return conn, desc
        except Exception as e:
            last_err = e
            continue
    die("无法连接环境 '%s' 的任一主机（%s），最后错误: %s" %
        (env_name, ",".join(hosts), last_err))


def slugify(text):
    s = re.sub(r'[\\/:*?"<>|\s]+', "_", text)
    return s[:60].rstrip("._") or "query"


def cell(v):
    if v is None:
        return "NULL"
    s = str(v)
    return s.replace("\r", "\\r").replace("\n", "\\n").replace("\t", "\\t")


def write_outputs(outdir, name, sql, cols, rows, truncated, desc):
    os.makedirs(outdir, exist_ok=True)
    txt_path = os.path.join(outdir, name + ".txt")
    json_path = os.path.join(outdir, name + ".json")

    lines = []
    lines.append("conn=%s" % desc)
    lines.append("sql=%s" % sql.replace("\n", " ")[:1000])
    lines.append("cols=%d  rows=%d%s" % (
        len(cols), len(rows),
        "  WARNING: 结果超过 limit 已截断" if truncated else ""))
    lines.append("")
    lines.append(" | ".join(cols))
    lines.append("-" * 60)
    for r in rows:
        lines.append(" | ".join(cell(v) for v in r))
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    data = [dict(zip(cols, [None if v is None else str(v) for v in r])) for r in rows]
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    return txt_path, json_path


def main():
    ap = argparse.ArgumentParser(description="数据库查询取数（只读优先，写操作需确认）。")
    ap.add_argument("--env", default=None, help="环境名 test/prod，缺省走配置 default_env")
    ap.add_argument("--list-envs", action="store_true", help="列出可用环境后退出")
    ap.add_argument("--connect", action="store_true", help="仅测试连通性（不执行 SQL）")
    ap.add_argument("--sql", default=None, help="待执行 SQL")
    ap.add_argument("--sql-file", default=None, help="从文件读取 SQL")
    ap.add_argument("--limit", type=int, default=None, help="返回行数上限（缺省走配置 default_limit）")
    ap.add_argument("--allow-write", action="store_true",
                    help="测试环境显式允许写语句（须先获得用户确认；生产环境忽略并拒绝）")
    ap.add_argument("--json", action="store_true", help="额外以 JSON 打印结果到 stdout")
    ap.add_argument("--config", default=None,
                    help="配置文件路径；缺省按优先级查找: 项目级 .claude/%s（当前目录向上）→ skill 同级默认" % CONFIG_FILENAME)
    ap.add_argument("--out-dir", default=None,
                    help="输出根目录；缺省按配置来源: 显式 --config→下载目录, 项目级配置→项目路径, 全局默认→~/.claude")
    args = ap.parse_args()

    proj_cfg = find_project_config()
    cfg_path = args.config or proj_cfg or DEFAULT_CONFIG
    cfg_src = "explicit" if args.config else ("project" if proj_cfg else "default")
    cfg = load_config(cfg_path)
    if args.list_envs:
        list_environments(cfg)
        return

    env_cfg, env_name = resolve_env(cfg, args.env)

    if args.connect:
        conn, desc = connect(env_cfg, env_name)
        cur = conn.cursor()
        cur.execute("SELECT version()")
        print("版本: %s" % cur.fetchone()[0])
        return

    sql = None
    if args.sql_file:
        with open(args.sql_file, "r", encoding="utf-8-sig") as f:
            sql = f.read()
    elif args.sql:
        sql = args.sql
    if not sql:
        ap.error("必须指定 --sql '...' 或 --sql-file")

    sql = enforce_write_policy(sql, env_cfg, env_name, args.allow_write)
    limit = args.limit or env_cfg.get("default_limit", 100)

    conn, desc = connect(env_cfg, env_name)
    cur = conn.cursor()
    t0 = time.time()
    try:
        cur.execute(sql)
    except Exception as e:
        try:
            conn.rollback()
        except Exception:
            pass
        die("执行失败: %s" % e)
    elapsed = time.time() - t0

    if cur.description is None:
        # DML/DDL：无结果集
        print("执行完成: 影响行数=%s  耗时 %.2fs" % (cur.rowcount, elapsed))
        return

    cols = [d[0] for d in cur.description]
    rows = cur.fetchmany(limit + 1)
    truncated = len(rows) > limit
    rows = rows[:limit]

    name = time.strftime("%Y%m%d-%H%M%S") + "-" + slugify(sql)
    outdir = os.path.join(resolve_out_root(cfg_path, cfg_src, args.out_dir), env_name)
    txt_path, json_path = write_outputs(outdir, name, sql, cols, rows, truncated, desc)

    print("环境: %s  返回: %d 行 x %d 列  耗时 %.2fs%s" % (
        env_name, len(rows), len(cols), elapsed,
        "  (超过 limit=%d 已截断)" % limit if truncated else ""))
    print("列: %s" % " | ".join(cols))
    for r in rows[:20]:
        print("  " + " | ".join(cell(v) for v in r))
    if len(rows) > 20:
        print("  ... 其余 %d 行见输出文件" % (len(rows) - 20))
    if args.json:
        print(json.dumps(
            [dict(zip(cols, [None if v is None else str(v) for v in r])) for r in rows],
            ensure_ascii=False))
    print("     txt:  %s" % txt_path)
    print("     json: %s" % json_path)


if __name__ == "__main__":
    main()
