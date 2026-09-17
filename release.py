#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
按 tag 补齐 GitHub Release（仓库自身工具，非技能）。

以 CHANGELOG.md 各版本段落为 Release 正文，为本地注解 tag 逐个补 Release ——
让仓库首页的 Releases 区块直接呈现最新版变更，Watchers 也能收到 release 通知
（约定见 AGENTS.md「架构」第 4 条）。

只创建缺失的 Release，**不修改已存在的**；不推 tag、不改 CHANGELOG、不发版。
默认只读（列出将创建 / 跳过的版本），`--apply` 才真正调用 GitHub API。

创建前校验**条目一致性**：Release 正文取自**工作区**的 CHANGELOG.md，而发布出去的正文
应当等于 tag 所指提交处的条目。两者不一致（版本条目改了没提交、或工作区停在别的提交）
时正文会带上未发布的草稿内容 —— 这类版本标为「阻塞」、不猜测正文（曾出现正文含两条
从未进入任何提交的条目行）。校验只比对**该版本那一段**，回填历史 tag 不受影响。

创建的只是「呈现层」：正文取自 CHANGELOG、版本号取自 tag，四处事实不在此重新判定 ——
tag 缺失与 CHANGELOG 缺段落都只报告不猜测（同「脚本只取数，判定归 agent」）。

用法:
    python release.py                        # 只列出计划（不发写请求）
    python release.py --apply                # 真正创建（token 取 GITHUB_TOKEN / GH_TOKEN）
    python release.py --tag v2.2.0 --apply   # 只补指定版本
退出码: 0 = 无阻塞项（可能仍有待创建项）；1 = 有版本被阻塞或有请求失败
"""
import sys
import os
import re
import json
import codecs
import argparse
import subprocess
import urllib.request
import urllib.error


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
API_ROOT = "https://api.github.com"
SECTION_RE = re.compile(r"^## \[(\d+\.\d+\.\d+)\](?: - (\d{4}-\d{2}-\d{2}))?\s*$", re.M)

blocked = []


def note(msg):
    blocked.append(msg)


def git(*args):
    """执行 git 子命令，返回 (returncode, stdout, stderr)，均由调用方判定。"""
    proc = subprocess.run(["git"] + list(args), cwd=ROOT,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return (proc.returncode,
            proc.stdout.decode("utf-8", "replace").strip(),
            proc.stderr.decode("utf-8", "replace").strip())


def version_key(version):
    """按数值排序版本号，避免 v1.10.0 排在 v1.9.0 之前。"""
    return tuple(int(part) for part in version.split("."))


def changelog_sections():
    """解析 CHANGELOG.md，返回 {版本号: 正文}（正文不含版本标题行）。"""
    if not os.path.exists(CHANGELOG_PATH):
        note("未找到 %s" % CHANGELOG_PATH)
        return {}
    with open(CHANGELOG_PATH, "r", encoding="utf-8") as f:
        text = f.read()
    marks = list(SECTION_RE.finditer(text))
    sections = {}
    for i, mark in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(text)
        sections[mark.group(1)] = text[mark.end():end].strip()
    return sections


def _norm(text):
    """比对用归一：统一行尾、去首尾空白（工作区文件可能是 CRLF，仓库对象是 LF）。"""
    return (text or "").replace("\r\n", "\n").strip()


def entry_at_tag(tag, version):
    """取 tag 提交处的 CHANGELOG.md 里该版本条目；返回 (条目文本, 错误信息)。"""
    rc, text, err = git("show", "%s:CHANGELOG.md" % tag)
    if rc != 0:
        return None, "读取 %s 提交处的 CHANGELOG.md 失败：%s" % (tag, err or "未知错误")
    marks = list(SECTION_RE.finditer(text))
    for i, mark in enumerate(marks):
        if "v%s" % mark.group(1) != tag:
            continue
        end = marks[i + 1].start() if i + 1 < len(marks) else len(text)
        return text[mark.end():end], None
    return None, "%s 提交处的 CHANGELOG.md 没有 [%s] 段落" % (tag, version)


def first_diff_line(old, new):
    """首个不同行的摘要，供提示用（只报告，不判定）。"""
    a, b = _norm(old).split("\n"), _norm(new).split("\n")
    for i in range(max(len(a), len(b))):
        x = a[i] if i < len(a) else "<缺行>"
        y = b[i] if i < len(b) else "<缺行>"
        if x != y:
            return "首个差异行 %d：tag 处 %s / 工作区 %s" % (i + 1, x[:36], y[:36])
    return ""


def entry_mismatch(tag, version, body):
    """工作区条目与 tag 提交处条目不一致时返回差异摘要，一致返回空串。"""
    tagged, err = entry_at_tag(tag, version)
    if err:
        return err
    if _norm(tagged) == _norm(body):
        return ""
    return ("条目与 %s 提交处不一致（正文会带上未提交 / 非该版本的草稿内容）—— %s"
            % (tag, first_diff_line(tagged, body)))


def local_versions():
    """本地注解 tag 的版本号，按版本升序；轻量 tag 不入列（会被远程漏推）。"""
    rc, out, err = git("for-each-ref", "--format=%(refname:short) %(objecttype)", "refs/tags/")
    if rc != 0:
        note("读取本地 tag 失败：%s" % (err or "未知错误"))
        return []
    versions = []
    for line in out.splitlines():
        parts = line.split()
        if len(parts) != 2 or parts[1] != "tag" or not parts[0].startswith("v"):
            continue
        name = parts[0][1:]
        if re.fullmatch(r"\d+\.\d+\.\d+", name):
            versions.append(name)
    return sorted(versions, key=version_key)


def repo_slug():
    """从 origin 解析 owner/repo，不硬编码仓库名（本工具随仓库复制也成立）。"""
    rc, url, err = git("remote", "get-url", "origin")
    if rc != 0 or not url:
        note("无法读取 origin 地址：%s" % (err or "未配置 origin"))
        return None
    m = re.search(r"github\.com[/:]([^/]+)/(.+?)(?:\.git)?$", url)
    if not m:
        note("origin 不是 GitHub 仓库地址（%s）" % url)
        return None
    return "%s/%s" % (m.group(1), m.group(2))


def api(method, path, token, payload=None):
    """调用 GitHub REST API，返回 (status, body)；网络错误时 status 为 0。"""
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(API_ROOT + path, data=data, method=method, headers={
        "Authorization": "Bearer %s" % token,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "Content-Type": "application/json",
        "User-Agent": "lldwb-claude-skills-release",
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8", "replace")
            return resp.status, (json.loads(raw) if raw else {})
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", "replace")
        try:
            raw = json.loads(raw).get("message", raw)
        except ValueError:
            pass
        return exc.code, {"message": raw}
    except OSError as exc:
        return 0, {"message": "网络不可达（%s）—— 需要代理时设置 https_proxy 环境变量" % exc}


def remote_state(slug, token):
    """一次取回远端已有 Release 的 tag 集合与远端 tag 名集合，返回 (released, remote_tags)。"""
    status, body = api("GET", "/repos/%s/releases?per_page=100" % slug, token)
    if status != 200:
        note("读取远端 Release 列表失败（HTTP %s）：%s" % (status, body.get("message")))
        return None, None
    released = {item.get("tag_name") for item in body if item.get("tag_name")}
    status, body = api("GET", "/repos/%s/git/matching-refs/tags/v" % slug, token)
    if status != 200:
        note("读取远端 tag 列表失败（HTTP %s）：%s" % (status, body.get("message")))
        return None, None
    remote_tags = {ref.get("ref", "").replace("refs/tags/", "") for ref in body}
    return released, remote_tags


def main():
    ap = argparse.ArgumentParser(description="按 tag 补齐 GitHub Release（正文取自 CHANGELOG.md）")
    ap.add_argument("--apply", action="store_true", help="真正创建 Release（缺省只列出计划）")
    ap.add_argument("--tag", nargs="*", metavar="vX.Y.Z", help="只处理指定版本（可多个）")
    ap.add_argument("--repo", metavar="owner/repo", help="覆盖 origin 解析出的仓库")
    ap.add_argument("--token", help="GitHub token（缺省取 GITHUB_TOKEN / GH_TOKEN 环境变量）")
    args = ap.parse_args()

    slug = args.repo or repo_slug()
    sections = changelog_sections()
    all_versions = local_versions()
    if not slug or not all_versions:
        for msg in blocked:
            print("阻塞: %s" % msg)
        return 1

    targets = all_versions
    if args.tag:
        wanted = [t[1:] if t.startswith("v") else t for t in args.tag]
        unknown = [t for t in wanted if t not in all_versions]
        for t in unknown:
            note("本地没有注解 tag v%s" % t)
        targets = [v for v in all_versions if v in wanted]
    latest = all_versions[-1]

    print("补齐 Release：%s（本地注解 tag %d 个，最新 v%s）"
          % (slug, len(all_versions), latest))
    if args.tag:
        print("  限定范围      %s" % " ".join("v" + v for v in targets))
    print()

    token = args.token or os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    released = remote_tags = None
    if token:
        released, remote_tags = remote_state(slug, token)
    else:
        note("未提供 token（--token 或 GITHUB_TOKEN / GH_TOKEN 环境变量）——无法核对远端状态")

    plan = []
    for i, version in enumerate(targets, 1):
        tag = "v%s" % version
        body = sections.get(version)
        state = "待创建"
        detail = "正文 %d 字（CHANGELOG.md）" % len(body) if body else ""
        if not body:
            state = "阻塞"
            detail = "CHANGELOG.md 里没有 [%s] 段落 —— 不猜测正文" % version
            note("v%s 缺少 CHANGELOG 段落" % version)
        elif remote_tags is not None and tag not in remote_tags:
            state = "阻塞"
            detail = "远端没有 tag %s —— 先 git push origin %s（否则 GitHub 会按分支自建轻量 tag）" % (tag, tag)
            note("v%s 未推送到远端" % version)
        elif released is not None and tag in released:
            state = "已存在"
            detail = "跳过，不修改已发布的 Release"
        elif (mismatch := entry_mismatch(tag, version, body)):
            state = "阻塞"
            detail = mismatch
            note("v%s 的 CHANGELOG 条目与 %s 提交处不一致" % (version, tag))
        elif args.apply and token:
            status, resp = api("POST", "/repos/%s/releases" % slug, token, {
                "tag_name": tag,
                "name": tag,
                "body": body,
                "draft": False,
                "prerelease": False,
                "make_latest": "true" if version == latest else "false",
            })
            if status == 201:
                state = "已创建"
                detail = str(resp.get("html_url", ""))
            else:
                state = "失败"
                detail = "HTTP %s：%s" % (status, resp.get("message"))
                note("v%s 创建失败" % version)
        elif not token:
            state = "待创建"
            detail = "正文 %d 字（需 token 才能核对远端）" % len(body)
        plan.append((i, tag, state, detail))
        print("  [%2d/%d] %-8s %-6s %s" % (i, len(targets), tag, state, detail))

    print()
    if not token:
        print("结果: 未提供 token，仅按本地 CHANGELOG 与 tag 列出计划（加 --token 或设 GITHUB_TOKEN 后重跑）")
        return 1
    if blocked:
        print("结果: %d 项待处理：" % len(blocked))
        for i, msg in enumerate(blocked, 1):
            print("  [%d] %s" % (i, msg))
        return 1
    if args.apply:
        created = sum(1 for _, _, state, _ in plan if state == "已创建")
        print("结果: 创建 %d 个 Release（最新 v%s 已标 latest）" % (created, latest))
        return 0
    pending = [tag for _, tag, state, _ in plan if state == "待创建"]
    if pending:
        print("结果: %d 个待创建（%s），加 --apply 执行" % (len(pending), " ".join(pending)))
    else:
        print("结果: 无需创建，%d 个版本均已有 Release" % len(plan))
    return 0


if __name__ == "__main__":
    sys.exit(main())
