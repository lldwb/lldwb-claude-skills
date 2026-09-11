#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
按分号切分执行 SQL 文件（flyway/fixdata 脚本试跑），逐条报告结果。

适用场景:
    修复脚本写好后先在测试环境试跑: 验证每条语句能否执行、
    统计 UPDATE/INSERT/DELETE 实际命中行数，失败即回滚整个文件。

用法:
    python run-sql-file.py --sql-file fix.sql [--env test] [--allow-write]

行为:
    - 读取文件，按分号切分（文件内字符串字面量请勿包含分号），逐条执行
    - 写策略与 db-query 一致: 生产（read_only）一律拒绝非只读语句；
      测试默认拒绝，须 --allow-write（agent 须先获用户确认）
    - SET/BEGIN/COMMIT/ROLLBACK/RESET 会话语句放行
    - 事务语义: 任一语句失败即回滚（模拟 Navicat 顺序执行），退出码 1；
      全部成功才 commit
    - 统计 UPDATE/INSERT/DELETE 命中行数（rowcount>0），--verbose 打印每条

注意:
    - 文件内不要写 BEGIN/COMMIT，事务由本脚本统一管理
    - 生产环境只读，本脚本在只读环境遇到非只读语句直接拒绝执行
"""
import sys
import os
import argparse

import db_common
from db_common import (die, load_config, find_project_config, resolve_env,
                       connect, check_write_allowed)

_DML_RE = __import__("re").compile(r"^\s*(?:UPDATE|INSERT|DELETE|MERGE)\b",
                                   __import__("re").IGNORECASE)


def split_statements(content):
    stmts = []
    for s in content.split(";"):
        s = s.strip()
        if s:
            stmts.append(s)
    return stmts


def main():
    ap = argparse.ArgumentParser(description="按分号切分执行 SQL 文件，逐条报告结果（写操作需确认）")
    ap.add_argument("--sql-file", required=True, help="SQL 文件路径")
    ap.add_argument("--env", default=None, help="环境名 test/prod，缺省走配置 default_env")
    ap.add_argument("--allow-write", action="store_true",
                    help="测试环境显式允许写语句（须先获得用户确认；生产环境忽略并拒绝）")
    ap.add_argument("--verbose", action="store_true", help="打印每条语句的执行结果")
    ap.add_argument("--config", default=None, help="配置文件路径；缺省按 db-query 查找顺序")
    args = ap.parse_args()

    if not os.path.exists(args.sql_file):
        die("SQL 文件不存在: %s" % args.sql_file)

    cfg = load_config(args.config or find_project_config() or db_common.DEFAULT_CONFIG)
    env_cfg, env_name = resolve_env(cfg, args.env)

    stmts = split_statements(open(args.sql_file, "r", encoding="utf-8-sig").read())
    if not stmts:
        die("文件中没有可执行的语句")
    print("语句总数: %d，环境: %s" % (len(stmts), env_name), flush=True)

    # 预检: 任一语句写策略不合法则整体拒绝，不连库
    checked = []
    for i, s in enumerate(stmts, 1):
        try:
            checked.append(check_write_allowed(s, env_cfg, env_name, args.allow_write))
        except SystemExit:
            print("（第 %d 条语句: %s）" % (i, s[:120]), file=sys.stderr)
            raise

    conn, desc = connect(env_cfg, env_name)
    conn.autocommit = False  # 事务: 全部成功才 commit
    cur = conn.cursor()
    ok = 0
    hits = []
    try:
        for i, s in enumerate(checked, 1):
            try:
                cur.execute(s)
            except Exception as e:
                conn.rollback()
                print("执行失败，已回滚: 第 %d 条\n%s\n错误: %s" % (i, s[:200], e),
                      file=sys.stderr)
                sys.exit(1)
            if _DML_RE.match(s):
                n = cur.rowcount
                if n is not None and n > 0:
                    hits.append(n)
            ok += 1
            if args.verbose:
                print("  第 %d 条 OK: %s" % (i, s[:100]))
        conn.commit()
    finally:
        cur.close()
        conn.close()

    print("全部 %d 条语句执行成功" % ok)
    print("命中（影响行数>0）的 DML 条数: %d，共影响行数: %d" % (len(hits), sum(hits)))


if __name__ == "__main__":
    main()
