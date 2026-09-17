#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
按 tag 补齐 gitee 镜像的发行版（仓库自身工具，非技能；对应 GitHub 侧的 release.py）。

gitee API v5 只认**私人令牌**（推送用的账号密码不行）。令牌按以下顺序取：
    ① --token  ② 环境变量 GITEE_TOKEN  ③ `.tasks/gitee-token.txt`
默认只读（列出计划），`--apply` 才真正调用 gitee API 创建；已存在的发行版跳过、不修改。

正文与 GitHub 侧同源：取工作区 CHANGELOG.md 的对应段落，并在创建前用 release.py 的
`entry_mismatch` 校验它与 **tag 提交处**的条目一致——不一致即阻塞、不猜测正文。
owner/repo 从 gitee 远端地址解析，不硬编码。`--verify` 回读远端发行版正文与 CHANGELOG
比对（两侧正文同源是「Release 只作呈现层」的前提，提交后核对用它）。

用法:
    python create-gitee-release.py                       # 只列出计划
    python create-gitee-release.py --apply               # 补齐全部缺失的发行版
    python create-gitee-release.py --tag v2.4.0 --apply  # 只补指定版本
    python create-gitee-release.py --verify               # 回读远端正文并与 CHANGELOG 比对
退出码: 0 = 无阻塞项；1 = 有版本被阻塞、或有请求失败
"""
import os
import re
import sys
import json
import argparse
import urllib.parse
import urllib.request
import urllib.error

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
import release  # noqa: E402  复用其 changelog_sections / local_versions / entry_mismatch / git

API_ROOT = "https://gitee.com/api/v5"
TOKEN_FILE = os.path.join(ROOT, ".tasks", "gitee-token.txt")


def gitee_slug():
    """从 gitee 远端地址解析 owner/repo。"""
    rc, url, err = release.git("remote", "get-url", "gitee")
    if rc != 0 or not url:
        print("阻塞: 无法读取 gitee 远端地址：%s" % (err or "未配置 gitee 远端"))
        return None
    m = re.search(r"gitee\.com[/:]([^/]+)/(.+?)(?:\.git)?$", url)
    if not m:
        print("阻塞: gitee 远端不是 gitee.com 地址（%s）" % url)
        return None
    return "%s/%s" % (m.group(1), m.group(2))


def remote_tags():
    """gitee 远端已有的 tag 名集合（缺它说明 tag 未推，先推再建发行版）。"""
    rc, out, err = release.git("ls-remote", "--tags", "gitee")
    if rc != 0:
        print("阻塞: 读取 gitee 远端 tag 失败：%s" % (err or "未知错误"))
        return None
    return {line.split("refs/tags/")[-1].rstrip("^{}") for line in out.splitlines() if "refs/tags/" in line}


def api(method, path, token, fields=None):
    """调用 gitee API v5；返回 (status, body)，网络错误时 status 为 0。"""
    url = API_ROOT + path
    data = None
    if fields is not None:
        fields = dict(fields)
        fields["access_token"] = token
        data = urllib.parse.urlencode(fields).encode("utf-8")
    else:
        url += ("&" if "?" in url else "?") + urllib.parse.urlencode({"access_token": token})
    req = urllib.request.Request(url, data=data, method=method, headers={
        "Content-Type": "application/x-www-form-urlencoded",
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
        return 0, {"message": "网络不可达（%s）" % exc}


def read_token(cli_token):
    """令牌取值顺序：命令行 → 环境变量 → 本地令牌文件。"""
    if cli_token:
        return cli_token
    if os.environ.get("GITEE_TOKEN"):
        return os.environ["GITEE_TOKEN"]
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    return None


def run_verify(slug, token, sections, targets):
    """回读 gitee 发行版正文与 CHANGELOG 对应段落比对（只读，不改远端）。"""
    status, releases = api("GET", "/repos/%s/releases?per_page=100" % slug, token)
    if status != 200:
        print("阻塞: 读取 gitee 发行版列表失败（HTTP %s）：%s" % (status, releases.get("message")))
        return 1
    wanted = set(targets) if targets else None
    print("gitee 发行版正文比对：%s（远端发行版 %d 个，CHANGELOG 段落 %d 个）\n"
          % (slug, len(releases), len(sections)))
    stats = {"一致": 0, "不一致": 0, "缺段落": 0, "跳过": 0}
    bad = []
    for rel in sorted(releases, key=lambda r: r.get("tag_name", "")):
        tag = rel.get("tag_name", "")
        version = tag[1:] if tag.startswith("v") else tag
        if wanted and version not in wanted:
            stats["跳过"] += 1
            continue
        want = sections.get(version)
        if want is None:
            stats["缺段落"] += 1
            bad.append(tag)
            print("  %-10s 阻塞     CHANGELOG 里没有 [%s] 段落" % (tag, version))
            continue
        have = rel.get("body") or ""
        if release._norm(have) == release._norm(want):
            stats["一致"] += 1
            print("  %-10s 一致     %d 字" % (tag, len(release._norm(want))))
        else:
            stats["不一致"] += 1
            bad.append(tag)
            print("  %-10s 不一致   现 %d 字 → 新 %d 字：%s"
                  % (tag, len(release._norm(have)), len(release._norm(want)),
                     release.first_diff_line(have, want)))
    print("\n结果: " + "，".join("%s %d" % (k, v) for k, v in stats.items() if v))
    if bad:
        print("  需处理（%d 个）：%s —— 回读只报告，改远端请走 gitee API（脚本不代改）"
              % (len(bad), " ".join(bad)))
    return 1 if bad else 0


def main():
    ap = argparse.ArgumentParser(description="按 tag 补齐 gitee 镜像发行版（正文取自 CHANGELOG.md）")
    ap.add_argument("--apply", action="store_true", help="真正创建发行版（缺省只列出计划）")
    ap.add_argument("--tag", nargs="*", metavar="vX.Y.Z", help="只处理指定版本（可多个）")
    ap.add_argument("--verify", action="store_true", help="回读远端正文并与 CHANGELOG 比对（只读）")
    ap.add_argument("--token", help="gitee 私人令牌（缺省取 GITEE_TOKEN 或 .tasks/gitee-token.txt）")
    args = ap.parse_args()

    slug = gitee_slug()
    sections = release.changelog_sections()
    versions = release.local_versions()
    token = read_token(args.token)
    if not slug or not versions:
        return 1
    if not token:
        print("阻塞: 未提供 gitee 私人令牌（--token / GITEE_TOKEN / %s）" % TOKEN_FILE)
        return 1

    targets = versions
    if args.tag:
        wanted = [t[1:] if t.startswith("v") else t for t in args.tag]
        targets = [v for v in versions if v in wanted]
        for t in wanted:
            if t not in versions:
                print("阻塞: 本地没有注解 tag v%s" % t)
                return 1

    if args.verify:
        return run_verify(slug, token, sections, targets)

    print("补齐 gitee 发行版：%s（本地注解 tag %d 个，处理 %d 个）"
          % (slug, len(versions), len(targets)))

    status, body = api("GET", "/repos/%s/releases?per_page=100" % slug, token)
    if status != 200:
        print("阻塞: 读取 gitee 发行版列表失败（HTTP %s）：%s" % (status, body.get("message")))
        return 1
    released = {item.get("tag_name") for item in body if item.get("tag_name")}
    tags = remote_tags()
    if tags is None:
        return 1
    print()

    plan, failed = [], False
    for i, version in enumerate(targets, 1):
        tag = "v%s" % version
        text = sections.get(version)
        state, detail = "待创建", "正文 %d 字（CHANGELOG.md）" % len(text) if text else ""
        if not text:
            state, detail = "阻塞", "CHANGELOG.md 里没有 [%s] 段落 —— 不猜测正文" % version
        elif tag not in tags:
            state, detail = "阻塞", "gitee 远端没有 tag %s —— 先 git push gitee main --follow-tags" % tag
        elif tag in released:
            state, detail = "已存在", "跳过，不修改已发布的发行版"
        elif (mismatch := release.entry_mismatch(tag, version, text)):
            state, detail = "阻塞", mismatch
        elif args.apply:
            status, resp = api("POST", "/repos/%s/releases" % slug, token, {
                "tag_name": tag, "name": tag, "body": text,
                "prerelease": "false", "target_commitish": "main",
            })
            if status in (200, 201):
                state = "已创建"
                # gitee 的发行版对象不含 html_url，网页地址由仓库与 tag 直接拼出
                detail = "https://gitee.com/%s/releases/tag/%s" % (slug, tag)
            else:
                state, detail, failed = "失败", "HTTP %s：%s" % (status, resp.get("message")), True
        plan.append((i, tag, state, detail))
        print("  [%2d/%d] %-8s %-6s %s" % (i, len(targets), tag, state, detail))

    blocked = [x for x in plan if x[2] == "阻塞"]
    print()
    if failed or blocked:
        if blocked:
            print("结果: %d 个版本被阻塞：" % len(blocked))
            for _, tag, _, detail in blocked:
                print("  %s  %s" % (tag, detail))
        if failed:
            print("结果: 有版本创建失败（见上）")
        return 1
    if args.apply:
        print("结果: 创建 %d 个发行版" % sum(1 for _, _, s, _ in plan if s == "已创建"))
    else:
        pending = [tag for _, tag, s, _ in plan if s == "待创建"]
        print("结果: %d 个待创建（%s）" % (len(pending), " ".join(pending)) if pending
              else "结果: 无需创建")
    return 0


if __name__ == "__main__":
    sys.exit(main())
