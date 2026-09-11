#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志取数脚本（通用，Kibana internal search API）。
只负责按 trace_id + 时间窗拉取并解析日志，不做 bug 判定（判定由调用方 agent 完成）。

多环境: 通过 --env <环境名> 选择（缺省取配置 default_env）。
config 结构: { "default_env": "prod", "environments": { "<env>": { kibana / index_pattern / ... } } }

用法:
    python log-diagnose.py <trace_id> [time] [--env test] [--config <path>] [--out-dir <path>]
    python log-diagnose.py --list-envs [--config <path>]
    time 示例:
      相对: 15h / 30d / 7w / 10m / now-15h / 纯数字(天)
      固定: from~to，如 2026-08-31T10:50:00~2026-08-31T10:52:00
            (ISO 无时区默认 +08:00 即 CST，与日志本地时间一致；单边可写 now)
      缺省走配置 default_days

输出（写到 --out-dir/<env>/<trace_id>.*）:
    <trace_id>.raw.json   原始命中(_source 数组，按 @timestamp 升序)
    <trace_id>.summary.txt 人类可读时序摘要 + 全量 ERROR 消息
stdout: 命中数 / 时间范围 / 输出路径
"""
import sys
import os
import json
import time
import re
import argparse
import urllib.request
import urllib.error
import base64
import codecs

# Windows 控制台缺省 GBK，强制 UTF-8 输出环境中文名。
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
from datetime import datetime, timezone


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CONFIG = os.path.join(SCRIPT_DIR, "..", "log-diagnose.config.json")
GLOBAL_OUT_DIR = os.path.join(os.path.expanduser("~"), ".claude", ".tasks", "log-diagnosis")
CONFIG_FILENAME = "log-diagnose.config.json"


def find_project_config():
    """从当前工作目录向上逐级查找项目级配置 <项目根>/.claude/<CONFIG_FILENAME>，命中返回路径，否则 None。
    项目级配置优先于 skill 全局默认，实现不同项目不同 Kibana 环境的切换。"""
    d = os.getcwd()
    while True:
        cand = os.path.join(d, ".claude", CONFIG_FILENAME)
        if os.path.exists(cand):
            return cand
        parent = os.path.dirname(d)
        if parent == d:
            return None
        d = parent
    return None


def resolve_out_root(cfg_path, cfg_src, out_dir_arg):
    """按配置来源决定输出根：--out-dir 显式 > 显式配置(下载目录) > 项目级(项目路径) > 全局(~/.claude)。"""
    if out_dir_arg:
        return os.path.abspath(out_dir_arg)
    if cfg_src == "explicit":
        return os.path.join(os.path.expanduser("~"), "Downloads")
    if cfg_src == "project":
        proj_root = os.path.dirname(os.path.dirname(os.path.abspath(cfg_path)))
        return os.path.join(proj_root, ".tasks", "log-diagnosis")
    return GLOBAL_OUT_DIR


def out_dir(base, env):
    return os.path.join(base, env)


def die(msg, code=1):
    print("ERROR: " + msg, file=sys.stderr)
    sys.exit(code)


def load_config(config_path):
    if not os.path.exists(config_path):
        die("配置文件不存在: %s\n请创建它，schema:\n%s" % (
            config_path, json.dumps({
                "default_env": "prod",
                "environments": {
                    "prod": {
                        "name": "生产环境",
                        "kibana": {"host": "http://<ip>:5601", "username": "elastic", "password": "..."},
                        "index_pattern": "filebeat-app-prod-*", "default_days": 30,
                        "max_hits": 2000, "page_size": 300
                    },
                    "test": {
                        "name": "测试环境",
                        "kibana": {"host": "http://<ip>:5601", "username": "elastic", "password": "..."},
                        "index_pattern": "filebeat-app-test-*", "default_days": 30,
                        "max_hits": 2000, "page_size": 300
                    }
                }
            }, indent=2, ensure_ascii=False)))
    with open(config_path, "r", encoding="utf-8-sig") as f:
        return json.load(f)


def list_environments(cfg):
    """列出可用环境。兼容旧的单环境平铺结构。"""
    if "environments" in cfg:
        for key, env in cfg["environments"].items():
            name = env.get("name", "")
            kib = env.get("kibana", {})
            print("%s\t%s\t%s" % (key, name, kib.get("host", "")))
    else:
        print("prod\t%s\t%s" % (cfg.get("name", ""), cfg.get("kibana", {}).get("host", "")))
    if "default_env" in cfg:
        print("默认环境: %s" % cfg["default_env"])


def resolve_env(cfg, env_name=None):
    """解析环境配置。env_name 缺省取 default_env。
    兼容旧平铺结构: 无 environments 键时按单环境 prod 处理。"""
    if "environments" not in cfg:
        if env_name not in (None, "prod", ""):
            die("旧版平铺配置仅含单环境 prod，不支持 --env %s（请改用 environments 结构）" % env_name)
        return dict(cfg), "prod"
    envs = cfg["environments"]
    if not env_name or env_name == "":
        env_name = cfg.get("default_env", "prod")
    if env_name not in envs:
        die("未知环境 '%s'，可用: %s" % (env_name, ", ".join(envs.keys())))
    return dict(envs[env_name]), env_name


ISO_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")
TZ_RE = re.compile(r"(Z$|[+-]\d{2}:?\d{2}$)")


def _norm_side(side, default_days):
    """归一化时间端点为 ES 可接受值。无时区的 ISO 默认按 +08:00 (CST，与日志本地时间一致)。"""
    side = side.strip()
    if side == "" or side == "now":
        return "now"
    if side.startswith("now-") or side.startswith("now/"):
        return side
    if len(side) >= 2 and side[-1] in "hdwm" and side[:-1].isdigit():
        return "now-" + side
    if side.isdigit():
        return "now-%sd" % side
    if ISO_RE.match(side):
        if side.endswith("Z") or TZ_RE.search(side):
            return side
        if "T" not in side:
            return side + "T00:00:00+08:00"
        return side + "+08:00"
    die("无法识别时间 '%s'，应为 Nh/Nd/Nw/Nm、now-15h、ISO(2026-08-31T10:50:00) 或 from~to" % side)


def parse_time_window(time_arg, default_days):
    """返回 (gte, lte)。支持相对(15h/30d/7w/10m/now-15h)、纯数字(天)、ISO 固定时间、from~to 固定区间。"""
    if not time_arg:
        return ("now-%dd" % default_days, "now")
    t = time_arg.strip()
    if "~" in t:
        frm, to = t.split("~", 1)
        return (_norm_side(frm, default_days), _norm_side(to, default_days))
    return (_norm_side(t, default_days), "now")


def logger_of(message):
    """从日志行 '[date tz LVL] trace span LOGGER  rest' 提取 logger 类名(第3个非空token)。"""
    try:
        after = message.split("] ", 1)[1]
        skipped = 0
        for tok in after.split(" "):
            if tok == "":
                continue
            skipped += 1
            if skipped == 3:
                return tok
        return ""
    except Exception:
        return ""


def build_query(kws, gte, lte, size):
    """构造 ES 查询体。单关键词保留原 trace_id 语义(should on message|trace_id)；
    多关键词按 AND(must) 匹配 message。
    注意: 不能用 _id 排序做 tie-breaker——部分集群禁用 _id fielddata（会致 2 分片失败、total=0）。
    改为 @timestamp 降序取最新 max_hits 条，调用方再反转为正序。超 max_hits 截断最早部分。"""
    query = {
        "bool": {
            "should": [
                {"match_phrase": {"message": kws[0]}},
                {"match_phrase": {"trace_id": kws[0]}},
            ],
            "minimum_should_match": 1,
            "filter": [{"range": {"@timestamp": {"gte": gte, "lte": lte}}}],
        }
    }
    if len(kws) > 1:
        # 多关键词场景忽略 trace_id 字段，仅按 message 全部命中(AND)
        query = {
            "bool": {
                "must": [{"match_phrase": {"message": kw}} for kw in kws],
                "filter": [{"range": {"@timestamp": {"gte": gte, "lte": lte}}}],
            }
        }
    return {
        "size": size,
        "query": query,
        "sort": [{"@timestamp": {"order": "desc"}}],
        "_source": ["message", "log_level", "@timestamp", "thread_name",
                    "trace_id", "host.name"],
    }


def search_es(cfg, kws, gte, lte):
    """单次 /internal/search/es（已验证的单 params 格式；batch 格式会忽略 body）。"""
    host = cfg["kibana"]["host"]
    if host.lower().startswith("http://"):
        print("警告: Kibana 地址为 http://，Basic 认证凭据（base64）将明文传输；"
              "生产环境建议改用 https://", file=sys.stderr)
    body = {
        "params": {
            "index": cfg["index_pattern"],
            "body": build_query(kws, gte, lte, cfg.get("max_hits", 2000)),
        }
    }
    data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    url = host.rstrip("/") + "/internal/search/es"
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("kbn-xsrf", "true")
    cred = "%s:%s" % (cfg["kibana"]["username"], cfg["kibana"]["password"])
    req.add_header("Authorization", "Basic " + base64.b64encode(cred.encode("utf-8")).decode("ascii"))
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        body_txt = e.read().decode("utf-8", errors="replace")
        die("ES 返回 HTTP %s: %s" % (e.code, body_txt[:1000]))
    except urllib.error.URLError as e:
        die("无法连接 Kibana: %s" % e.reason)
    try:
        obj = json.loads(raw)
    except Exception:
        die("响应非 JSON: %s" % raw[:500])
    if "rawResponse" not in obj:
        die("响应缺少 rawResponse: %s" % raw[:1000])
    resp = obj["rawResponse"]
    tot = resp.get("hits", {}).get("total")
    total = tot.get("value") if isinstance(tot, dict) else tot
    page = resp.get("hits", {}).get("hits", [])
    page.reverse()  # desc -> 正序
    return page, total


def slugify(text):
    """文件名安全化：替换 Windows 非法字符与空白，限制长度。"""
    s = re.sub(r'[\\/:*?"<>|\s]+', "_", text)
    return s[:80].rstrip("._")


def write_outputs(out_dir, name, display, hits, total, gte, lte):
    os.makedirs(out_dir, exist_ok=True)
    raw_path = os.path.join(out_dir, name + ".raw.json")
    sum_path = os.path.join(out_dir, name + ".summary.txt")

    with open(raw_path, "w", encoding="utf-8") as f:
        json.dump([h.get("_source", {}) for h in hits], f, ensure_ascii=False, indent=1)

    lines = []
    lines.append("query=%s  total_matched=%s  returned=%d  window_gte=%s  lte=%s"
                 % (display, total, len(hits), gte, lte))
    if isinstance(total, int) and total > len(hits):
        lines.append("WARNING: 命中 %d 超过 max_hits %d，已按 @timestamp 降序保留最新部分，最早 %d 条被截断。"
                     % (total, len(hits), total - len(hits)))
    lines.append("")
    lines.append("=== 时序摘要 (ts | level | logger | msg头) ===")
    errors = []
    for h in hits:
        s = h.get("_source", {})
        ts = s.get("@timestamp", "")
        lvl = s.get("log_level", "")
        msg = s.get("message", "")
        logger = logger_of(msg)
        head = msg.replace("\r", " ").replace("\n", " ")
        head = head[:240]
        lines.append("[%s] %s | %s | %s" % (ts, lvl, logger, head))
        if str(lvl).upper() == "ERROR":
            errors.append((ts, logger, msg))
    lines.append("")
    lines.append("=== 全量 ERROR 消息 ===")
    for ts, logger, msg in errors:
        lines.append("---- [%s] %s ----" % (ts, logger))
        lines.append(msg)
        lines.append("")
    with open(sum_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return raw_path, sum_path


TIME_PATTERN = re.compile(r"^\d+[hdwm]$|^now([/-]\d+[hdwm]?|$)|\d{4}-\d{2}-\d{2}|~")


def main():
    ap = argparse.ArgumentParser(description="日志取数：trace_id 或关键词(AND) + 时间窗。")
    ap.add_argument("trace_id", nargs="?", default=None,
                    help="MDC trace_id（与 --kw 同时给出时按 AND 组合）")
    ap.add_argument("time", nargs="?", default=None,
                    help="Nh/Nd/Nw/Nm / now-15h / ISO(2026-08-31T10:50:00) / from~to；缺省走配置 default_days")
    ap.add_argument("--env", default=None, help="环境名(如 prod/test)，缺省走配置 default_env")
    ap.add_argument("--list-envs", action="store_true", help="列出可用环境后退出")
    ap.add_argument("--config", default=None,
                    help="配置文件路径；缺省按优先级查找: 项目级 .claude/%s（当前目录向上）→ skill 同级默认" % CONFIG_FILENAME)
    ap.add_argument("--out-dir", default=None,
                    help="输出根目录；缺省按配置来源: 显式 --config→下载目录, 项目级配置→项目路径, 全局默认→~/.claude")
    ap.add_argument("--kw", action="append", default=[], dest="kws",
                    help="关键词，可多次指定，全部按 AND 命中的快照；仅 trace_id 时兼容原语义")
    ap.add_argument("--time", "--t", dest="time_opt", default=None,
                    help="显式指定时间窗（推荐），避免与 trace_id 位置歧义")
    args = ap.parse_args()

    proj_cfg = find_project_config()
    cfg_path = args.config or proj_cfg or DEFAULT_CONFIG
    cfg_src = "explicit" if args.config else ("project" if proj_cfg else "default")
    cfg = load_config(cfg_path)
    if args.list_envs:
        list_environments(cfg)
        return

    # 位置参数歧义消解：trace_id 位置若像时间，则视为 time（便于 --kw 与时间混排）
    time_arg = args.time_opt or args.time
    trace_id = args.trace_id
    if time_arg is None and trace_id and TIME_PATTERN.search(trace_id):
        time_arg = trace_id
        trace_id = None

    if not trace_id and not args.kws:
        ap.error("至少提供一个 trace_id 或 --kw 关键词")
    env_cfg, env = resolve_env(cfg, args.env)
    gte, lte = parse_time_window(time_arg, env_cfg.get("default_days", 30))

    kws = list(args.kws)
    if trace_id:
        kws.insert(0, trace_id)
    display = " | ".join(kws)
    name = slugify(display)
    t0 = time.time()
    hits, total = search_es(env_cfg, kws, gte, lte)
    elapsed = time.time() - t0
    if not hits:
        print("无日志命中: env=%s, query=%s, 时间窗 %s..%s" % (env, display, gte, lte))
        print("提示: 确认关键词/时间窗；该组合可能未落 %s 日志。" % env)
        return
    outdir = out_dir(resolve_out_root(cfg_path, cfg_src, args.out_dir), env)
    raw_path, sum_path = write_outputs(outdir, name, display, hits, total, gte, lte)
    print("OK  env=%s  query=%s" % (env, display))
    print("    时间窗: %s .. %s" % (gte, lte))
    print("    命中: %s (返回 %d)  耗时 %.1fs" % (total, len(hits), elapsed))
    print("    raw:    %s" % raw_path)
    print("    summary:%s" % sum_path)


if __name__ == "__main__":
    main()
