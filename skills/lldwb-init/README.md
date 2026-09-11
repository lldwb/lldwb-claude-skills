# lldwb-init

仓库指引初始化（`/init` 的 lldwb 版）：为项目生成或更新 agent 指引文档——正文写入 `AGENTS.md`（唯一权威源），`CLAUDE.md` 只保留一段指向。

## 使用

用户要求"初始化这个项目 / 仓库""执行 /init""生成或补全 `CLAUDE.md` / `AGENTS.md` 的指引""给新克隆的仓库做 agent 指引"时自动触发；也可显式要求"用 lldwb-init skill 初始化指引"。

适用边界：

- **本技能**：仓库指引导文档的生成与更新，产物是 `AGENTS.md` + `CLAUDE.md`（指向）
- 内置 `/init`：产物只有 `CLAUDE.md`；本技能把正文改投 `AGENTS.md`，适合"`AGENTS.md` 为唯一权威源、`CLAUDE.md` 只做指向"这一约定的仓库
- `doc-sync`：已有文档与代码行为不一致时的**同步修正**；本技能是从零（或近乎从零）建立指引

## 流程

1. **前置检查** — 确认 git 仓库根、既有 `AGENTS.md` / `CLAUDE.md`、两份文件是否被 `.gitignore` 忽略（`git check-ignore`）
2. **探索仓库** — 读 README、构建清单、CI 配置、目录结构、既有 AI 规则；`git ls-files` 确认哪些文件真正入库；`git log` 采集提交信息风格
3. **归纳架构** — 只提炼"读多个文件才能拼出来"的结论（分层与入口、分发路径、跨模块共用约定、已知坑），每条标注出处
4. **动笔** — 按骨架写 `AGENTS.md`（与既有内容合并、不覆盖）；`CLAUDE.md` 写成指向
5. **落盘核验** — `git status` / `git check-ignore` / `git diff` 三项
6. **汇报与提交** — 汇报改动与发现的问题，询问后按项目规范提交

## 能力

- 产物归属固定：正文进 `AGENTS.md`，`CLAUDE.md` 仅指向（含 `/init` 要求的标准英文前缀）
- 合并策略：既有 `AGENTS.md` 内容只降层级、文本零改动，新正文在前；既有 `CLAUDE.md` 的实质内容先并入 `AGENTS.md` 再收敛为指向
- 断言必须带佐证：命令、路径、"唯一入口""共享模块""只改一处"等结论动笔前用 `grep` / `git` 核实
- 写作红线对齐 `/init`：不编造章节、不写通用开发实践、不罗列文件树、只写非显然的架构与约定
- 异常按"记录 + 上交"处理：`.gitignore` 误命中、逻辑重复等问题记入「已知坑」并汇报，不擅自修
- 提交边界：落盘核验后先问用户，显式 `git add` 两份文档，不自动 push

## 文件

- `SKILL.md` — 技能指令（唯一入口）
- `references/output-templates.md` — `AGENTS.md` 章节骨架与反例、`CLAUDE.md` 指向模板、合并既有内容的做法、动笔前核验清单

## 依赖

- git（探索与核验用）
