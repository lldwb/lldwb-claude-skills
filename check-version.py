#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
版本与 tag 一致性校验（仓库自身工具，非技能）。

确认「CHANGELOG.md 顶部最新条目版本 = .claude-plugin/marketplace.json 的 version =
注解 tag vX.Y.Z，且该 tag 在当前分支可达、已推送到远程 main」，防止版本号更新了
却没打 tag / tag 只在本地 —— 那会让远端 `/tree/<tag>` 变成 404，引用该版本的
文档链接全部失效（约定见 AGENTS.md「架构」第 4 条）。

只核对三处是否一致与 tag 是否可达、**不定级**：该升大 / 中 / 小哪一位由人按
「架构」第 4 条的分级规则选取（同「脚本只取数，判定归 agent」）。

用法:
    python check-version.py              # 本地校验（版本号三处一致 / 注解 tag 存在 / tag 可达）
    python check-version.py --remote     # 追加远程校验（tag 已推送且指向的提交已在远程 main 上）
退出码: 0 = 通过；1 = 不通过
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
CHANGELOG_PATH = os.path.join(ROOT, "CHANGELOG.md")
MARKETPLACE_PATH = os.path.join(ROOT, ".claude-plugin", "marketplace.json")
VERSION_RE = re.compile(r"^## \[(\d+\.\d+\.\d+)\]", re.M)

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


def short(sha):
    return sha[:7] if sha else "?"


def changelog_version():
    if not os.path.exists(CHANGELOG_PATH):
        note("未找到 %s" % CHANGELOG_PATH)
        return None
    with open(CHANGELOG_PATH, "r", encoding="utf-8") as f:
        m = VERSION_RE.search(f.read())
    if not m:
        note("CHANGELOG.md 里没有 `## [x.y.z]` 形式的版本标题")
        return None
    return m.group(1)


def marketplace_version():
    if not os.path.exists(MARKETPLACE_PATH):
        note("未找到 %s" % MARKETPLACE_PATH)
        return None
    try:
        with open(MARKETPLACE_PATH, "r", encoding="utf-8") as f:
            version = json.load(f).get("version")
    except (ValueError, OSError) as exc:
        note("marketplace.json 读取/解析失败：%s" % exc)
        return None
    if not version:
        note("marketplace.json 缺少 version 字段")
        return None
    return version


def check_local(tag):
    """本地三项：tag 存在、是注解 tag、指向的提交在当前分支可达。"""
    rc, sha, _ = git("rev-list", "-n1", tag)
    if rc != 0:
        note("缺少 tag %s —— 版本号已更新却没打 tag。\n"
             "    修复: git tag -a %s -m \"<说明>\"   # 再与 main 一并推送" % (tag, tag))
        return None
    rc, obj_type, _ = git("cat-file", "-t", tag)
    if rc == 0 and obj_type != "tag":
        note("tag %s 是轻量 tag（%s）—— `git push --follow-tags` 不会推送轻量 tag，"
             "远程将缺该 tag。\n"
             "    修复: git tag -d %s && git tag -a %s -m \"<说明>\"" % (tag, obj_type, tag, tag))
        return None
    print("  本地 tag      %s -> %s（注解 tag）" % (tag, short(sha)))
    rc, _, _ = git("merge-base", "--is-ancestor", sha, "HEAD")
    if rc != 0:
        note("tag %s 指向 %s，不在当前分支可达范围内（游离提交或未合并分支）——"
             "远端引用会与 main 脱节" % (tag, short(sha)))
        return None
    print("  分支可达      是")
    return sha


def check_remote(tag, local_sha):
    """远程三项：tag 已推送、指向与本地一致、指向的提交已在远程 main 历史中。"""
    rc, out, err = git("ls-remote", "origin",
                       "refs/tags/%s" % tag, "refs/tags/%s^{}" % tag,
                       "refs/heads/main")
    if rc != 0:
        note("无法访问远程 origin（%s）—— 网络不可达时按本机代理配置后重试；"
             "仅需本地校验时去掉 --remote" % (err.splitlines()[-1] if err else "未知错误"))
        return
    remote_tag = None
    remote_main = None
    for line in out.splitlines():
        parts = line.split()
        if len(parts) != 2:
            continue
        sha, ref = parts
        if ref == "refs/tags/%s^{}" % tag:
            remote_tag = sha
        elif ref == "refs/heads/main":
            remote_main = sha
    if remote_tag is None:
        note("远程没有 tag %s —— tag 只存在于本地。\n"
             "    修复: git push origin main --follow-tags" % tag)
        return
    if remote_tag != local_sha:
        note("远程 tag %s 指向 %s，与本地 %s 不一致（tag 被重打过？）"
             % (tag, short(remote_tag), short(local_sha)))
        return
    print("  远程 tag      %s -> %s" % (tag, short(remote_tag)))
    if remote_main is None:
        note("远程没有 main 分支")
        return
    rc, _, _ = git("cat-file", "-e", remote_main)
    if rc != 0:
        print("  远程 main     %s（本地缺该提交对象，未核对 tag 是否已在 main 上；可先 git fetch）"
              % short(remote_main))
        return
    rc, _, _ = git("merge-base", "--is-ancestor", local_sha, remote_main)
    if rc != 0:
        note("tag %s 指向的 %s 不在远程 main（%s）历史中 —— main 尚未推送到该提交，"
             "远端会出现「tag 打得开、main 上却看不到」的错位。\n"
             "    修复: git push origin main" % (tag, short(local_sha), short(remote_main)))
        return
    print("  远程 main     %s（tag 提交已在其中）" % short(remote_main))


def main():
    ap = argparse.ArgumentParser(description="校验版本号与 tag 一致性")
    ap.add_argument("--remote", action="store_true",
                    help="追加校验远程 tag 与远程 main（需能访问 origin）")
    args = ap.parse_args()

    print("校验版本与 tag 一致性：%s" % ROOT)
    cl_ver = changelog_version()
    mp_ver = marketplace_version()
    print("  CHANGELOG.md        %s" % (cl_ver or "<未解析到>"))
    print("  marketplace.json    %s" % (mp_ver or "<未解析到>"))

    if cl_ver and mp_ver and cl_ver != mp_ver:
        note("版本号不一致：CHANGELOG.md 顶部为 %s，marketplace.json 为 %s"
             % (cl_ver, mp_ver))

    version = cl_ver or mp_ver
    if version:
        tag = "v%s" % version
        local_sha = check_local(tag)
        if local_sha and args.remote:
            check_remote(tag, local_sha)

    print()
    if problems:
        print("结果: 不通过，%d 项待处理：" % len(problems))
        for i, msg in enumerate(problems, 1):
            print("  [%d] %s" % (i, msg))
        return 1
    print("结果: 通过（版本 %s 三处对齐%s）"
          % (version, "，远程一致" if args.remote else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
