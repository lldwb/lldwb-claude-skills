#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
lldwb-claude-skills 卸载脚本：删除 ~/.claude/skills/ 下已安装的技能目录。

用法:
    python uninstall.py fix-bug       # 卸载指定技能
    python uninstall.py --all         # 卸载本仓库安装的全部技能（按 config.json 技能清单）
"""
import sys
import os
import json
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

    removed = []
    for name in names:
        dst = safe_skill_dir(TARGET_DIR, name)
        if os.path.isdir(dst):
            print("删除: %s" % dst)
            shutil.rmtree(dst)
            removed.append(name)
        else:
            print("未安装或已删除: %s" % dst)
    print("共卸载 %d 个" % len(removed))


if __name__ == "__main__":
    main()
