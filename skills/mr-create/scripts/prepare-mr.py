#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
合并请求（MR/PR）素材取数脚本（通用）。
只负责校验分支与差异、拉取提交记录与变更范围并落盘；**不生成描述、不创建合并请求**，
描述撰写与创建动作由调用方 agent 完成。

用法:
    python prepare-mr.py [--source <分支>] [--target <分支>]
                         [--max-diff-lines 400] [--out-dir <目录>]

默认:
    --source 当前所在分支；--target 依次探测 origin/HEAD → main → master

前置校验（任一不通过即非零退出，且不产出素材）:
    当前目录是 git 仓库 / 源与目标分支存在 / 两者不是同一提交 /
    两分支有共同祖先 / 源分支相对目标分支存在有效差异（有领先提交或文件差异）

输出（默认落在 <仓库根>/.tasks/mr-create/）:
    mr-<源>-to-<目标>.material.md   元信息 + 远端状态 + 变更范围 + 提交记录 + 文件清单 + diff + 创建通道
    mr-<源>-to-<目标>.raw.diff      完整 diff（不截断）
stdout: 校验结论 + 关键事实 + 输出路径

源分支推送状态给 `state`（状态键，键名即技能「推送源分支」表的行键）与事实描述，
**不判定该不该推送**——处置规则由调用方 agent 按技能表格执行。
"""
import argparse
import codecs
import datetime
import glob
import os
import re
import shutil
import subprocess
import sys
from urllib.parse import quote, urlencode

GIT = ["git", "-c", "core.quotepath=false"]
DEFAULT_MAX_DIFF_LINES = 400


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


def ref_exists(ref):
    ok, _, _ = git_ok("rev-parse", "--verify", "--quiet", ref + "^{commit}")
    return ok


def ref_sha(ref):
    ok, out, _ = git_ok("rev-parse", "--verify", "--quiet", ref + "^{commit}")
    return out.strip() if ok else None


# ---------------------------------------------------------------- 分支解析

def resolve_branch(spec, role):
    """把分支名解析为 {name, local_ref, remote_ref, local_sha, remote_sha}。

    可带 origin/ 前缀；本地分支与 origin 远端分支任一存在即可。
    """
    name = spec[len("origin/"):] if spec.startswith("origin/") else spec
    if not name:
        die("--%s 为空" % role)
    local_ref = "refs/heads/" + name
    remote_ref = "refs/remotes/origin/" + name
    local_sha, remote_sha = ref_sha(local_ref), ref_sha(remote_ref)
    if local_sha is None and remote_sha is None:
        hint = ""
        if role == "source" and ref_sha(spec):
            hint = "（%s 可解析为提交，但不是分支名；--source 需传分支名）" % spec
        die("分支不存在: %s%s\n  本地分支与 origin 远端分支均无该名字（git branch -a 可查看全部）" % (spec, hint))
    return {
        "name": name,
        "local_ref": local_ref if local_sha else None,
        "remote_ref": remote_ref if remote_sha else None,
        "local_sha": local_sha,
        "remote_sha": remote_sha,
    }


def default_target_name():
    """探测默认目标分支：origin/HEAD → main → master。"""
    ok, out, _ = git_ok("symbolic-ref", "--quiet", "refs/remotes/origin/HEAD")
    if ok:
        name = out.strip().rsplit("/", 1)[-1]
        if name:
            return name
    for cand in ("main", "master"):
        if ref_exists("refs/heads/" + cand) or ref_exists("refs/remotes/origin/" + cand):
            return cand
    die("无法确定目标分支：origin/HEAD 未设置，且本地与 origin 均无 main/master\n"
        "  请用 --target <分支名> 显式指定")


# ---------------------------------------------------------------- 远端状态

def push_state(node, src_ref):
    """取源分支的远端推送状态（只报事实，不判定该不该推送）。

    state 为状态键，是技能「推送源分支」表中处置规则的行键——**改键名须同步该表**；
    text 为面向读者的事实描述，二者一一对应。
    """
    if node["local_sha"] is None:
        return {"state": "remote-only", "upstream": None, "ahead": None, "behind": None,
                "text": "本地无同名分支，源分支直接取 origin/%s（%.8s）"
                        % (node["name"], node["remote_sha"])}

    # upstream 须用分支短名查（<全 ref>@{upstream} 会被 git 拒绝）；
    # for-each-ref 对无跟踪的分支输出空串，无需额外判错
    ok, out, _ = git_ok("for-each-ref", "--format=%(upstream:short)",
                        "refs/heads/" + node["name"])
    upstream = out.strip() if ok and out.strip() else None

    if upstream:
        ok2, out2, _ = git_ok("rev-list", "--left-right", "--count",
                              upstream + "..." + src_ref)
        if ok2:
            parts = out2.split()
            behind, ahead = int(parts[0]), int(parts[1])
            if ahead and behind:
                return {"state": "diverged", "upstream": upstream,
                        "ahead": ahead, "behind": behind,
                        "text": "已推送（upstream=%s）：本地领先 %d 个提交、落后 %d 个提交（与远端已分叉）"
                                % (upstream, ahead, behind)}
            if ahead:
                return {"state": "ahead", "upstream": upstream, "ahead": ahead, "behind": 0,
                        "text": "已推送但本地更新（upstream=%s）：本地领先 %d 个提交，未推送的提交不会出现在合并请求里"
                                % (upstream, ahead)}
            if behind:
                return {"state": "behind", "upstream": upstream, "ahead": 0, "behind": behind,
                        "text": "已推送（upstream=%s）：本地落后 %d 个提交" % (upstream, behind)}
            return {"state": "up-to-date", "upstream": upstream, "ahead": 0, "behind": 0,
                    "text": "已推送且与 upstream 一致（%s）" % upstream}
        return {"state": "pushed-unknown", "upstream": upstream, "ahead": None, "behind": None,
                "text": "已推送（upstream=%s），但本地与远端的领先/落后关系无法判定" % upstream}

    remote_ref = "refs/remotes/origin/" + node["name"]
    remote_sha = ref_sha(remote_ref)
    if remote_sha:
        if remote_sha == node["local_sha"]:
            return {"state": "pushed-no-tracking", "upstream": None, "ahead": 0, "behind": 0,
                    "text": "origin 上已有同名分支且提交一致，但本地未设置 upstream 跟踪"}
        return {"state": "pushed-diverged", "upstream": None, "ahead": None, "behind": None,
                "text": "origin 上已有同名分支但提交不一致（远端 %.8s / 本地 %.8s），"
                        "同名的合并请求可能已存在" % (remote_sha, node["local_sha"])}
    return {"state": "not-pushed", "upstream": None, "ahead": None, "behind": None,
            "text": "未推送到 origin（远端无该分支）——合并请求要求源分支已在远端"}


# ---------------------------------------------------------------- 平台与模板

def parse_remote(url):
    """解析 git remote URL 为 (host, owner/repo)；无法识别返回 (None, None)。"""
    u = (url or "").strip()
    host = path = None
    m = re.match(r"^[A-Za-z][A-Za-z0-9+.-]*://", u)
    if m:
        rest = u[m.end():]
        head, _, tail = rest.partition("/")
        if "@" in head:
            head = head.split("@", 1)[1]
        host, path = head, tail
    else:
        m = re.match(r"^(?:[^@/]+@)?([^:/]+):(.+)$", u)
        if m:
            host, path = m.group(1), m.group(2)
    if not host or not path:
        return None, None
    path = path.strip("/")
    if path.endswith(".git"):
        path = path[:-4]
    return host, path


def platform_info(repo_root):
    ok, out, _ = git_ok("remote", "get-url", "origin")
    url = out.strip() if ok else ""
    host, slug = parse_remote(url)
    hostname = (host or "").split(":")[0].lower()
    if hostname.endswith("github.com"):
        kind = "github"
    elif "gitlab" in hostname:
        kind = "gitlab"
    else:
        kind = "unknown"
    return {"url": url, "host": host, "slug": slug, "kind": kind,
            "clis": [c for c in ("gh", "glab") if shutil.which(c)]}


def compare_url(platform, source, target):
    """按平台给出「手工创建合并请求」的页面链接；未知平台返回 None。"""
    host, slug = platform["host"], platform["slug"]
    if not host or not slug:
        return None
    if platform["kind"] == "github":
        return "https://%s/%s/compare/%s...%s?expand=1" % (
            host, slug, quote(target, safe=""), quote(source, safe=""))
    if platform["kind"] == "gitlab":
        query = urlencode({"merge_request[source_branch]": source,
                           "merge_request[target_branch]": target})
        return "https://%s/%s/-/merge_requests/new?%s" % (host, slug, query)
    return None


def find_templates(repo_root):
    """探测仓库内的合并请求模板（只报路径）。

    大小写不敏感的文件系统（Windows / macOS）上，同一文件会被多条 pattern 命中，
    按 normcase 去重；大小写敏感的文件系统上二者是不同文件，各自保留。
    """
    found, seen = [], set()
    for pattern in (".github/PULL_REQUEST_TEMPLATE.md",
                    ".github/pull_request_template.md",
                    ".github/PULL_REQUEST_TEMPLATE/*.md",
                    "PULL_REQUEST_TEMPLATE.md",
                    ".gitlab/merge_request_templates/*.md"):
        for hit in sorted(glob.glob(os.path.join(repo_root, pattern))):
            key = os.path.normcase(os.path.abspath(hit))
            if key in seen:
                continue
            seen.add(key)
            found.append(os.path.relpath(hit, repo_root).replace(os.sep, "/"))
    return found


# ---------------------------------------------------------------- 变更范围

def group_changes(numstat_text):
    """按前两级目录聚合变更：返回 [(分组, 文件数, 新增行, 删除行)]，按文件数倒序。"""
    groups = {}
    for line in numstat_text.split("\n"):
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        added, deleted, path = parts[0], parts[1], parts[2]
        segs = path.split("/")
        if len(segs) >= 3:
            key = "/".join(segs[:2])
        elif len(segs) == 2:
            key = segs[0]
        else:
            key = "(仓库根)"
        g = groups.setdefault(key, [0, 0, 0])
        g[0] += 1
        g[1] += 0 if added == "-" else int(added)   # 二进制文件以 - 记
        g[2] += 0 if deleted == "-" else int(deleted)
    return sorted([(k, v[0], v[1], v[2]) for k, v in groups.items()],
                  key=lambda x: (-x[1], x[0]))


def safe_name(s):
    return re.sub(r"[^0-9A-Za-z._-]", "_", s)[:60]


# ---------------------------------------------------------------- 落盘

def render_material(ctx, max_diff_lines):
    commit_log, file_list, diff_text = ctx["commit_log"], ctx["file_list"], ctx["diff_text"]
    lines = []
    add = lines.append

    add("# 合并请求素材（脚本取数，描述由 agent 撰写）")
    add("")
    add("生成时间: %s" % ctx["generated_at"])
    add("")
    add("## 仓库与远端")
    add("- remote origin: %s" % (ctx["platform"]["url"] or "(未配置 origin)"))
    add("- 平台识别: %s   可用 CLI: %s"
        % (ctx["platform"]["kind"], " ".join(ctx["platform"]["clis"]) or "(无 gh / glab)"))
    add("- 仓库标识: %s" % (ctx["platform"]["slug"] or "(无法解析)"))
    add("")
    add("## 分支与差异")
    add("- 源分支: %s  ref=%s  sha=%s" % (
        ctx["source"]["name"], ctx["src_ref"], ctx["src_sha"][:12]))
    add("- 目标分支: %s  diff 基准=%s  sha=%s" % (
        ctx["target"]["name"], ctx["base_ref"], ctx["tgt_sha"][:12]))
    add("- 合并基点(merge-base): %s" % ctx["merge_base"][:12])
    add("- 领先提交数: %d   变更文件数: %d   %s"
        % (ctx["commits_ahead"], ctx["files_changed"], ctx["shortstat"] or "(无增删行)"))
    if ctx["target_note"]:
        add("- 提示: %s" % ctx["target_note"])
    add("")
    add("## 源分支推送状态")
    add("- 状态键: %s" % ctx["push"]["state"])
    add("- 事实: %s" % ctx["push"]["text"])
    add("- 依据: 本地 remote-tracking（未 fetch 时可能过期，先 `git fetch origin` 再重跑本脚本）")
    src = ctx["source"]
    if src["local_sha"] and src["remote_sha"] and src["local_sha"] != src["remote_sha"]:
        add("- 注意: 本地 %s 与 origin/%s 提交不一致（本地 %.8s / 远端 %.8s）——"
            "素材 diff 取本地分支，平台合并请求的 head 取 origin/%s"
            % (src["name"], src["name"], src["local_sha"], src["remote_sha"], src["name"]))
    add("")
    add("## 变更范围（按目录聚合）")
    if ctx["groups"]:
        for key, files, added, deleted in ctx["groups"]:
            add("- %s: %d 个文件  +%d -%d" % (key, files, added, deleted))
    else:
        add("- (无文件变更)")
    add("")
    add("## 提交记录（%s..%s，共 %d 个）" % (ctx["target"]["name"], ctx["source"]["name"],
                                      ctx["commits_ahead"]))
    add("")
    add(commit_log.strip() or "(无领先提交)")
    add("")
    add("## 文件清单（状态 路径）")
    add("")
    for ln in file_list:
        add(ln)
    add("")
    n_diff = diff_text.count("\n")
    truncated = n_diff > max_diff_lines
    add("## 差异（%d 行%s）" % (
        n_diff, "，此处前 %d 行，完整见 raw.diff" % max_diff_lines if truncated else ""))
    add("")
    if truncated:
        add("\n".join(diff_text.split("\n")[:max_diff_lines]))
        add("")
        add("... (已截断 %d 行，完整内容见 %s)" % (n_diff - max_diff_lines, ctx["raw_path"]))
    else:
        add(diff_text)
    add("")
    add("## 创建通道（参数以 CLI 实际 --help 为准）")
    if ctx["compare"]:
        add("- 手工创建页: %s" % ctx["compare"])
    else:
        add("- 未识别平台，请到代码托管页面手工创建")
    if "gh" in ctx["platform"]["clis"]:
        add("- gh: `gh pr create --base %s --head %s --title \"<标题>\" --body-file <描述文件>`"
            % (ctx["target"]["name"], ctx["source"]["name"]))
        add("  注: `--head` 会跳过 gh 的建分支/建 fork 交互，源分支未推送时会直接失败；"
            "先推送源分支再创建")
    if "glab" in ctx["platform"]["clis"]:
        add("- glab: `glab mr create --source-branch %s --target-branch %s --title \"<标题>\" "
            "--description-file <描述文件> --yes`"
            % (ctx["source"]["name"], ctx["target"]["name"]))
        add("  注: **不要用 `--fill`**（会顺带 push 分支并覆盖描述）；`--description-file` 不可用时"
            "退回 `-d \"$(cat <描述文件>)\"`")
    add("")
    add("## 模板文件")
    if ctx["templates"]:
        for t in ctx["templates"]:
            add("- %s" % t)
    else:
        add("- (未发现合并请求模板)")
    add("")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", default=None,
                    help="源分支名（默认当前所在分支；可带 origin/ 前缀）")
    ap.add_argument("--target", default=None,
                    help="目标分支名（默认依次探测 origin/HEAD → main → master）")
    ap.add_argument("--max-diff-lines", type=int, default=DEFAULT_MAX_DIFF_LINES,
                    help="素材中差异显示行数上限，默认 %d（raw.diff 始终完整）" % DEFAULT_MAX_DIFF_LINES)
    ap.add_argument("--out-dir", default=None,
                    help="素材输出目录（默认 <仓库根>/.tasks/mr-create）")
    args = ap.parse_args()

    ok, out, _ = git_ok("rev-parse", "--show-toplevel")
    if not ok:
        die("当前目录不是 git 仓库（或 git 不可用）")
    repo_root = out.strip()

    # ---- 分支解析
    if args.source:
        source = resolve_branch(args.source, "source")
    else:
        ok2, head, _ = git_ok("symbolic-ref", "--quiet", "--short", "HEAD")
        if not ok2:
            die("当前处于分离 HEAD 状态，无法推断源分支，请用 --source <分支名> 指定")
        source = resolve_branch(head.strip(), "source")
    src_ref = source["local_ref"] or source["remote_ref"]
    src_sha = ref_sha(src_ref)

    target_name = args.target or default_target_name()
    target = resolve_branch(target_name, "target")
    base_ref = target["remote_ref"] or target["local_ref"]
    tgt_sha = ref_sha(base_ref)

    target_note = ""
    if target["local_sha"] and target["remote_sha"]:
        if target["local_sha"] != target["remote_sha"]:
            target_note = ("本地 %s 与 origin/%s 不一致（本地 %.8s / 远端 %.8s）；"
                           "diff 以远端为准（远端才是合并请求的基线），必要时先 fetch 再重算"
                           % (target["name"], target["name"],
                              target["local_sha"], target["remote_sha"]))
    elif not target["remote_sha"] and args.target is None:
        target_note = "origin 无该分支，diff 以本地分支为准"

    # ---- 前置校验
    if src_sha == tgt_sha:
        die("源分支与目标分支指向同一提交（%.12s），无差异可合并\n"
            "  源: %s  目标: %s" % (src_sha, source["name"], target["name"]))

    ok2, _, _ = git_ok("merge-base", base_ref, src_ref)
    if not ok2:
        die("源分支与目标分支没有共同祖先（历史不相关），无法生成合并请求素材")

    commits_ahead = int(git("rev-list", "--count", base_ref + ".." + src_ref).strip() or "0")
    numstat = git("diff", "--numstat", base_ref + "..." + src_ref)
    name_status = git("diff", "--name-status", base_ref + "..." + src_ref)
    file_list = [ln for ln in name_status.split("\n") if ln.strip()]
    files_changed = len(file_list)

    if commits_ahead == 0 and files_changed == 0:
        die("源分支相对目标分支没有有效差异（无领先提交、无文件差异），不创建空合并请求\n"
            "  源: %s  目标: %s（diff 基准 %s）" % (source["name"], target["name"], base_ref))

    # ---- 取数
    merge_base = git("merge-base", base_ref, src_ref).strip()
    shortstat = git("diff", "--shortstat", base_ref + "..." + src_ref).strip()
    commit_log = git("log", "--pretty=medium", base_ref + ".." + src_ref, "--")
    diff_text = git("diff", base_ref + "..." + src_ref).strip()
    push = push_state(source, src_ref)
    platform = platform_info(repo_root)
    compare = compare_url(platform, source["name"], target["name"])
    templates = find_templates(repo_root)
    groups = group_changes(numstat)

    # ---- 落盘
    out_dir = os.path.abspath(args.out_dir or os.path.join(repo_root, ".tasks", "mr-create"))
    os.makedirs(out_dir, exist_ok=True)
    stem = "mr-%s-to-%s" % (safe_name(source["name"]), safe_name(target["name"]))
    mat_path = os.path.join(out_dir, stem + ".material.md")
    raw_path = os.path.join(out_dir, stem + ".raw.diff")

    ctx = {
        "generated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "source": source, "target": target, "src_ref": src_ref, "base_ref": base_ref,
        "src_sha": src_sha, "tgt_sha": tgt_sha, "merge_base": merge_base,
        "commits_ahead": commits_ahead, "files_changed": files_changed,
        "shortstat": shortstat, "target_note": target_note, "push": push,
        "platform": platform, "compare": compare, "templates": templates,
        "groups": groups, "commit_log": commit_log, "file_list": file_list,
        "diff_text": diff_text, "raw_path": raw_path,
    }
    with open(mat_path, "w", encoding="utf-8") as f:
        f.write(render_material(ctx, args.max_diff_lines))
    with open(raw_path, "w", encoding="utf-8") as f:
        f.write(diff_text)

    # 素材落在仓库内且未被忽略时提示勿提交（跨盘符等无法求相对路径的情况跳过）
    try:
        rel_out = os.path.relpath(out_dir, repo_root)
    except ValueError:
        rel_out = None
    outside = rel_out is None or rel_out == os.pardir or rel_out.startswith(os.pardir + os.sep) \
        or os.path.isabs(rel_out)
    unignored = bool(rel_out) and not outside and not git_ok("check-ignore", "-q", rel_out)[0]

    # ---- stdout
    print("OK  校验通过")
    print("    源分支:   %s  (%.8s)" % (source["name"], src_sha))
    print("    目标分支: %s  (%.8s)  diff 基准=%s" % (target["name"], tgt_sha, base_ref))
    print("    领先提交: %d   变更文件: %d   %s" % (commits_ahead, files_changed,
                                                shortstat or "(无增删行)"))
    print("    推送状态: %s — %s" % (push["state"], push["text"]))
    if source["local_sha"] and source["remote_sha"] and source["local_sha"] != source["remote_sha"]:
        print("    注意: 本地 %s 与 origin/%s 提交不一致（素材 diff 取本地分支，平台 head 取远端）"
              % (source["name"], source["name"]))
    print("    平台:     %s   可用 CLI: %s" % (platform["kind"],
                                            " ".join(platform["clis"]) or "(无)"))
    if commits_ahead and files_changed == 0:
        print("    注意: 有领先提交但无文件差异（空提交/仅合并），描述中请勿声称有代码改动")
    if templates:
        print("    模板:     %s" % " ".join(templates))
    if unignored:
        print("    注意: %s 未被 .gitignore 忽略，素材文件勿提交入库"
              % rel_out.replace(os.sep, "/") + "/")
    print("    素材: %s" % mat_path)
    print("    完整差异: %s" % raw_path)


if __name__ == "__main__":
    main()
