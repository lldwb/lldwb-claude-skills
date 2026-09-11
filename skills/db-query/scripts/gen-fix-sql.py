#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把 db-query 查询结果文件转换为批量 UPDATE 修复 SQL 脚本（flyway/fixdata 风格）。

适用场景:
    db-query.py 查出“每行要改成什么值”（如 id | 新编码），本脚本将其转换为
    CREATE TABLE bak... AS + begin + update ... where id=... + commit 的
    标准修复脚本，可直接放入项目 fixdata 目录或交给 run-sql-file.py 试跑。

输入（--result，两种格式均可）:
    txt : db-query 落盘的表格文本（自动跳过 conn=/sql=/cols= 头、列头、分隔线）
    json: db-query 落盘的行数据数组（取每行 --id-col 与 --set-col 列）

用法:
    python gen-fix-sql.py --result .tasks/db-query/prod/20260911-144129-xxx.txt \
        --table <表名> --set-col <要更新的列> \
        --filter "<条件>" \
        [--id-col id] [--id-re 正则] [--bak-suffix 20260911] [--out fix.sql]

输出（缺省 --out 时写到结果文件同目录 fix_<table>_<bak-suffix>.sql）:
    CREATE TABLE bak_<bak-suffix>_<table> AS SELECT * FROM <table> WHERE <filter>;
    begin;
    update <table> set <set-col> = '<value>' where <id-col> = '<id>' and <filter>;
    ...
    commit;

安全:
    - 仅生成 SQL 文本，不连接数据库、不执行任何语句
    - 表名/列名/备份表后缀必须是合法标识符；id 必须匹配 --id-re（json 与 txt 输入一致）
    - id 与值统一按标准 SQL 转义（单引号翻倍），并显式 SET standard_conforming_strings = on
    - id 重复、值为空、id 不匹配 --id-re 等情况直接报错中止，不静默生成
"""
import sys
import os
import re
import json
import time
import argparse

import db_common
from db_common import die, check_ident

_DEFAULT_ID_RE = r"^[0-9a-fA-F]{32}$|^[0-9]+$"


def read_rows_json(path, id_col, set_col, id_re):
    """读 JSON 结果。id 必须匹配 --id-re——与 txt 路径同样校验，
    防止异常 id 值被拼接进生成的 SQL。"""
    pat = re.compile(id_re)
    with open(path, "r", encoding="utf-8-sig") as f:
        data = json.load(f)
    if not isinstance(data, list):
        die("JSON 结果格式不符: 应为行对象数组")
    rows = []
    for i, rec in enumerate(data):
        if id_col not in rec:
            die("第 %d 行缺少 id 列 '%s'" % (i + 1, id_col))
        if set_col not in rec:
            die("第 %d 行缺少值列 '%s'" % (i + 1, set_col))
        rid = str(rec[id_col]).strip()
        val = str(rec[set_col]).strip()
        if not rid or val.lower() == "none" and rec[set_col] is None:
            die("第 %d 行 id 为空" % (i + 1))
        if not pat.match(rid):
            die("第 %d 行 id 不匹配 --id-re（%s）: %r\n"
                "如 id 形态特殊，请按实际形态调整 --id-re 后重试" % (i + 1, id_re, rid[:60]))
        rows.append((rid, val))
    return rows


def read_rows_txt(path, id_col, set_col, id_re):
    pat = re.compile(id_re)
    rows = []
    with open(path, "r", encoding="utf-8-sig") as f:
        for lineno, line in enumerate(f, 1):
            line = line.rstrip("\r\n")
            if not line.strip():
                continue
            if line.startswith(("conn=", "sql=", "cols=")):
                continue
            if re.match(r"^\s*-+\s*$", line):
                continue
            parts = [p.strip() for p in line.split("|")]
            if len(parts) != 2:
                continue
            rid, val = parts
            if not pat.match(rid):
                continue
            if not val or val == "NULL":
                die("行 %d: id=%s 的值为空/NULL，请检查结果后重新生成" % (lineno, rid))
            rows.append((rid, val))
    return rows


def main():
    ap = argparse.ArgumentParser(
        description="把 db-query 查询结果文件转换为批量 UPDATE 修复 SQL 脚本（不连库、不执行）")
    ap.add_argument("--result", required=True, help="db-query 结果文件（.txt 或 .json）")
    ap.add_argument("--table", required=True, help="目标表名")
    ap.add_argument("--set-col", required=True, help="要更新的列名")
    ap.add_argument("--filter", required=True, help="过滤条件（用于备份表与 update 的 where），如 project_id='xxx'")
    ap.add_argument("--id-col", default="id", help="id 列名（json 输入用；txt 输入取每行首段）")
    ap.add_argument("--id-re", default=_DEFAULT_ID_RE,
                    help="id 的匹配正则（默认 UUID 或纯数字）；txt 与 json 输入均校验，"
                         "防止列头等行被当数据、也防止异常 id 值被拼进 SQL")
    ap.add_argument("--bak-suffix", default=time.strftime("%Y%m%d"),
                    help="备份表名后缀，默认今天 yyyyMMdd")
    ap.add_argument("--out", default=None, help="输出 SQL 路径（缺省: 结果文件同目录 fix_<table>_<suffix>.sql）")
    args = ap.parse_args()

    if not os.path.exists(args.result):
        die("结果文件不存在: %s" % args.result)
    if ";" in args.filter:
        die("过滤条件中不允许出现分号")
    # 拼进 SQL 的标识符先校验（表名/列名独立出现；备份表后缀嵌在 bak_<后缀>_<表> 中间）
    check_ident(args.table, "--table")
    check_ident(args.set_col, "--set-col")
    check_ident(args.id_col, "--id-col")
    check_ident(args.bak_suffix, "--bak-suffix", allow_leading_digit=True)

    ext = os.path.splitext(args.result)[1].lower()
    if ext == ".json":
        rows = read_rows_json(args.result, args.id_col, args.set_col, args.id_re)
    else:
        rows = read_rows_txt(args.result, args.id_col, args.set_col, args.id_re)
    if not rows:
        has_data = any(
            line.strip() and not line.startswith(("conn=", "sql=", "cols="))
            and not re.match(r"^\s*-+\s*$", line)
            and len([p.strip() for p in line.split("|")]) == 2
            for line in open(args.result, "r", encoding="utf-8-sig"))
        if has_data:
            die("结果文件中有数据行，但 id 均不匹配当前 --id-re（%s），"
                "请按实际 id 形态调整 --id-re" % args.id_re)
        die("未从结果文件中解析到任何 (id, 值) 行，请检查 --result")

    ids = [r[0] for r in rows]
    if len(set(ids)) != len(ids):
        dup = sorted({i for i in ids if ids.count(i) > 1})
        die("id 存在重复: %s（共 %d 行）" % (", ".join(dup[:10]), len(ids)))
    vals = [r[1] for r in rows]
    if len(set(vals)) != len(vals):
        dup = sorted({v for v in vals if vals.count(v) > 1})
        die("值存在重复: %s（共 %d 行）。如确需重复值请手工拆分脚本" % (", ".join(dup[:10]), len(vals)))

    out = args.out or os.path.join(os.path.dirname(os.path.abspath(args.result)),
                                   "fix_%s_%s.sql" % (args.table, args.bak_suffix))

    lines = ["-- 由 gen-fix-sql.py 生成: %s 行 update（%s.%s <- %s）" % (
        len(rows), args.table, args.set_col, os.path.basename(args.result))]
    lines.append("-- id 与值均按标准 SQL 转义（单引号翻倍）；显式声明字符串模式以保证确定性")
    lines.append("SET standard_conforming_strings = on;")
    lines.append("")
    lines.append("CREATE TABLE bak_%s_%s AS" % (args.bak_suffix, args.table))
    lines.append("SELECT * FROM %s WHERE %s;" % (args.table, args.filter))
    lines.append("")
    lines.append("begin;")
    for rid, val in rows:
        esc_val = val.replace("'", "''")
        esc_rid = rid.replace("'", "''")
        lines.append("update %s set %s = '%s' where %s = '%s' and %s;" % (
            args.table, args.set_col, esc_val, args.id_col, esc_rid, args.filter))
    lines.append("commit;")

    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("已生成: %s" % out)
    print("共 %d 条 update，备份表 bak_%s_%s" % (len(rows), args.bak_suffix, args.table))


if __name__ == "__main__":
    main()
