#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
提交检查取数脚本（通用）。
只负责按修订号拉取提交元信息与 diff 并落盘，不做问题判定（判定由调用方 agent 完成）。

用法:
    python check-commit.py <修订号> [--max-diff-lines 500] [--out-dir .tasks/check-commit]

输出:
    <sha>.summary.txt   提交元信息 + 文件清单 + 截断后的 diff（截断时头部告警）
    <sha>.raw.diff      完整 diff（不截断）
stdout: 提交概要 + 输出路径
"""
import sys
import os
import argparse
import subprocess
import codecs

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_TASKS_DIR = os.path.join(SCRIPT_DIR, "..", ".tasks", "check-commit")

# Windows 控制台缺省 GBK，强制 UTF-8 输出中文。
# 提前规避乱码：stdout/stderr 可能被 GBK 控制台消费，或被 AI 以
# UTF-8 捕获（如 --resume 场景）；统一按 UTF-8 输出，两处均不乱码；
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

GIT = ["git", "-c", "core.quotepath=false"]


def die(msg, code=1):
    print("ERROR: " + msg, file=sys.stderr)
    sys.exit(code)


def git(*args):
    """执行 git 并返回 stdout，失败即退出。"""
    r = subprocess.run(GIT + list(args), capture_output=True,
                       encoding="utf-8", errors="replace")
    if r.returncode != 0:
        die("git %s 失败: %s" % (" ".join(args), r.stderr.strip()[:500]))
    return r.stdout


def git_ok(*args):
    """执行 git 不抛错，返回 (ok, stdout, stderr)。"""
    r = subprocess.run(GIT + list(args), capture_output=True,
                       encoding="utf-8", errors="replace")
    return r.returncode == 0, r.stdout, r.stderr


def write_outputs(out_dir, sha, subject, author, date, parents,
                  files, shortstat, file_list, diff_text, max_diff_lines):
    os.makedirs(out_dir, exist_ok=True)
    sum_path = os.path.join(out_dir, sha + ".summary.txt")
    raw_path = os.path.join(out_dir, sha + ".raw.diff")

    lines = []
    lines.append("sha=%s  subject=%s" % (sha, subject))
    lines.append("author=%s" % author)
    lines.append("date=%s" % date)
    lines.append("parents=%d (%s)" % (len(parents), " ".join(parents) or "-"))
    lines.append("files=%s  %s" % (files, shortstat or "(无增删)"))
    if not diff_text:
        lines.append("提示: 该提交无 diff（空提交或仅合并，见 raw.diff）。")
    lines.append("")
    lines.append("=== 提交信息 ===")
    body = git("show", "-s", "--format=%B", sha).strip()
    lines.append(body)
    lines.append("")
    lines.append("=== 文件清单 (状态 路径) ===")
    lines.extend(file_list)
    lines.append("")
    n_diff = diff_text.count("\n")
    truncated = n_diff > max_diff_lines
    lines.append("=== diff (%d 行%s) ===" % (
        n_diff, "，前 %d 行，完整见 raw.diff" % max_diff_lines if truncated else ""))
    if truncated:
        diff_show = "\n".join(diff_text.split("\n")[:max_diff_lines])
        lines.append(diff_show)
        lines.append("")
        lines.append("... (已截断 %d 行，完整内容见 %s)" % (n_diff - max_diff_lines, raw_path))
    else:
        lines.append(diff_text)

    with open(sum_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    with open(raw_path, "w", encoding="utf-8") as f:
        f.write(diff_text)
    return sum_path, raw_path, truncated, n_diff


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("revision", help="提交修订号（完整/短 sha、分支名、tag 等，与 git show 一致）")
    ap.add_argument("--max-diff-lines", type=int, default=500,
                    help="summary 中 diff 显示行数上限，默认 500；实际行数超出时截断并告警（raw.diff 始终完整）")
    ap.add_argument("--out-dir", default=DEFAULT_TASKS_DIR)
    args = ap.parse_args()

    ok, meta, err = git_ok("show", "-s", "--format=%H%x09%an%x09%aI%x09%P", args.revision)
    if not ok:
        die("修订号无效: %s\n%s" % (args.revision, err.strip()[:500]))
    sha, author, date, parents_str = meta.strip().split("\t")
    parents = [p for p in parents_str.split() if p]

    subject = git("show", "-s", "--format=%s", sha).strip()

    # merge 提交按第一父级展示改动（聚焦主分支合入内容）；非 merge 即普通 patch
    shortstat = git("show", "--first-parent", "--shortstat", "--format=", sha).strip()
    ns = git("show", "--first-parent", "--name-status", "--format=", sha)
    file_list = [ln.strip() for ln in ns.split("\n") if ln.strip()]
    files = len(file_list)

    diff_text = git("show", "--first-parent", "--format=", sha).strip()

    out_dir = os.path.abspath(args.out_dir)
    sum_path, raw_path, truncated, n_diff = write_outputs(
        out_dir, sha, subject, author, date, parents,
        files, shortstat, file_list, diff_text, args.max_diff_lines)

    print("OK  sha=%s" % sha)
    print("    subject: %s" % subject)
    print("    作者/时间: %s / %s" % (author, date))
    print("    文件: %d  %s" % (files, shortstat or "(无增删)"))
    print("    diff: %d 行%s" % (n_diff, "（summary 已截断，完整见 raw）" if truncated else ""))
    print("    summary:%s" % sum_path)
    print("    raw:    %s" % raw_path)


if __name__ == "__main__":
    main()
