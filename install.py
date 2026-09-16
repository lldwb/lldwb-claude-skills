#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
lldwb-claude-skills 安装脚本：按 config.json 中 enabled=true 的技能，
将 skills/<技能名>/ 复制到 Claude Code 用户级 skills 目录（~/.claude/skills/）。

覆盖同名技能前会把原目录备份到 ~/.claude/backup/lldwb-skills/<时间戳>/，
安装状态记在同目录的 state.json；误覆盖可用 --restore 回滚。

用法:
    python install.py                  # 安装 config.json 中启用的全部技能
    python install.py bug-fix          # 仅安装指定技能
    python install.py --list           # 列出可用技能、启用状态与已安装版本
    python install.py --dry-run        # 只打印将执行的复制与备份，不实际安装
    python install.py --list-backups   # 列出备份
    python install.py --restore <技能名> [--backup <时间戳>]   # 从备份恢复
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

ROOT = os.path.dirname(os.path.abspath(__file__))
SKILLS_DIR = os.path.join(ROOT, "skills")
CONFIG_PATH = os.path.join(ROOT, "config.json")
PLUGIN_MANIFEST = os.path.join(ROOT, ".claude-plugin", "marketplace.json")
HOME = os.path.expanduser("~")
TARGET_DIR = os.path.join(HOME, ".claude", "skills")

# 覆盖安装前的备份与安装状态全部落在同一目录下：删掉它即清空本安装器在用户机的足迹。
# 备份与状态逻辑与 uninstall.py 的同名函数保持一致——两处一起改。
BACKUP_ROOT = os.path.join(HOME, ".claude", "backup", "lldwb-skills")
STATE_PATH = os.path.join(BACKUP_ROOT, "state.json")
IGNORE_PATTERNS = (".tasks", "__pycache__", "*.pyc", "*.pyo")


def die(msg, code=1):
    print("ERROR: " + msg, file=sys.stderr)
    sys.exit(code)


def now_stamp():
    return time.strftime("%Y-%m-%d_%H%M%S")


def now_iso():
    return time.strftime("%Y-%m-%dT%H:%M:%S")


def repo_version():
    """版本号取自 .claude-plugin/marketplace.json（发版三处对齐之一），读不到时记 unknown。"""
    try:
        with open(PLUGIN_MANIFEST, "r", encoding="utf-8") as f:
            return json.load(f).get("version") or "unknown"
    except Exception:
        return "unknown"


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


def backup_skill(src_dir, stamp, dry_run=False):
    """把将被覆盖的技能目录复制到 <BACKUP_ROOT>/<stamp>/<技能名>/，返回备份路径。"""
    dst = os.path.join(BACKUP_ROOT, stamp, os.path.basename(src_dir))
    if dry_run:
        return dst
    if os.path.exists(dst):
        shutil.rmtree(dst)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copytree(src_dir, dst, ignore=shutil.ignore_patterns(*IGNORE_PATTERNS))
    return dst


def list_backups():
    """返回 [(时间戳, [技能名, ...]), ...]，按时间倒序。"""
    if not os.path.isdir(BACKUP_ROOT):
        return []
    out = []
    for stamp in sorted(os.listdir(BACKUP_ROOT), reverse=True):
        d = os.path.join(BACKUP_ROOT, stamp)
        if not os.path.isdir(d):
            continue
        names = sorted(n for n in os.listdir(d) if os.path.isdir(os.path.join(d, n)))
        out.append((stamp, names))
    return out


def restore_skill(name, stamp=None):
    """把备份中的技能目录恢复到 ~/.claude/skills/；目标已存在时停下报告，不覆盖。"""
    candidates = [b for b in list_backups() if name in b[1]]
    if stamp:
        candidates = [b for b in candidates if b[0] == stamp]
    if not candidates:
        die("备份中没有技能 '%s'%s（用 --list-backups 查看现有备份）"
            % (name, "（时间戳 %s）" % stamp if stamp else ""))
    use_stamp = candidates[0][0]
    src = safe_skill_dir(os.path.join(BACKUP_ROOT, use_stamp), name)
    dst = safe_skill_dir(TARGET_DIR, name)
    if os.path.exists(dst):
        die("目标已存在，未覆盖：%s\n请先卸载该技能（python uninstall.py %s）后重试" % (dst, name))
    os.makedirs(TARGET_DIR, exist_ok=True)
    shutil.copytree(src, dst)
    print("已恢复: %s -> %s（来自备份 %s）" % (src, dst, use_stamp))


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
    ap.add_argument("--list", action="store_true", help="列出可用技能、启用状态与已安装版本")
    ap.add_argument("--dry-run", action="store_true", help="只打印将执行的复制与备份，不实际安装")
    ap.add_argument("--list-backups", action="store_true", help="列出备份目录下的时间戳与技能")
    ap.add_argument("--restore", metavar="技能名", help="从备份恢复指定技能（默认取最近一次）")
    ap.add_argument("--backup", metavar="时间戳", help="配合 --restore 指定备份时间戳")
    args = ap.parse_args()

    skills = load_skills()
    if args.list:
        recorded = load_state().get("skills", {})
        for name in sorted(skills):
            flag = "enabled" if skills[name].get("enabled", True) else "disabled"
            dst = os.path.join(TARGET_DIR, name)
            if not os.path.isdir(dst):
                mark = "未安装"
            elif name in recorded:
                mark = "已安装 %s (%s)" % (recorded[name].get("version") or "unknown",
                                           recorded[name].get("installedAt") or "unknown")
            else:
                mark = "已安装（无本仓库安装记录）"
            print("%s\t%s\t%s" % (name, flag, mark))
        return

    if args.list_backups:
        backups = list_backups()
        if not backups:
            print("暂无备份（%s）" % BACKUP_ROOT)
        for stamp, names in backups:
            print("%s\t%s" % (stamp, "、".join(names) if names else "(无技能目录)"))
        return

    if args.restore:
        restore_skill(args.restore, args.backup)
        return

    if args.names:
        todo = [(n, skills.get(n, {})) for n in args.names]
        for n, _ in todo:
            if not os.path.isdir(safe_skill_dir(SKILLS_DIR, n)):
                die("技能 '%s' 不存在于 %s" % (n, SKILLS_DIR))
    else:
        # 无参安装以 config.json 的启用清单为准：缺配置时自动创建最小配置
        # （未列出的技能默认启用 = 全量安装），仅在首次创建、已存在绝不覆盖
        if not os.path.exists(CONFIG_PATH):
            try:
                with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                    json.dump({"skills": {}}, f, ensure_ascii=False, indent=2)
                    f.write("\n")
                print("已自动创建最小配置: %s（未列出的技能默认启用，可按需编辑）" % CONFIG_PATH)
            except OSError as e:
                die("无法自动创建 %s（%s）" % (CONFIG_PATH, e))
        todo = [(n, s) for n, s in sorted(skills.items()) if s.get("enabled", True)]

    if not todo:
        die("没有可安装的技能（config.json 中全部 disabled）")
    if not args.dry_run:
        os.makedirs(TARGET_DIR, exist_ok=True)

    stamp = now_stamp()
    state = load_state()
    installed = 0
    backed_up = 0
    for name, _ in todo:
        src = safe_skill_dir(SKILLS_DIR, name)
        dst = safe_skill_dir(TARGET_DIR, name)
        print("%s -> %s" % (src, dst))
        exists = os.path.exists(dst)
        if exists:
            # 覆盖前先备份原目录，可经 --restore 回滚
            print("  备份原目录 -> %s" % backup_skill(dst, stamp, dry_run=args.dry_run))
            backed_up += 1
        if not args.dry_run:
            if exists:
                shutil.rmtree(dst)
            # 跳过本地产物，避免把 .tasks 里的查询结果/任务产物带到安装目录
            shutil.copytree(src, dst, ignore=shutil.ignore_patterns(*IGNORE_PATTERNS))
            state["skills"][name] = {
                "version": repo_version(),
                "installedAt": now_iso(),
                "backup": stamp if exists else None,
            }
            installed += 1

    if args.dry_run:
        print("(--dry-run: 未实际安装、未写备份与状态)")
    else:
        if installed:
            state["version"] = repo_version()
            state["installedAt"] = now_iso()
            save_state(state)
        print("已安装 %d 个技能到 %s" % (installed, TARGET_DIR))
        if backed_up:
            print("已备份 %d 个被覆盖的目录到 %s（恢复: python install.py --restore <技能名>）"
                  % (backed_up, os.path.join(BACKUP_ROOT, stamp)))
        print("提示: 重新安装会覆盖同名技能目录（覆盖前自动备份）；卸载用 uninstall.py")


if __name__ == "__main__":
    main()
