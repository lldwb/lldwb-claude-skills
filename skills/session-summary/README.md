# session-summary

会话总结与 skills 迭代：把一次会话收尾为「做了什么 → 发现的问题与教训 → 当前 skills 优化点评估 → 独立对抗性审查 → 实施」，作为迭代本仓库技能的工具（session-summary 自身也在迭代范围内）。会话操作的是别的项目仓库时，还包含把该仓库实证过的教训回流进**它自己的** `AGENTS.md`。

## 使用

当用户要求"总结这次会话""看看 skills 有没有可优化的地方""把这次的经验沉淀进技能"时触发。

```bash
# 会话记录先落盘抽取再读（单文件可达十几 MB，别整份读 transcript）
python <skill 目录>/scripts/extract-session.py <会话id> [--project <项目路径>] [--user|--assistant N|--timeline|--transcript]
# 自测基线（改过 extract-session.py 必跑）
python <skill 目录>/scripts/selftest.py
```

给会话文件路径亦可；产出默认落盘 `<当前目录>/.tasks/session-extract/`，`--stdout` 直接打印。

## 能力

- 会话取证：四种抽取模式——用户消息全文（总结的取证主体）、尾部 N 条 assistant 文本消息、逐条时间线（含工具调用摘要）、紧凑全文转录；按 Claude Code 的项目目录转义规则（非字母数字字符转 `-`）定位 `~/.claude/projects/<转义路径>/<会话 id>.jsonl`；**无会话 id 时目标为当前会话**——同转义目录下最近修改的 `.jsonl`，多会话并行时比对文件尾部内容甄别
- 总结三段：做了什么、发现的问题与教训、skills 优化点评估
- 独立审查：总结、教训、优化点清单与回流内容在交用户确认 / 提交目标仓库前，经**未参与产出的只读子代理对抗性审查**（默认怀疑结论夸大与证据断链），主代理复核证据后修复偏差并复审（最多 3 轮，超限交用户）
- 自迭代：session-summary 自身的迭代在**流程收尾**执行（输入是整个当前会话——从取证到实施的全过程，不提前触发），不设特殊通道：清单同样过对抗性审查与用户确认；实施改过抽取脚本的，重跑自测基线防回归
- 教训回流：会话操作的是**别的项目仓库**时，把该仓库实证过的教训写进那个仓库的 `AGENTS.md`（按那个仓库的规范提交，先落笔、审查通过后才提交）——**会话记忆（memory）只是本机补充，不替代回流**；目标文档是「主文件 + 分册 / 按需加载」形态时先读它顶部的加载索引表再定落点（常驻规则进主文件、特定时机的坑进分册，体例照既有分册复刻）；会话中**反复复用的中间脚本**（探针等）列入审视——视情况固化入库并登记，`tmp/` 等过程目录默认不固化
- 实施阶段按改动性质转 `feature-dev` / `bug-fix` / `refactor`，不自己硬走实现流程

## 文件

| 文件 | 说明 |
|------|------|
| `SKILL.md` | 技能指令（取证 → 总结 → 审视 skills → 目标项目 `AGENTS.md` 回流 → 优化点清单 → 独立审查 → 确认后实施 → 自迭代收尾） |
| `references/review-agent.md` | 独立审查子代理的 prompt 模板（对抗性、只读；第 6 步单次同步调用时整体作为子代理 prompt） |
| `scripts/extract-session.py` | 会话记录抽取（只取数不判定；四模式；默认落盘 `.tasks/session-extract/`） |
| `scripts/selftest.py` | 自测基线：18 用例覆盖四模式、过滤规则、定位转义与退出码（含两条历史回归用例；改过 extract-session.py 必跑） |

## 依赖

- Python 3（运行 `scripts/extract-session.py` 与 `scripts/selftest.py`，仅用标准库）
- Claude Code 的会话记录文件（`~/.claude/projects/<项目路径转义>/<会话 id>.jsonl`）
- 实施阶段按改动性质转 `feature-dev` / `bug-fix` / `refactor`；回流与发版各按其对象的规范——目标仓库 `AGENTS.md` 按那个仓库的提交规范，本仓库发版走仓库既有规则
