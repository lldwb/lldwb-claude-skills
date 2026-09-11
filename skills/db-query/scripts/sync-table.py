#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把源环境表数据同步到目标环境（典型: 生产数据同步到测试复现/验证）。

行为:
    1. 源（--from）: 查 information_schema 取列清单，按列名 SELECT 导出
       --where 范围内的行（源连接强制只读会话）
    2. 目标（--to）: 校验列清单与源完全一致 → 按 --where 清理目标行 → 批量插入
    3. 事务: 全部成功 commit，任一失败回滚（目标不残留半截数据）

用法:
    python sync-table.py --table <表名> --from prod --to test \
        --where "<条件>" [--allow-write]

安全:
    - --table 必须是合法标识符；--where 必填且禁止分号，杜绝无条件全表同步/拼接
    - 源连接强制会话只读，即使源环境配置为可写也不允许写源
    - 目标为只读环境（如 prod）一律拒绝；测试环境默认拦截，须 --allow-write
      （agent 须先向用户说明将清理/插入哪些行，获确认后再执行）
"""
import sys
import argparse

import db_common
from db_common import (die, load_config, find_project_config, resolve_env,
                       connect, check_write_allowed, check_ident)


def get_columns(conn, schema, table):
    cur = conn.cursor()
    cur.execute("""
        SELECT column_name FROM information_schema.columns
        WHERE table_schema = %s AND table_name = %s
        ORDER BY ordinal_position
    """, (schema, table))
    cols = [r[0] for r in cur.fetchall()]
    cur.close()
    return cols


def main():
    ap = argparse.ArgumentParser(description="把源环境表数据同步到目标环境（源只读，目标写需确认）")
    ap.add_argument("--table", required=True, help="表名")
    ap.add_argument("--from", dest="from_env", required=True, help="源环境名（只读导出）")
    ap.add_argument("--to", dest="to_env", required=True, help="目标环境名（清理+插入）")
    ap.add_argument("--where", required=True, help="过滤条件（导出与清理共用），如 project_id='xxx'")
    ap.add_argument("--allow-write", action="store_true",
                    help="目标环境显式允许写（须先获得用户确认；目标为只读环境仍拒绝）")
    ap.add_argument("--config", default=None, help="配置文件路径；缺省按 db-query 查找顺序")
    args = ap.parse_args()

    if ";" in args.where:
        die("--where 中不允许出现分号")
    # 表名会直接拼进源/目标两侧的 SQL，必须是合法标识符（--where 的分号拦截挡不住表名）
    check_ident(args.table, "--table")
    if args.from_env == args.to_env:
        die("源环境与目标环境不能相同: %s" % args.from_env)

    cfg = load_config(args.config or find_project_config() or db_common.DEFAULT_CONFIG)
    src_cfg, src_name = resolve_env(cfg, args.from_env)
    dst_cfg, dst_name = resolve_env(cfg, args.to_env)
    if dst_cfg.get("read_only"):
        die("目标环境 '%s'(%s) 为只读，拒绝写入。" % (dst_name, dst_cfg.get("name", "")))
    if not args.allow_write:
        die("目标环境写操作（清理 %s 范围行 + 插入）须先获得用户确认，"
            "确认后加 --allow-write 重新执行。" % args.where)

    src_conn, src_desc = connect(src_cfg, src_name, force_readonly=True)
    dst_conn, dst_desc = connect(dst_cfg, dst_name)
    try:
        src_cols = get_columns(src_conn, src_cfg.get("schema") or "", args.table)
        dst_cols = get_columns(dst_conn, dst_cfg.get("schema") or "", args.table)
        if src_cols != dst_cols:
            die("源/目标表结构不一致:\n  源(%s): %s\n  目标(%s): %s" % (
                src_name, ",".join(src_cols), dst_name, ",".join(dst_cols)))
        print("表结构一致（%d 列）" % len(src_cols))

        col_list = ",".join(src_cols)
        src_cur = src_conn.cursor()
        src_cur.execute("SELECT %s FROM %s WHERE %s" % (col_list, args.table, args.where))
        rows = src_cur.fetchall()
        print("源导出: %d 行" % len(rows))
        src_cur.close()

        dst_conn.autocommit = False
        dst_cur = dst_conn.cursor()
        try:
            dst_cur.execute("DELETE FROM %s WHERE %s" % (args.table, args.where))
            deleted = dst_cur.rowcount
            if rows:
                placeholders = ",".join(["%s"] * len(src_cols))
                dst_cur.executemany(
                    "INSERT INTO %s (%s) VALUES (%s)" % (args.table, col_list, placeholders),
                    rows)
            dst_conn.commit()
        except Exception as e:
            dst_conn.rollback()
            die("目标写入失败，已回滚（目标未残留半截数据）: %s" % e)
        finally:
            dst_cur.close()
        print("目标清理: %d 行，插入: %d 行" % (deleted, len(rows)))
        print("同步完成: %s → %s（表 %s）" % (src_name, dst_name, args.table))
    finally:
        src_conn.close()
        dst_conn.close()


if __name__ == "__main__":
    main()
