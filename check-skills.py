#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
技能仓库自检（仓库自身工具，非技能）。

把「架构」与「提交规范」里可机械核对的部分一次跑完，作为改动技能后的体检：

  ① 技能清单与数量声明（磁盘目录数 / marketplace 数组 / 技能表 / 正文里的「N 个技能」）
  ② SKILL.md 骨架与 README 段位（七节基准 / frontmatter / name = 目录 / README 四段）
  ③ 技能名疑似拼错（正文里的连字符 token 与既有技能名编辑距离过近 —— 会把 agent 转错技能）
  ④ 脱敏扫描（通用模式内置 + 业务词表外置）
  ⑤ 旧技能名残留（改名后不得复活）
  ⑥ 分发清单同步（marketplace / README / PLUGIN_README；config.json 为本地文件、只提示）

**只取数，判定归 agent**：脚本报事实与位置，是否要改、怎么改由人判断（同「架构」第 4 条）。

业务敏感词表（项目名 / 业务术语 / 模块缩写）**不入库** —— 本仓库是通用技能仓库，把敏感词
本身写进仓库等于换个地方泄露。词表放仓库根 `sensitive-terms.txt`（已 gitignore；每行一个
词，`re:` 前缀的行按正则匹配，`#` 开头为注释）；缺该文件时跳过业务词扫描并在结果里注明，
通用模式（绝对路径 / IP / 凭据赋值 / 本机用户名）始终扫描。

用法:
    python check-skills.py                 # 全部检查
    python check-skills.py --terms <文件>   # 指定业务敏感词表
退出码: 0 = 通过；1 = 有需处理项
"""
import sys
import os
import re
import json
import codecs
import argparse
import subprocess


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
MARKETPLACE_PATH = os.path.join(ROOT, ".claude-plugin", "marketplace.json")
DEFAULT_TERMS = os.path.join(ROOT, "sensitive-terms.txt")

# SKILL.md 七节基准 + 收尾的「输入」（顺序固定，标题逐字）；「git 提交规则」为技能可选节。
BASE_SECTIONS = ["角色", "适用与边界", "要求", "执行步骤", "验证", "任务目标", "注意事项", "输入"]
# README 四段基准（其余为各技能自定的补充段）。
README_SECTIONS = ["使用", "能力", "文件", "依赖"]
# frontmatter 允许的键：name / description 必备，其余限 Claude Code 官方字段（见「架构」）。
FM_REQUIRED = ["name", "description"]
FM_OFFICIAL = {"name", "description", "disable-model-invocation", "allowed-tools",
               "argument-hint", "model", "license", "version"}
# 改名前的旧技能名，改名后不得在任何位置复活（CHANGELOG 的历史记录除外）。
OLD_SKILL_NAMES = (r"fix-bug|create-mr|commit-changes|explain-project|lldwb-init|controller-check")
# 与技能名相近但确属他物的 token（产物目录名等），不报「疑似拼错」。
NON_SKILL_TOKENS = {"log-diagnosis"}
# 通用脱敏模式：任何项目下都算敏感，内置；业务专属词走外置词表。
GENERIC_PATTERNS = [
    (r"[A-Za-z]:\\", "Windows 绝对路径"),
    (r"(?<![\w.])/(?:home|Users|root)/", "Unix 绝对路径"),
    (r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b", "IP 地址"),
    (r"(?i)\b(?:password|passwd|token|secret|api[_-]?key)\s*[=:]\s*\S", "疑似凭据赋值"),
    (r"\blldwb\b", "本仓库 owner 名（技能正文须脱敏）"),
]

problems = []


def note(msg):
    problems.append(msg)


def git(*args):
    """执行 git 子命令，返回 (returncode, stdout, stderr)，均由调用方判定。"""
    proc = subprocess.run(["git"] + list(args), cwd=ROOT,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return (proc.returncode,
            proc.stdout.decode("utf-8", "replace").strip(),
            proc.stderr.decode("utf-8", "replace").strip())


def read(path):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def skill_names():
    """磁盘上的技能名（有 SKILL.md 的目录），排序返回。"""
    if not os.path.isdir(SKILLS_DIR):
        return []
    return sorted(d for d in os.listdir(SKILLS_DIR)
                  if os.path.isfile(os.path.join(SKILLS_DIR, d, "SKILL.md")))


def edit_distance(a, b):
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def check_inventory(skills):
    """① 技能清单与数量声明：磁盘为准，正文里的「N 个技能」必须等于实际数。"""
    print("=== ① 技能清单与数量声明 ===")
    print("磁盘技能数：%d" % len(skills))
    counted = []
    targets = [os.path.join(ROOT, f) for f in ("README.md", "PLUGIN_README.md", "AGENTS.md")]
    for d in skills:
        targets += [os.path.join(SKILLS_DIR, d, f) for f in ("SKILL.md", "README.md")]
    for path in targets:
        if not os.path.isfile(path):
            continue
        for n, line in enumerate(read(path).splitlines(), 1):
            for m in re.finditer(r"(\d+)\s*个技能", line):
                counted.append((os.path.relpath(path, ROOT), n, int(m.group(1))))
    bad = [c for c in counted if c[2] != len(skills)]
    print("「N 个技能」声明：%d 处，与实际不符 %d 处" % (len(counted), len(bad)))
    for rel, n, v in bad:
        print("  %s:%d  声明 %d 个（实际 %d 个）" % (rel, n, v, len(skills)))
        note("%s:%d 的技能数量声明为 %d，实际 %d" % (rel, n, v, len(skills)))


def check_structure(skills):
    """② 结构校验：SKILL.md 七节 / frontmatter / name = 目录 / README 四段。"""
    print("\n=== ② SKILL.md 骨架与 README 段位 ===")
    bad = []
    for d in skills:
        p = os.path.join(SKILLS_DIR, d, "SKILL.md")
        text = read(p)
        heads = re.findall(r"^## (.+)$", text, re.M)
        miss = [h for h in BASE_SECTIONS if not any(hd.startswith(h) for hd in heads)]
        fm = re.match(r"^---\n(.*?)\n---", text, re.S)
        if not fm:
            bad.append((d, "缺 frontmatter", "", [], []))
            continue
        keys = [l.split(":")[0].strip() for l in fm.group(1).splitlines()
                if l and not l.startswith(" ")]
        unknown = [k for k in keys if k not in FM_OFFICIAL]
        miss_key = [k for k in FM_REQUIRED if k not in keys]
        m = re.search(r"^name:\s*(\S+)", fm.group(1), re.M)
        name = m.group(1) if m else ""
        rd_path = os.path.join(SKILLS_DIR, d, "README.md")
        rmiss = []
        if not os.path.isfile(rd_path):
            rmiss = ["<无 README.md>"]
        else:
            rd = read(rd_path)
            rmiss = [s for s in README_SECTIONS if ("## " + s) not in rd]
        if miss or unknown or miss_key or name != d or rmiss:
            bad.append((d, miss, name, unknown or miss_key, rmiss))
    if not bad:
        print("不合规技能：无")
    for d, miss, name, fm_bad, rmiss in bad:
        detail = []
        if miss:
            detail.append("缺节 %s" % "/".join(miss))
        if name != d:
            detail.append("name=%r ≠ 目录" % name)
        if fm_bad:
            detail.append("frontmatter 问题 %s" % fm_bad)
        if rmiss:
            detail.append("README 缺段 %s" % "/".join(rmiss))
        print("  %s：%s" % (d, "；".join(detail)))
        note("%s 结构不合基准：%s" % (d, "；".join(detail)))


def check_typos(skills):
    """③ 技能名疑似拼错：正文里的连字符 token 与既有技能名编辑距离过近（提示层）。"""
    print("\n=== ③ 技能名疑似拼错（提示，不计入结论）===")
    name_set = set(skills)
    hints = []
    for d in skills:
        for f in ("SKILL.md", "README.md"):
            p = os.path.join(SKILLS_DIR, d, f)
            if not os.path.isfile(p):
                continue
            for i, line in enumerate(read(p).splitlines(), 1):
                for tok in set(re.findall(r"`([a-z][a-z0-9]*(?:-[a-z0-9]+)+)`", line)):
                    if tok in name_set or tok in NON_SKILL_TOKENS or len(tok) < 6:
                        continue
                    near = [(edit_distance(tok, s), s) for s in name_set]
                    dist, cand = min(near)
                    if 0 < dist <= 2:
                        hints.append((os.path.relpath(p, ROOT), i, tok, cand))
    if not hints:
        print("疑似拼错：无")
    for rel, n, tok, cand in hints:
        print("  %s:%d  `%s` 与技能名 `%s` 相近（是否拼错？）" % (rel, n, tok, cand))


def load_terms(path):
    """读业务敏感词表：每行一个词，`re:` 前缀按正则，`#` 为注释。"""
    terms = []
    for line in read(path).splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("re:"):
            terms.append((line[3:].strip(), True, "词表正则 " + line[3:].strip()))
        else:
            terms.append((re.escape(line), False, line))
    return terms


def check_sensitive(skills, terms_path):
    """④ 脱敏扫描：通用模式始终扫，业务词表按提供情况扫。"""
    print("\n=== ④ 脱敏扫描 ===")
    patterns = list(GENERIC_PATTERNS)
    if terms_path and os.path.isfile(terms_path):
        terms = load_terms(terms_path)
        patterns += [(p, label) for p, _, label in terms]
        print("业务词表：%s（%d 条）" % (os.path.relpath(terms_path, ROOT), len(terms)))
    else:
        print("业务词表：未提供（%s 不存在）—— 只扫通用模式；"
              "按需在本地建该文件（每行一个词，`re:` 前缀按正则）" % os.path.relpath(DEFAULT_TERMS, ROOT))
    hits = []
    for d in skills:
        for dirpath, _, files in os.walk(os.path.join(SKILLS_DIR, d)):
            for f in files:
                if not f.endswith(".md"):
                    continue
                p = os.path.join(dirpath, f)
                for i, line in enumerate(read(p).splitlines(), 1):
                    for pat, label in patterns:
                        if re.search(pat, line):
                            hits.append((os.path.relpath(p, ROOT), i, label, line.strip()))
    print("命中 %d 处（需人工裁定：命中不等于敏感，可能是子串误报）" % len(hits))
    for rel, n, label, line in hits:
        print("  %s:%d  [%s]  %s" % (rel, n, label, line[:80]))
        note("%s:%d 命中脱敏模式 [%s]" % (rel, n, label))


def check_old_names():
    """⑤ 旧技能名残留（排除 CHANGELOG 历史节：历史条目不改写）。"""
    print("\n=== ⑤ 旧技能名残留 ===")
    rc, out, err = git("grep", "--untracked", "-nE", OLD_SKILL_NAMES, "--",
                       "skills", "README.md", "PLUGIN_README.md", "AGENTS.md", "config.json",
                       ".claude-plugin", "install.py", "uninstall.py")
    if rc not in (0, 1):
        print("  读取失败：%s" % (err or "未知错误"))
        note("旧技能名残留检查失败：%s" % (err or "未知错误"))
        return
    lines = [l for l in out.splitlines() if l.strip()]
    print("残留：%s" % ("\n  " + "\n  ".join(lines) if lines else "无"))
    for l in lines:
        note("旧技能名残留：%s" % l)


def check_distribution(skills):
    """⑥ 分发清单同步：marketplace 数组 / README 技能表 / PLUGIN_README 技能表。"""
    print("\n=== ⑥ 分发清单同步 ===")
    if not os.path.isfile(MARKETPLACE_PATH):
        note("未找到 .claude-plugin/marketplace.json")
        print("marketplace.json：<缺失>")
    else:
        mp = read(MARKETPLACE_PATH)
        listed = re.findall(r'"\./skills/([a-z0-9-]+)"', mp)
        same = sorted(listed) == sorted(skills)
        print("marketplace.json skills 数组：%d 项，与磁盘一致=%s" % (len(listed), same))
        if not same:
            note("marketplace.json 的 skills 数组与磁盘技能不一致：缺 %s / 多 %s"
                 % (sorted(set(skills) - set(listed)), sorted(set(listed) - set(skills))))
    for f in ("README.md", "PLUGIN_README.md"):
        p = os.path.join(ROOT, f)
        if not os.path.isfile(p):
            note("未找到 %s" % f)
            print("%s：<缺失>" % f)
            continue
        txt = read(p)
        missing = [s for s in skills if ("| " + s + " |") not in txt and ("`" + s + "`") not in txt]
        print("%s：缺 %s" % (f, missing if missing else "无"))
        for s in missing:
            note("%s 的技能表缺 %s" % (f, s))
    cfg = os.path.join(ROOT, "config.json")
    if os.path.isfile(cfg):
        try:
            listed = list(json.loads(read(cfg)).get("skills") or {})
        except ValueError as exc:
            listed = []
            print("config.json 解析失败（%s）" % exc)
        unknown = [s for s in listed if s not in skills]
        print("config.json：%d 项（本地文件、未入库，允许滞后；只核对无失效项）%s"
              % (len(listed), "" if not unknown else "，失效项 %s" % unknown))
        for s in unknown:
            note("config.json 列了磁盘上不存在的技能 %s" % s)


def main():
    ap = argparse.ArgumentParser(description="技能仓库自检（骨架 / 分发清单 / 脱敏 / 数量声明）")
    ap.add_argument("--terms", default=DEFAULT_TERMS,
                    help="业务敏感词表路径（缺省 %s；不存在则跳过业务词扫描）"
                         % os.path.relpath(DEFAULT_TERMS, ROOT))
    args = ap.parse_args()

    print("技能仓库自检：%s\n" % ROOT)
    skills = skill_names()
    check_inventory(skills)
    check_structure(skills)
    check_typos(skills)
    check_sensitive(skills, args.terms)
    check_old_names()
    check_distribution(skills)

    print()
    if problems:
        print("结果: 不通过，%d 项待处理：" % len(problems))
        for i, msg in enumerate(problems, 1):
            print("  [%d] %s" % (i, msg))
        return 1
    print("结果: 通过（%d 个技能：骨架 / 分发清单 / 脱敏 / 数量声明均一致）" % len(skills))
    return 0


if __name__ == "__main__":
    sys.exit(main())
