#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
lldwb-claude-skills 卸载脚本：删除 ~/.claude/skills/ 下已安装的技能目录。

删除前会先把目录备份到 ~/.claude/backup/lldwb-skills/<时间戳>/，
可用 `python install.py --restore <技能名>` 恢复。

用法:
    python uninstall.py bug-fix       # 卸载指定技能
    python uninstall.py --all         # 卸载本仓库安装的全部技能（按 config.json 技能清单）
"""
import sys
import os
import json
import time
import shutil
import argparse
import codecs

# Windows 控制台缺省 GBK，强制 UTF-8 输出（同仓库其他脚本的处理）。
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


def die(msg, code=1):
    print("ERROR: " + msg, file=sys.stderr)
    sys.exit(code)


ROOT = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(ROOT, "config.json")
HOME = os.path.expanduser("~")
TARGET_DIR = os.path.join(HOME, ".claude", "skills")

# 卸载前的备份与安装状态：与 install.py 用同一个目录 / 同一份状态文件。
# 备份与状态逻辑与 install.py 的同名函数保持一致——两处一起改。
BACKUP_ROOT = os.path.join(HOME, ".claude", "backup", "lldwb-skills")
STATE_PATH = os.path.join(BACKUP_ROOT, "state.json")
IGNORE_PATTERNS = (".tasks", "__pycache__", "*.pyc", "*.pyo")


def now_stamp():
    return time.strftime("%Y-%m-%d_%H%M%S")


def load_state():
    try:
        with open(STATE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            data.setdefault("skills", {})
            return data
    except Exception:
        pass
    return {"version": None, "installedAt": None, "skills": {}}


def save_state(state):
    os.makedirs(BACKUP_ROOT, exist_ok=True)
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
        f.write("\n")


def backup_skill(src_dir, stamp):
    """把将被删除的技能目录复制到 <BACKUP_ROOT>/<stamp>/<技能名>/，返回备份路径。"""
    dst = os.path.join(BACKUP_ROOT, stamp, os.path.basename(src_dir))
    if os.path.exists(dst):
        shutil.rmtree(dst)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copytree(src_dir, dst, ignore=shutil.ignore_patterns(*IGNORE_PATTERNS))
    return dst


def load_skill_names():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        return list(cfg.get("skills", {}).keys())
    return []


def safe_skill_dir(base_dir, name):
    """把技能名解析为 base_dir 下的直接子目录路径。
    技能名来自命令行，必须校验：os.path.join 遇绝对路径会直接丢弃 base_dir，
    不校验时后续 rmtree 可能删掉技能目录之外的任意目录。"""
    if not name or name in (".", ".."):
        die("非法技能名: %r" % name)
    if "\\" in name or "/" in name:
        die("非法技能名（不得包含路径分隔符）: %r" % name)
    if os.path.isabs(name) or os.path.splitdrive(name)[0]:
        die("非法技能名（不得为绝对路径或含盘符）: %r" % name)
    base = os.path.abspath(base_dir)
    target = os.path.abspath(os.path.join(base, name))
    if os.path.dirname(target) != base:
        die("技能名越出技能目录: %r" % name)
    return target


def main():
    ap = argparse.ArgumentParser(description="卸载 ~/.claude/skills/ 下的技能")
    ap.add_argument("names", nargs="*", help="技能名（至少一个，或 --all）")
    ap.add_argument("--all", action="store_true", help="卸载 config.json 中的全部技能")
    args = ap.parse_args()

    if args.all:
        names = load_skill_names()
    else:
        names = args.names
    if not names:
        ap.error("请指定技能名或用 --all")

    stamp = now_stamp()
    state = load_state()
    removed = []
    for name in names:
        dst = safe_skill_dir(TARGET_DIR, name)
        if os.path.isdir(dst):
            print("删除: %s" % dst)
            print("  备份 -> %s" % backup_skill(dst, stamp))
            shutil.rmtree(dst)
            removed.append(name)
            state["skills"].pop(name, None)
        else:
            print("未安装或已删除: %s" % dst)
    if removed:
        save_state(state)
    print("共卸载 %d 个" % len(removed))
    if removed:
        print("如需恢复: python install.py --restore <技能名>（备份保留在 %s）" % BACKUP_ROOT)


if __name__ == "__main__":
    main()
