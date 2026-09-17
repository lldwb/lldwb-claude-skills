#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
mr-create 技能自测：逐项验证 prepare-mr.py 的校验分支、推送状态、平台识别与落盘渲染。

**改过 `scripts/prepare-mr.py` 必须重跑本脚本**（38 项用例覆盖各失败分支、六种推送状态、
平台识别与素材渲染）。其中 C36 校验脚本产出的状态键与 SKILL.md「推送源分支」表一一对应 ——
加/改状态键时若忘了同步表格，跑本脚本即可发现。

隔离性：每个用例都在系统临时目录内新建独立 git 仓库（含 bare 远端），不触碰调用者所在仓库。
跨盘符用例（C32）需要第二个可用盘符，本机不满足时记 SKIP（不计入失败）。

用法:
    python selftest.py        # 跑全部用例，逐项打印 PASS / FAIL / ERROR / SKIP
退出码: 0 = 无 FAIL / ERROR（允许 SKIP）；1 = 有失败项
"""
import os
import re
import string
import subprocess
import sys
import tempfile
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

# 自定位被测脚本（技能目录自包含，不依赖仓库位置与盘符）。
HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.join(HERE, "prepare-mr.py")
PY = sys.executable
RESULTS = []


class Skipped(Exception):
    """用例在本机不具备构造条件（如只有一个盘符），记 SKIP 而非失败。"""


def git(cwd, *args, check=True):
    r = subprocess.run(["git", "-c", "core.quotepath=false"] + list(args), cwd=cwd,
                       capture_output=True, encoding="utf-8", errors="replace")
    if check and r.returncode != 0:
        raise RuntimeError("git %s -> %s" % (" ".join(args), r.stderr.strip()[:400]))
    return r


def prepare(cwd, *args):
    return subprocess.run([PY, SKILL] + list(args), cwd=cwd, capture_output=True,
                          encoding="utf-8", errors="replace")


def new_repo(branch="main"):
    d = tempfile.mkdtemp(prefix="mrt-")
    git(d, "init", "-q")
    git(d, "symbolic-ref", "HEAD", "refs/heads/" + branch)
    git(d, "config", "user.name", "tester")
    git(d, "config", "user.email", "tester@example.com")
    git(d, "config", "commit.gpgsign", "false")
    return d


def make_bare():
    d = tempfile.mkdtemp(prefix="mrtbare-")
    git(d, "init", "-q", "--bare")
    git(d, "symbolic-ref", "HEAD", "refs/heads/main")
    return d


def write_commit(cwd, path, text, msg):
    full = os.path.join(cwd, path)
    parent = os.path.dirname(full)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(text)
    git(cwd, "add", "-A")
    git(cwd, "commit", "-q", "-m", msg)
    return full


def base_repo():
    """main 一个提交；feat 领先 1 个提交，未推送、无 origin。"""
    d = new_repo()
    write_commit(d, "a.txt", "a\n", "feat: 初始提交")
    git(d, "checkout", "-q", "-b", "feat")
    write_commit(d, "b.txt", "b\n", "feat: 新增 b")
    return d


def pushed_repo(extra=0):
    """带 bare origin：main 已推送，feat 领先 1+extra 个提交且已 push -u。"""
    d = new_repo()
    bare = make_bare()
    git(d, "remote", "add", "origin", bare)
    write_commit(d, "a.txt", "a\n", "feat: 初始提交")
    git(d, "push", "-q", "-u", "origin", "main")
    git(d, "checkout", "-q", "-b", "feat")
    write_commit(d, "b.txt", "b\n", "feat: 新增 b")
    for i in range(extra):
        write_commit(d, "e%d.txt" % i, "e\n", "feat: 追加 %d" % i)
    git(d, "push", "-q", "-u", "origin", "feat")
    return d, bare


def mat_path(d, src, tgt, out_dir=None):
    return os.path.join(out_dir or os.path.join(d, ".tasks", "mr-create"),
                        "mr-%s-to-%s.material.md" % (src, tgt))


def read_material(d, src, tgt, out_dir=None):
    with open(mat_path(d, src, tgt, out_dir), encoding="utf-8") as f:
        return f.read()


def expect_ok(r):
    assert r.returncode == 0, "期望成功，实际退出码 %d\nSTDOUT:\n%s\nSTDERR:\n%s" % (
        r.returncode, r.stdout, r.stderr)


def expect_fail(r, keyword):
    assert r.returncode != 0, "期望非零退出，实际成功\nSTDOUT:\n%s" % r.stdout
    blob = r.stdout + r.stderr
    assert keyword in blob, "输出中未包含 %r：\n%s" % (keyword, blob)


def case(name):
    def deco(fn):
        try:
            fn()
            RESULTS.append((name, "PASS", ""))
        except Skipped as e:
            RESULTS.append((name, "SKIP", str(e).strip() or "本机不具备构造条件"))
        except AssertionError as e:
            RESULTS.append((name, "FAIL", str(e).strip()))
        except Exception as e:
            RESULTS.append((name, "ERROR", "%s: %s" % (type(e).__name__, str(e)[:300])))
    return deco


# ------------------------------------------------------------ 前置校验（失败路径）

@case("C01 非 git 仓库 -> 报错退出")
def _():
    expect_fail(prepare(tempfile.mkdtemp(prefix="mrt-")), "不是 git 仓库")


@case("C02 源分支不存在 -> 报错退出")
def _():
    d = new_repo()
    write_commit(d, "a.txt", "a\n", "init")
    expect_fail(prepare(d, "--source", "nope", "--target", "main"), "分支不存在")


@case("C03 --source 传提交号 -> 提示需传分支名")
def _():
    d = base_repo()
    sha = git(d, "rev-parse", "HEAD").stdout.strip()[:8]
    expect_fail(prepare(d, "--source", sha, "--target", "main"), "需传分支名")


@case("C04 源与目标同一提交 -> 报错退出")
def _():
    d = new_repo()
    write_commit(d, "a.txt", "a\n", "init")
    expect_fail(prepare(d, "--source", "main", "--target", "main"), "同一提交")


@case("C05 无共同祖先 -> 报错退出")
def _():
    d = new_repo()
    write_commit(d, "a.txt", "a\n", "init")
    git(d, "checkout", "-q", "--orphan", "orphan")
    git(d, "rm", "-rf", "-q", ".")
    write_commit(d, "z.txt", "z\n", "orphan init")
    expect_fail(prepare(d, "--source", "orphan", "--target", "main"), "没有共同祖先")


@case("C06 源分支落后（无有效差异）-> 报错退出")
def _():
    d = new_repo()
    write_commit(d, "a.txt", "a\n", "init")
    git(d, "checkout", "-q", "-b", "old")
    git(d, "checkout", "-q", "main")
    write_commit(d, "c.txt", "c\n", "main 前进")
    expect_fail(prepare(d, "--source", "old", "--target", "main"), "没有有效差异")


@case("C07 分离 HEAD 且未指定源分支 -> 报错退出")
def _():
    d = new_repo()
    write_commit(d, "a.txt", "a\n", "init")
    write_commit(d, "b.txt", "b\n", "second")
    git(d, "checkout", "-q", "HEAD~1")
    expect_fail(prepare(d), "分离 HEAD")


@case("C08 无 origin/HEAD 且无 main/master -> 目标分支探测失败")
def _():
    d = new_repo(branch="trunk")
    write_commit(d, "a.txt", "a\n", "init")
    git(d, "checkout", "-q", "-b", "feat")
    write_commit(d, "b.txt", "b\n", "feat")
    expect_fail(prepare(d), "无法确定目标分支")


# ------------------------------------------------------------ 正常路径与推送状态

@case("C09 默认解析（源=当前分支，目标=main）+ 未推送")
def _():
    d = base_repo()
    r = prepare(d)
    expect_ok(r)
    assert "OK  校验通过" in r.stdout, r.stdout
    assert "未推送到 origin" in r.stdout, r.stdout
    assert "领先提交: 1" in r.stdout, r.stdout
    mat = read_material(d, "feat", "main")
    assert "状态键: not-pushed" in mat, mat[:900]
    assert "git push -u origin feat" not in mat, "素材不再代出推送命令（处置规则单点定义在 SKILL.md 表格）"
    assert "## 变更范围（按目录聚合）" in mat


@case("C10 --source 带 origin/ 前缀可解析为分支短名")
def _():
    d, _bare = pushed_repo()
    r = prepare(d, "--source", "origin/feat", "--target", "main")
    expect_ok(r)
    assert "源分支:   feat" in r.stdout, r.stdout


@case("C11 空提交（有领先提交无文件差异）-> OK 且提示")
def _():
    d = new_repo()
    write_commit(d, "a.txt", "a\n", "init")
    git(d, "checkout", "-q", "-b", "feat")
    git(d, "commit", "-q", "--allow-empty", "-m", "chore: 空提交")
    r = prepare(d)
    expect_ok(r)
    assert "有领先提交但无文件差异" in r.stdout, r.stdout
    assert "(无文件变更)" in read_material(d, "feat", "main")


@case("C12 推送状态：已推送且 upstream 一致")
def _():
    d, _bare = pushed_repo()
    r = prepare(d)
    expect_ok(r)
    assert "已推送且与 upstream 一致" in r.stdout, r.stdout
    assert "推送状态: up-to-date" in r.stdout, r.stdout
    mat = read_material(d, "feat", "main")
    assert "git push -u origin feat" not in mat, "已一致时不应给出推送指引"
    assert "状态键: up-to-date" in mat, mat[-900:]


@case("C13 推送状态：本地领先（未推送的提交）")
def _():
    d, _bare = pushed_repo()
    write_commit(d, "c.txt", "c\n", "feat: 本地新增")
    r = prepare(d)
    expect_ok(r)
    assert "已推送但本地更新" in r.stdout, r.stdout


@case("C14 推送状态：本地落后")
def _():
    d, _bare = pushed_repo(extra=1)
    git(d, "reset", "-q", "--hard", "HEAD~1")
    r = prepare(d)
    expect_ok(r)
    assert "本地落后 1 个提交" in r.stdout, r.stdout


@case("C15 推送状态：与远端已分叉")
def _():
    d, bare = pushed_repo()
    other = tempfile.mkdtemp(prefix="mrtother-")
    git(other, "clone", "-q", bare, other)
    git(other, "config", "user.email", "t2@example.com")
    git(other, "config", "user.name", "t2")
    git(other, "checkout", "-q", "feat")
    write_commit(other, "c.txt", "c\n", "feat: 远端新增")
    git(other, "push", "-q", "origin", "feat")
    git(d, "fetch", "-q", "origin")
    write_commit(d, "d.txt", "d\n", "feat: 本地新增")
    r = prepare(d)
    expect_ok(r)
    assert "与远端已分叉" in r.stdout, r.stdout


@case("C16 推送状态：origin 同名分支提交不一致（无 upstream）")
def _():
    d, _bare = pushed_repo()
    git(d, "branch", "--unset-upstream")
    write_commit(d, "c.txt", "c\n", "feat: 本地新增")
    r = prepare(d)
    expect_ok(r)
    assert "提交不一致" in r.stdout and "可能已存在" in r.stdout, r.stdout


@case("C17 推送状态：origin 同名分支提交一致但无 upstream")
def _():
    d, _bare = pushed_repo()
    git(d, "branch", "--unset-upstream")
    r = prepare(d)
    expect_ok(r)
    assert "本地未设置 upstream 跟踪" in r.stdout, r.stdout


@case("C18 推送状态：仅远端有分支（本地已删）")
def _():
    d, _bare = pushed_repo()
    git(d, "checkout", "-q", "main")
    git(d, "branch", "-q", "-D", "feat")
    r = prepare(d, "--source", "feat", "--target", "main")
    expect_ok(r)
    assert "本地无同名分支" in r.stdout, r.stdout


@case("C19 目标分支基线取远端 + 本地/远端不一致提示")
def _():
    d, _bare = pushed_repo()
    git(d, "checkout", "-q", "main")
    write_commit(d, "m.txt", "m\n", "feat: main 本地前进")
    git(d, "checkout", "-q", "feat")
    r = prepare(d)
    expect_ok(r)
    mat = read_material(d, "feat", "main")
    assert "本地 main 与 origin/main 不一致" in mat, mat[:900]
    assert "diff 基准=refs/remotes/origin/main" in mat, mat[:900]


# ------------------------------------------------------------ 平台 / 模板 / 落盘

@case("C20 平台识别 github + compare 链接")
def _():
    d = base_repo()
    git(d, "remote", "add", "origin", "https://github.com/owner/repo.git")
    r = prepare(d)
    expect_ok(r)
    assert "平台:     github" in r.stdout, r.stdout
    mat = read_material(d, "feat", "main")
    assert "https://github.com/owner/repo/compare/main...feat?expand=1" in mat, mat[:900]


@case("C21 平台识别 gitlab + mr new 链接")
def _():
    d = base_repo()
    git(d, "remote", "add", "origin", "git@gitlab.example.com:group/proj.git")
    r = prepare(d)
    expect_ok(r)
    assert "平台:     gitlab" in r.stdout, r.stdout
    mat = read_material(d, "feat", "main")
    assert "merge_request%5Bsource_branch%5D=feat" in mat, mat[:900]
    assert "merge_request%5Btarget_branch%5D=main" in mat, mat[:900]


@case("C22 平台识别 unknown -> 未识别平台提示")
def _():
    d, _bare = pushed_repo()
    r = prepare(d)
    expect_ok(r)
    assert "平台:     unknown" in r.stdout, r.stdout
    assert "未识别平台" in read_material(d, "feat", "main")


@case("C23 模板探测（大小写不敏感须去重只报一次）")
def _():
    d = base_repo()
    p = os.path.join(d, ".github")
    os.makedirs(p, exist_ok=True)
    with open(os.path.join(p, "pull_request_template.md"), "w", encoding="utf-8") as f:
        f.write("## 背景\n")
    r = prepare(d)
    expect_ok(r)
    mat = read_material(d, "feat", "main")
    assert mat.lower().count("pull_request_template.md") == 1, mat[-600:]


@case("C23b 多模板探测（嵌套目录 + 仓库根）")
def _():
    d = base_repo()
    write_commit(d, ".github/PULL_REQUEST_TEMPLATE/feature.md", "## 背景\n", "chore: 模板 1")
    write_commit(d, "PULL_REQUEST_TEMPLATE.md", "## 背景\n", "chore: 模板 2")
    r = prepare(d)
    expect_ok(r)
    assert ".github/PULL_REQUEST_TEMPLATE/feature.md" in r.stdout, r.stdout
    assert "PULL_REQUEST_TEMPLATE.md" in r.stdout, r.stdout


@case("C24 默认落盘到 <仓库根>/.tasks/mr-create/（子目录调用亦然）")
def _():
    d = base_repo()
    sub = os.path.join(d, "sub", "deep")
    os.makedirs(sub)
    r = prepare(sub)
    expect_ok(r)
    assert os.path.exists(mat_path(d, "feat", "main")), r.stdout


@case("C25 --out-dir 覆盖 + 未忽略目录提示")
def _():
    d = base_repo()
    out = os.path.join(d, "docs")
    os.makedirs(out)
    r = prepare(d, "--out-dir", out)
    expect_ok(r)
    assert "未被 .gitignore 忽略" in r.stdout, r.stdout
    assert os.path.exists(mat_path(d, "feat", "main", out))


@case("C26 已忽略目录不提示")
def _():
    d = base_repo()
    write_commit(d, ".gitignore", ".tasks/\n", "chore: 忽略产物")
    r = prepare(d)
    expect_ok(r)
    assert "未被 .gitignore 忽略" not in r.stdout, r.stdout


@case("C27 diff 截断 + raw.diff 完整")
def _():
    d = new_repo()
    write_commit(d, "a.txt", "x\n" * 10, "init")
    git(d, "checkout", "-q", "-b", "feat")
    write_commit(d, "a.txt", "y\n" * 200, "feat: 大改")
    r = prepare(d, "--max-diff-lines", "20")
    expect_ok(r)
    mat = read_material(d, "feat", "main")
    assert "已截断" in mat, mat[:600]
    raw = os.path.join(d, ".tasks", "mr-create", "mr-feat-to-main.raw.diff")
    assert sum(1 for _ in open(raw, encoding="utf-8")) > 200


@case("C28 变更范围按前两级目录聚合")
def _():
    d = new_repo()
    write_commit(d, "a.txt", "a\n", "init")
    git(d, "checkout", "-q", "-b", "feat")
    write_commit(d, "skills/mr-create/x.md", "x\n", "feat: 1")
    write_commit(d, "docs/a.md", "a\n", "feat: 2")
    write_commit(d, "top.txt", "t\n", "feat: 3")
    r = prepare(d)
    expect_ok(r)
    mat = read_material(d, "feat", "main")
    assert "- skills/mr-create: 1 个文件" in mat, mat[:900]
    assert "- docs: 1 个文件" in mat, mat[:900]
    assert "- (仓库根): 1 个文件" in mat, mat[:900]


@case("C29 分支名含中文/斜杠 -> 素材文件名安全")
def _():
    d = base_repo()
    git(d, "checkout", "-q", "-b", "特性/中文-测试", "main")
    write_commit(d, "c.txt", "c\n", "feat: 中文分支")
    r = prepare(d, "--source", "特性/中文-测试", "--target", "main")
    expect_ok(r)
    out = os.path.join(d, ".tasks", "mr-create")
    names = os.listdir(out)
    assert names, r.stdout
    for n in names:
        assert all(ch.isascii() and (ch.isalnum() or ch in "._-") for ch in n), names


@case("C30 空仓库（无任何提交）-> 报错退出")
def _():
    d = new_repo()
    expect_fail(prepare(d), "分支不存在")


@case("C31 提交正文写入素材（--pretty=medium）")
def _():
    d = new_repo()
    write_commit(d, "a.txt", "a\n", "init")
    git(d, "checkout", "-q", "-b", "feat")
    with open(os.path.join(d, "b.txt"), "w", encoding="utf-8") as f:
        f.write("b\n")
    git(d, "add", "-A")
    git(d, "commit", "-q", "-m", "feat: 新增 b", "-m", "正文：说明改动动机与影响面。")
    r = prepare(d)
    expect_ok(r)
    mat = read_material(d, "feat", "main")
    assert "正文：说明改动动机与影响面。" in mat, mat[:1200]


@case("C32 --out-dir 跨盘符（relpath 不可求）不误报未忽略")
def _():
    d = base_repo()
    drive = os.path.splitdrive(os.path.abspath(d))[0].upper()
    others = [c + ":" for c in string.ascii_uppercase
              if c + ":" != drive and os.path.exists(c + ":\\")]
    if not others:
        raise Skipped("本机只有 %s 一个盘符，构造不出跨盘符场景" % drive)
    try:
        out = tempfile.mkdtemp(prefix="mrtx-", dir=others[0] + os.sep)
    except OSError as e:
        raise Skipped("在 %s 盘建临时目录失败：%s" % (others[0], e))
    r = prepare(d, "--out-dir", out)
    expect_ok(r)
    assert "未被 .gitignore 忽略" not in r.stdout, r.stdout
    assert os.path.exists(mat_path(d, "feat", "main", out))
    print("       [证据] 仓库在 %s 盘、产出在 %s 盘，relpath 跨盘符不误报" % (drive, others[0]))


@case("C33 --target 指定的分支不存在 -> 报错退出")
def _():
    d = base_repo()
    expect_fail(prepare(d, "--source", "feat", "--target", "nobranch"), "分支不存在")


def advance_remote(bare, name="feat"):
    """另克隆一份推进远端分支（模拟他人推送），使调用方的 remote-tracking 变陈旧。"""
    other = tempfile.mkdtemp(prefix="mrtother-")
    git(other, "clone", "-q", bare, other)
    git(other, "config", "user.email", "t2@example.com")
    git(other, "config", "user.name", "t2")
    git(other, "checkout", "-q", name)
    write_commit(other, "c.txt", "c\n", "feat: 远端新增")
    git(other, "push", "-q", "origin", name)


@case("C34 remote-only：素材给状态键、不给推送指引（该 push 必然失败）")
def _():
    d, _bare = pushed_repo()
    git(d, "checkout", "-q", "main")
    git(d, "branch", "-q", "-D", "feat")
    r = prepare(d, "--source", "feat", "--target", "main")
    expect_ok(r)
    assert "本地无同名分支" in r.stdout, r.stdout
    assert "推送状态: remote-only" in r.stdout, r.stdout
    mat = read_material(d, "feat", "main")
    assert "状态键: remote-only" in mat, mat[-900:]
    assert "git push -u origin feat" not in mat, "不应给出该状态下必然失败的推送指引"
    p = git(d, "push", "-u", "origin", "feat", check=False)
    print("       [证据] git push -u origin feat -> rc=%d  %s"
          % (p.returncode, (p.stderr or p.stdout).strip().splitlines()[:1]))
    assert p.returncode != 0, "期望该命令失败（本地无该分支），实际成功"


@case("C35 未 fetch 时状态可能过期：素材标注依据（故技能要求取数前先 fetch）")
def _():
    d, bare = pushed_repo()
    advance_remote(bare)
    write_commit(d, "d.txt", "d\n", "feat: 本地新增")
    r = prepare(d)
    expect_ok(r)
    assert "推送状态: ahead" in r.stdout, r.stdout
    assert "未 fetch 时可能过期" in read_material(d, "feat", "main"), read_material(d, "feat", "main")[-900:]
    git(d, "fetch", "-q", "origin")
    r2 = prepare(d)
    expect_ok(r2)
    assert "推送状态: diverged" in r2.stdout, r2.stdout
    print("       [证据] 未 fetch 报 ahead，fetch 后报 diverged")


@case("C36 状态键与 SKILL.md「推送源分支」表一致（改键名须同步表格）")
def _():
    with open(SKILL, encoding="utf-8") as f:
        src = f.read()
    keys = sorted(set(re.findall(r'"state":\s*"([a-z-]+)"', src)))
    assert keys, "未从脚本解析到状态键"
    skill_md = os.path.join(os.path.dirname(os.path.dirname(SKILL)), "SKILL.md")
    with open(skill_md, encoding="utf-8") as f:
        doc = f.read()
    missing = [k for k in keys if "`%s`" % k not in doc]
    assert not missing, "SKILL.md 表格缺少状态键: %s" % missing
    print("       [证据] 脚本状态键 %d 个，SKILL.md 全部覆盖: %s" % (len(keys), " ".join(keys)))


@case("C37 源分支本地与远端不一致时素材给出提示")
def _():
    d, _bare = pushed_repo()
    write_commit(d, "c.txt", "c\n", "feat: 本地新增")
    r = prepare(d)
    expect_ok(r)
    mat = read_material(d, "feat", "main")
    assert "本地 feat 与 origin/feat 提交不一致" in mat, mat[-900:]
    assert "素材 diff 取本地分支，平台合并请求的 head 取 origin/feat" in mat, mat[-900:]


# ------------------------------------------------------------ 汇总
print("=" * 72)
for name, status, detail in RESULTS:
    print("%-6s %s" % (status, name))
    if detail:
        for ln in detail.splitlines():
            print("       | %s" % ln)
print("=" * 72)
n_skip = sum(1 for _, s, _ in RESULTS if s == "SKIP")
n_bad = sum(1 for _, s, _ in RESULTS if s in ("FAIL", "ERROR"))
print("合计 %d 项：PASS %d / SKIP %d / 失败 %d"
      % (len(RESULTS), len(RESULTS) - n_skip - n_bad, n_skip, n_bad))
sys.exit(1 if n_bad else 0)
