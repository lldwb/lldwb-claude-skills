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


def safe_skill_dir(base_dir, name):
    """把技能名解析为 base_dir 下的直接子目录路径。
    技能名来自命令行，必须校验：os.path.join 遇绝对路径会直接丢弃 base_dir，
    不校验时后续 rmtree / copytree 可能落到技能目录之外的任意路径。"""
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
            if not os.path.isdir(safe_skill_dir(SKILLS_DIR, n)):
                die("技能 '%s' 不存在于 %s" % (n, SKILLS_DIR))
    else:
        # 无参安装必须以 config.json 的启用清单为准：缺配置时报错，
        # 不兜底安装全部技能（避免 clone 后未建配置导致全量安装）
        if not os.path.exists(CONFIG_PATH):
            die("未找到 %s，无法确定启用清单。\n"
                "请按 README 的目录结构创建 config.json，"
                "或显式指定技能名: python install.py <技能名> [<技能名> ...]" % CONFIG_PATH)
        todo = [(n, s) for n, s in sorted(skills.items()) if s.get("enabled", True)]

    if not todo:
        die("没有可安装的技能（config.json 中全部 disabled）")
    if not args.dry_run:
        os.makedirs(TARGET_DIR, exist_ok=True)

    for name, _ in todo:
        src = safe_skill_dir(SKILLS_DIR, name)
        dst = safe_skill_dir(TARGET_DIR, name)
        print("%s -> %s" % (src, dst))
        if not args.dry_run:
            if os.path.exists(dst):
                shutil.rmtree(dst)
            # 跳过本地产物，避免把 .tasks 里的查询结果/任务产物带到安装目录
            shutil.copytree(src, dst, ignore=shutil.ignore_patterns(
                ".tasks", "__pycache__", "*.pyc", "*.pyo"))

    if args.dry_run:
        print("(--dry-run: 未实际安装)")
    else:
        print("已安装 %d 个技能到 %s" % (len(todo), TARGET_DIR))
        print("提示: 重新安装会覆盖同名技能目录；卸载用 uninstall.py")


if __name__ == "__main__":
    main()
