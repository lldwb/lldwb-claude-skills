#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
lldwb-claude-skills 安装脚本：按 config.json 中 enabled=true 的技能，
将 skills/<技能名>/ 复制到 Claude Code 用户级 skills 目录（~/.claude/skills/）。

用法:
    python install.py                  # 安装 config.json 中启用的全部技能
    python install.py fix-bug          # 仅安装指定技能
    python install.py --list           # 列出可用技能与启用状态
    python install.py --dry-run        # 只打印将执行的复制，不实际安装
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

ROOT = os.path.dirname(os.path.abspath(__file__))
SKILLS_DIR = os.path.join(ROOT, "skills")
CONFIG_PATH = os.path.join(ROOT, "config.json")
HOME = os.path.expanduser("~")
TARGET_DIR = os.path.join(HOME, ".claude", "skills")


def die(msg, code=1):
    print("ERROR: " + msg, file=sys.stderr)
    sys.exit(code)


def load_skills():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        skills = cfg.get("skills", {})
    else:
        skills = {}
    # 以磁盘上实际存在的技能目录为准补全（config.json 未列出的默认启用）
    if os.path.isdir(SKILLS_DIR):
        for name in sorted(os.listdir(SKILLS_DIR)):
            if os.path.isdir(os.path.join(SKILLS_DIR, name)):
                skills.setdefault(name, {"enabled": True})
    return skills


def main():
    ap = argparse.ArgumentParser(description="安装 skills 到 ~/.claude/skills/")
    ap.add_argument("names", nargs="*", help="指定技能名（缺省安装 config.json 中启用的全部）")
    ap.add_argument("--list", action="store_true", help="列出可用技能与启用状态")
    ap.add_argument("--dry-run", action="store_true", help="只打印将执行的复制，不实际安装")
    args = ap.parse_args()

    skills = load_skills()
    if args.list:
        for name in sorted(skills):
            print("%s\t%s" % (name, "enabled" if skills[name].get("enabled", True) else "disabled"))
        return

    if args.names:
        todo = [(n, skills.get(n, {})) for n in args.names]
        for n, _ in todo:
            if not os.path.isdir(os.path.join(SKILLS_DIR, n)):
                die("技能 '%s' 不存在于 %s" % (n, SKILLS_DIR))
    else:
        todo = [(n, s) for n, s in sorted(skills.items()) if s.get("enabled", True)]

    if not todo:
        die("没有可安装的技能（config.json 中全部 disabled）")
    if not args.dry_run:
        os.makedirs(TARGET_DIR, exist_ok=True)

    for name, _ in todo:
        src = os.path.join(SKILLS_DIR, name)
        dst = os.path.join(TARGET_DIR, name)
        print("%s -> %s" % (src, dst))
        if not args.dry_run:
            if os.path.exists(dst):
                shutil.rmtree(dst)
            shutil.copytree(src, dst)

    if args.dry_run:
        print("(--dry-run: 未实际安装)")
    else:
        print("已安装 %d 个技能到 %s" % (len(todo), TARGET_DIR))
        print("提示: 重新安装会覆盖同名技能目录；卸载用 uninstall.py")


if __name__ == "__main__":
    main()
