#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
db-query 技能配套脚本公共模块：配置加载、环境解析、建连、SQL 读写判定。
仅被同目录脚本 import，不直接运行。
"""
import sys
import os
import json
import re
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
CONFIG_FILENAME = "db-query.config.json"

# 只读语句白名单。WITH 开头的 CTE 单独判断是否内嵌写操作。
_READ_ONLY_HEAD_RE = re.compile(
    r"^\s*(?:SELECT|SHOW|EXPLAIN|DESCRIBE|VALUES|TABLE)\b", re.IGNORECASE)
_WITH_HEAD_RE = re.compile(r"^\s*WITH\b", re.IGNORECASE)
# 写操作关键字（用于判定 WITH 内嵌写 / 报错文案加固）
_WRITE_KW_RE = re.compile(
    r"\b(?:INSERT|UPDATE|DELETE|MERGE|UPSERT|CREATE|ALTER|DROP|TRUNCATE|"
    r"GRANT|REVOKE|COMMENT|CALL|VACUUM|REINDEX|REFRESH|RENAME|COPY|MOVE)\b",
    re.IGNORECASE)
# 会话级语句：不写数据、不改表结构，生产/测试均放行
_SESSION_HEAD_RE = re.compile(r"^\s*(?:SET|BEGIN|COMMIT|ROLLBACK|RESET)\b", re.IGNORECASE)


def die(msg, code=1):
    print("ERROR: " + msg, file=sys.stderr)
    sys.exit(code)


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
        return json.load(f)


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


def connect(env_cfg, env_name, force_readonly=False):
    """依次尝试 hosts 建连，返回 (conn, 描述串)。
    force_readonly=True 时强制会话只读（用于“源只导出”的同步场景，
    即使源环境配置为可写也不允许在源上做任何写操作）。"""
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
        kwargs["options"] = "-c search_path=%s" % schema
    readonly = force_readonly or bool(env_cfg.get("read_only"))
    last_err = None
    for host in hosts:
        try:
            kwargs["host"] = host
            conn = psycopg2.connect(**kwargs)
            conn.autocommit = True
            if readonly:
                try:
                    # 会话级只读双保险（只读账号本身已无写权限，失败不阻断）
                    conn.set_session(readonly=True)
                except Exception:
                    pass
            desc = "%s@%s:%s/%s (schema=%s, read_only=%s)" % (
                kwargs["user"], host, kwargs["port"], kwargs["dbname"],
                schema or "-", readonly)
            print("已连接: " + desc)
            return conn, desc
        except Exception as e:
            last_err = e
            continue
    die("无法连接环境 '%s' 的任一主机（%s），最后错误: %s" %
        (env_name, ",".join(hosts), last_err))


def strip_comments(sql):
    """去除 -- 行注释与 /* */ 块注释，便于语句判定（不处理引号内文本，够用）。"""
    sql = re.sub(r"/\*.*?\*/", " ", sql, flags=re.S)
    sql = re.sub(r"--[^\r\n]*", " ", sql)
    return sql


def is_read_only(sql):
    """去掉注释后判定：仅 SELECT/SHOW/EXPLAIN/... 及不含写关键字的 WITH 为只读。"""
    head = strip_comments(sql).strip()
    if _READ_ONLY_HEAD_RE.match(head):
        return True
    if _WITH_HEAD_RE.match(head):
        return not _WRITE_KW_RE.search(head)
    return False


def is_session_stmt(sql):
    """会话级语句（SET/BEGIN/COMMIT/ROLLBACK/RESET）：不写数据，不做写拦截。"""
    return bool(_SESSION_HEAD_RE.match(strip_comments(sql).strip()))


def check_write_allowed(stmt, env_cfg, env_name, allow_write):
    """写策略判定（供逐条执行类工具复用）：
    生产（read_only）一律拒绝；测试默认拒绝，--allow-write 才放行。
    返回规范化后的语句；非法则 die。"""
    stmt = strip_comments(stmt).strip().rstrip(";").strip()
    if not stmt:
        die("SQL 为空")
    if ";" in stmt:
        die("只允许单条 SQL；请勿使用分号拼接多条语句")
    if is_read_only(stmt) or is_session_stmt(stmt):
        return stmt
    if env_cfg.get("read_only"):
        die("环境 '%s'(%s) 为只读，拒绝执行非只读语句。\n"
            "如需修复数据请切换到测试环境（--env test）并获用户确认后加 --allow-write。" %
            (env_name, env_cfg.get("name", "")))
    if not allow_write:
        die("检测到写语句（非 SELECT）。测试环境写操作须先获得用户确认，"
            "确认后加 --allow-write 重新执行。\n语句头部: %s" % stmt[:120])
    if not _WRITE_KW_RE.search(stmt):
        die("无法识别的写语句，已拒绝: %s" % stmt[:120])
    print("!! 写模式: 环境 %s(%s)" % (env_name, env_cfg.get("name", "")))
    return stmt


def default_config_for_die():
    return DEFAULT_CONFIG
