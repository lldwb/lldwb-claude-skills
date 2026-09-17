# Changelog

## [2.3.4] - 2026-09-17

补 `bug-fix` 的取证口径与上下文节制：新增截图 / 抽样证据的处理规则、同类非缺陷任务的边界说明、自建取证脚本的「落盘 + 截断」要求；`references/root-cause-checklist.md` 同步新增「证据产出与上下文节制」一节（原第 7 节「结论自检」顺延为第 8 节）；未新增技能、技能名与 `description` 不变。

### 新增

- **`bug-fix` 补截图与抽样证据口径**：用户以截图 / 录屏报现象时，截图是**线索不是结论**——先核验现象是否仍是当前状态（截图可能过期；程序可能仍跑着旧代码，改了源不等于现象已消失），再定位；读图工具返回空或截断时换能直接看图的工具，不凭记忆描述图内容。证据来自抽样（几张截图、几个 case）时，取证**升级为同类问题的全量清点**（枚举同一形态的全部出现位置与实例，归类后一次性处置），不逐个 case 追着修
- **`bug-fix` 补「证据产出与上下文节制」**：自建诊断脚本 / 批量比对 / 全量扫描的完整结果落盘到过程产物目录，只把摘要结论与文件路径读回上下文，单次读回超过约 200 行先截断或分组读；同一批证据在两种基准上取数时，摘要必须写明每个数字各自取自哪份基准——基准写反会让整条结论反过来
- **`bug-fix` 补同类非缺陷任务的边界说明**：实际是资产维护类任务（覆盖补全、产物 / 数据同步、批量补齐既有资产）时，按取证与验证的要求推进即可、不套缺陷叙事；同类任务反复出现且无技能覆盖时，向用户提议沉淀为独立技能，不自行新建——也不为了「用得上本技能」把维护任务写成 bug
- **`bug-fix` 的 `references/root-cause-checklist.md` 同步**：第 1 节补「用户提供的截图 / 录屏」与「抽样证据」两条取证口径，新增第 7 节「证据产出与上下文节制」

### 变更

- **`bug-fix` 的 `README.md` 能力与边界同步**：能力表补截图 / 抽样证据口径与清单新增节，边界补非缺陷资产维护任务与技能沉淀提议

### 说明

- 正文为既有技能的取证能力补强与文档同步（小修小补 + 小功能补强），未新增 / 删除技能、技能流程与语义无变更，按分级取**小版本**。
- 技能数量与名称零改动，两条分发路径（安装脚本启用清单、`.claude-plugin/marketplace.json` 的 `skills` 数组）无需改动。
- `.claude-plugin/marketplace.json` 版本号 2.3.3 → 2.3.4

## [2.3.3] - 2026-09-16

补既有技能的取证能力与安装器便利：`frontend-error-diagnose` 新增「请求头被改写类报错」取证路径（`references/extension-header-forensics.md`），`bug-fix` 补环境侧缺陷处置分支与工具链故障取证清单，`db-query` 补 GaussDB 兼容注意节；安装器缺 `config.json` 时自动创建最小配置并修复 Windows 脚本失败提示乱码；`AGENTS.md` 已知坑补 install.py 补全行为区分，`.gitignore` 忽略本地诊断产物目录 `diagnosis/`；未新增技能、技能名与 `description` 不变。

### 修复

- **Windows 安装脚本失败提示乱码修复**：`install.bat` / `uninstall.bat` 失败分支的 `pause` 换为 `python -X utf8` 输出中文提示，规避 GBK 控制台乱码

### 新增

- **`frontend-error-diagnose` 补「请求头被改写类报错」取证路径**：新增 `references/extension-header-forensics.md`——适用判据（接口直连正常但浏览器稳定失败、失败 403/401 且请求头自相矛盾、失败成片含静态资源等）、curl 对照实验定性、扩展 DNR 规则的磁盘取证（`DNR Extension Rules` / LevelDB 关键字检索）、扩展源码辅助判据、处置与验证、环境能力限制；`browser-evidence-checklist.md` 增加「接口 403/401 但直连正常」行与对照实验提示，无浏览器 MCP 时以 HAR 导出作请求头证据
- **`bug-fix` 补环境侧缺陷处置分支**：根因不在本项目代码（运行环境、第三方依赖、工具链层）时仍走四段式定位与验证，但改动落在环境侧、不产生 git 提交（不为"有东西可提交"而在本仓库造改动）；`references/root-cause-checklist.md` 新增第 6 节「环境 / 工具链故障取证」——隔离复现优先于溯源、复合报错拆到最内层、退出码语义（127）、上游包缺陷按 tarball 实判、受限网络下取依赖、环境侧验证口径
- **安装器缺 `config.json` 时自动创建最小配置**：无参 `python install.py` 在缺配置时自动创建 `{"skills": {}}`（未列出的技能默认启用 = 全量安装），仅首次创建、已存在绝不覆盖；`--list` 与显式指定技能名不依赖配置
- **`db-query` 补 GaussDB 兼容注意节**：SKILL.md 新增实测注意——`COUNT(*) FILTER` 不支持改用 `SUM(CASE WHEN)`、无 `::regnamespace` 类型、分布键与主键/唯一约束的关系、`RENAME TO` 目标不带 schema 前缀、约束名在 schema 内全局唯一、Navicat 导出 DDL 的 `DISTRIBUTE BY HASH()` 坑与 collate 显式指定

### 变更

- **`AGENTS.md` 已知坑补 install.py 补全行为区分**：明确「配置文件缺失」自动创建 vs「文件存在但未列出某技能」按默认启用补全的区别——想排除某技能须显式写 `enabled: false`，不能靠"不列出"
- **`.gitignore` 忽略本地诊断产物目录 `diagnosis/`**：目录内可能含真实 IP / 端口 / 扩展 ID 等环境与请求头证据，不入库

### 说明

- 正文为既有技能取证能力补强、安装器小功能与缺陷修复、文档同步（小修小补 + 小功能补强），未新增 / 删除技能、技能流程与语义无变更，按分级取**小版本**。
- 技能数量与名称零改动，两条分发路径（安装脚本启用清单、`.claude-plugin/marketplace.json` 的 `skills` 数组）无需改动。
- `.claude-plugin/marketplace.json` 版本号 2.3.2 → 2.3.3

## [2.3.2] - 2026-09-15

修复插件分发与文档的技能数量不一致：`marketplace.json` 插件条目补必填 `source` 并修正 skills 数组路径；README / PLUGIN_README 技能数量声明从「24 个」修正为「26 个」（与 `skills/` 目录条目数对齐），`session-summary` 技能内两处同源数量同步修正，`AGENTS.md` 架构第 3 条固化「技能数量声明以 `skills/` 目录条目数为准、随技能表同步更新」约定；未新增技能、技能名与 `description` 不变。

### 修复

- **`marketplace.json` 插件条目补必填 `source` 并修正 skills 路径**：插件条目标准字段补全，`skills` 数组路径修正为 `./skills/<技能名>`，与安装脚本分发路径一致
- **文档技能数量声明 24 → 26**：README / PLUGIN_README 正文「24 个」修正为「26 个」（技能表实际 26 行、`skills/` 目录 26 个目录、marketplace `skills` 数组 26 条）；`session-summary` SKILL.md 的 frontmatter description 与「验证方式」两处「24 个技能」同步修正

### 变更

- **`AGENTS.md` 架构第 3 条补技能数量一致约定**：文档正文的技能数量声明必须以 `skills/` 目录条目数（即分发清单全量）为准，新增 / 删除技能时数字随技能表一并更新，不得停留在旧值

### 说明

- 正文为文档数量修正与表述统一（小修小补），不构成技能新增 / 删除 / 语义重写，按分级取**小版本**。
- 技能数量与名称零改动；`config.json`（本地启用清单，不入库）本地补全 `git-history-rewrite` / `session-summary` 两项，与分发全量对齐。
- `.claude-plugin/marketplace.json` 版本号 2.3.1 → 2.3.2

## [2.3.1] - 2026-09-15

补任务跟踪机制的可选指引与技能自包含约定：`AGENTS.md` 新增「任务跟踪机制（环境能力可选）」小节并强化「技能目录自包含」为架构第 1 条（强制），26 个技能注意事项补一条「任务跟踪按环境能力可选」（**自包含**写法，安装到其他项目后不依赖仓库文档）；未新增技能、技能名与 `description` 不变。

### 变更

- **`AGENTS.md` 强化「技能目录自包含（强制）」为架构第 1 条**：`skills/<技能名>/` 单目录内自带运行所需的全部内容，正文不得依赖未随技能分发的文件（仓库 `AGENTS.md`、其他技能目录、安装器脚本），不得隐式依赖其他技能（需他技能能力时显式写「转 `xxx` 技能」边界）；安装即整体复制到 `~/.claude/skills/`、复制后可直接使用。原因：保证技能独立可用（安装 / 卸载 / 覆盖后无失效引用）、便于跨工具复用与 Task 子代理调度（子代理为全新上下文、只读随技能分发的文件）、是「任务跟踪机制」等按需引用写法的前提；原架构条目顺延为 2-5，版本号引用同步改为「架构」第 5 条
- **`AGENTS.md` 新增「任务跟踪机制（环境能力可选）」小节**：进度跟踪不硬性依赖某一种形态——环境提供 `TodoWrite` / `Task*` 工具时用原生任务清单（完成一项勾一项、收尾核对无未勾选项；新模型代际默认不加载这些工具属正常设计，是否启用由使用者自定）；否则退回对话内文本清单或 `.tasks/` 落盘勾选（沿用 feature-dev `tasks.md` 勾选规则：完成一项立即勾、不批量补勾、未完成项写明处置）；清单由主代理维护，与子代理调度配合时各自回报单元状态、不共享
- **26 个技能 `SKILL.md` 注意事项补「任务跟踪按环境能力可选」一条**：段首新增引用行，采用**自包含**写法——一行内含完整可执行规则（原生清单可用时完成一项勾一项、收尾核对无未勾选项，否则退回对话内文本清单或 `.tasks/` 落盘勾选、未完成项写明处置），不指向 AGENTS.md 小节，安装到其他项目后引用不悬空；`AGENTS.md` 小节定位为仓库级约定展开

### 说明

- 正文为规则说明与注意事项增补（表述统一），不构成技能新增 / 删除 / 语义重写，按分级取**小版本**。
- 技能数量与名称零改动，两条分发路径（安装脚本启用清单、`.claude-plugin/marketplace.json` 的 `skills` 数组）无需改动。
- `.claude-plugin/marketplace.json` 版本号 2.3.0 → 2.3.1

## [2.3.0] - 2026-09-15

新增两个技能（`git-history-rewrite` 历史改写、`session-summary` 会话总结与 skills 迭代），`commit-review` 审查清单补发版提交专项核查；技能总数 24 → 26。

### 新增

- **`git-history-rewrite` 技能（新增）**：Git 历史改写标准工作流——拆分提交（功能/版本分离）、改类型/标题、重排顺序、删除提交、恢复提交时间；先备份分支、方案先行、四重验证（树一致性 / 提交规则 / 时间语义 / tag 指向）、确认后强推。沉淀自历史改写实操：拆分提交固定顺序（先取信息再 reset、`restore --staged` 移出）、时间恢复方法（信息匹配映射 + filter-branch）、发版提交位置与条目不可变规则；`references/lessons.md` 收录常见坑速查
- **`session-summary` 技能（新增）**：会话总结与 skills 迭代工具——取证会话动作 → 总结（做了什么 / 发现了什么 / 教训 / 留下的状态）→ 审视当前技能找优化点（每项给价值 / 成本 / 建议）→ 确认后按对应技能流程实施，新增 / 增强技能走发版流程

### 变更

- **`commit-review` 审查清单补「发版提交专项核查」**：第七维（提交信息规范）新增子节——被审提交为 `chore(release): 发布 vX.Y.Z` 时核查：类型与标题、改动范围（只动版本文件、不夹带 `skills` 数组）、位置（位于该版本最后一个功能提交之后）、条目不可变（不修改历史条目、无补记）、版本号三处对齐、时间语义（历史重写后恢复原提交时间）
- **分发同步**：`marketplace.json` skills 数组 24 → 26、README / PLUGIN_README 技能表补 2 行；`config.json`（本地启用清单，不入库）需本地同步

### 说明

- 技能数量 24 → 26（新增 2 个），既有技能为审查清单增补，按分级取**中版本**。
- `.claude-plugin/marketplace.json` 版本号 2.2.4 → 2.3.0

## [2.2.4] - 2026-09-15

技能正文转向**充分运用 Claude Code 机制**：把「正文不依赖仅 Claude Code 可用机制」的仓库基调反转为「面向 Claude Code 运行、充分运用其机制」，并修复 6 个技能对专用工具调用 / Task 子代理调度运用不足的实现；未新增技能、技能名与 `description` 不变。

### 变更

- **`AGENTS.md` 反转机制约束基调**：「正文不依赖仅 Claude Code 可用的机制」改为「面向 Claude Code 运行、充分运用其机制」——Task 子代理调度、上下文管理（按段加载、长产物落盘后引用路径）、专用工具调用（Grep / Glob / Read，不用 bash 的 grep / cat 代替）与浏览器 MCP 是技能应**主动运用**的机制，不因跨工具兼容而回避；frontmatter 允许 Claude Code 官方字段（`disable-model-invocation` / `allowed-tools` / `argument-hint` / `model` 等），不新增私有字段——`git-clean-branches` / `git-rollback` 已用的 `disable-model-invocation` 与旧「frontmatter 仅 name + description」约束的冲突随之消除；「子代理调度约定」补适用范围判据（可并行、需上下文隔离的单元级任务与独立只读审查用子代理；单任务工作流如 `bug-fix` / `commit-create` 不强制）
- **`check-rule-extract` 改用专用工具**：正文「用 bash（Grep / wc / ls / python）解析范围」「用 bash ls / Grep 校验文件存在」改为「用 Grep / Glob 工具定位与校验、bash 仅用于 wc / ls / python」——修复工具调用机制运用不足
- **`commit-review` / `log-diagnose` / `repo-init` 统一工具名**：正文与核查清单中的小写 `grep` / `glob` / `read`（歧义为 bash 命令）统一为 Grep / Glob / Read 工具；`commit-review` 影响面检索与 `project-explain` 素材收集补充「检索面大时派只读子代理分担、避免挤占上下文」提示
- **`repo-init` 大仓库探索补子代理分片**：入库文件多时按模块 / 目录派**只读探索子代理**分片收集素材（一个分片一个子代理，回报「事实 + 出处（`file:line` / 命令 + 输出）」清单），主代理只汇总归纳写指引，避免探索挤占上下文；全仓清点与计数口径仍由主代理用 bash 完成
- **`comment-supplement` 批量收集补只读子代理**：目标文件多时按文件 / 模块派只读子代理并行收集「缺失 / 不准确 / 过期」三类位置清单（一个单元一个子代理），主代理汇总去重后交用户确认；补全修正仍由主代理执行（注释质量敏感，不外包）
- **`README.md` 同步基调**：技能定位从「非 Claude Code 私有格式、跨工具需适配」改为「面向 Claude Code 运行、充分运用其机制，开放格式仍可被其他工具复用、由使用方适配」

### 说明

- 本次为技能正文对 Claude Code 机制运用的缺陷修复：机制基调反转（`AGENTS.md`）+ 6 个技能对专用工具 / 子代理调度运用不足的修正，均为正文表述与机制提示增补，不构成技能新增 / 删除 / 语义重写，按分级取**小版本**。
- 技能数量与名称零改动，两条分发路径（安装脚本启用清单、`.claude-plugin/marketplace.json` 的 `skills` 数组）无需改动。
- `.claude-plugin/marketplace.json` 版本号 2.2.3 → 2.2.4

## [2.2.3] - 2026-09-15

吸纳外部工具 zcf（Zero-Config Code Flow）中尚未评估的三块：`commit-create` 补提交前状态校验与提交信息约束、`repo-init` 补扫描覆盖与缺口汇报、安装脚本补备份与安装状态；未新增技能、技能名与 `description` 不变。

### 新增

- **`install.py` 覆盖前备份 + 安装状态 + 恢复**：覆盖同名技能前先把 `~/.claude/skills/<技能名>/` 备份到 `~/.claude/backup/lldwb-skills/<时间戳>/`；安装状态（版本取自 `.claude-plugin/marketplace.json`、安装时间、各技能本次是否产生备份）合并写入同目录 `state.json`；新增 `--list-backups` 与 `--restore <技能名> [--backup <时间戳>]`（目标已存在时**拒绝覆盖**，提示先卸载）；`--list` 追加「已安装版本与时间」列，以磁盘实际为准、与状态不一致时显示「已安装（无本仓库安装记录）」；`--dry-run` 不写备份与状态
- **`uninstall.py` 删除前备份**：删除技能目录前先备份到同一目录，并移除 `state.json` 中的对应条目（**备份保留**，可经 `install.py --restore` 回滚），输出恢复命令提示

### 变更

- **`commit-create` 补三项提交前约束**：① 提交前校验仓库状态——非 Git 仓库、rebase / merge 中途、detached HEAD 三类先报告并询问，不盲目提交（执行步骤新增为第 1 步）；② 正文分点要求动词开头，禁止 `Feature: xxx` 式冒号分隔行；③ 首行（含 `type(scope):` 前缀）≤ 50 字符、正文每行 ≤ 72 字符——取值按 Git 通行的 50/72 惯例，并核对了本仓库近 40 条提交标题（39 条 ≤ 50、中位数 35）
- **`repo-init` 补「覆盖与缺口要报出来」**：探索按「全仓清点 → 模块定点读 → 按需深挖」三档推进；收尾汇报须给出**口径可复算**的覆盖数据（已读 / 入库文件总数，`git ls-files | wc -l` 可复核）、覆盖模块、未覆盖路径与原因、下一步建议；达工具或轮次上限时**先落盘已完成部分**并写明"为何到此为止 + 缺口清单"，不静默截断、不假装读全
- **文档同步**：`AGENTS.md` 常用命令补备份 / 恢复用法与备份落点、`README.md` 安装章节补备份与恢复说明及清理方式、`commit-create` / `repo-init` 的 `README.md` 能力清单同步

### 说明

- **来源与取舍**：源自本机安装的 zcf（命令 / 代理 / 输出风格 / 安装器）。其**命令集主体已于 v2.2.0 吸纳**（`git-cleanBranches` / `git-rollback` / `git-worktree` / `git-commit` / `workflow`，见该版本条目），本次只处理当时**未被评估**的三块。**未吸纳**：4 个代理的形态（frontmatter 用 `tools` / `color` 私有字段，违反本仓库跨工具开放性要求——只把内容迁移进技能正文，不新增 `agents/` 目录）、6 个输出风格（常驻风格与「按需触发的流程技能」定位冲突，同 v2.2.2 对 caveman 的处理）、`bmad-init` / i18n 的 en·ja 模板 / Codex 多工具模板（成本高且与本仓库的占位符通用化不是一回事）；提交信息语言推断与 `.zcf` 计划目录约定维持不采纳。
- **有意简化（写明上限与升级路径）**：`repo-init` 不落 `.claude/index.json` 式扫描索引，避免往被初始化的仓库塞入指引之外的持久产物——上限是中断后需重新清点、不能断点续扫，确有需求时再引入索引文件；安装器备份不做自动轮转——上限是反复安装会累积磁盘占用，需要时再补 `--prune-backups`。
- 备份与状态逻辑在 `install.py` / `uninstall.py` 各有一份实现（保持脚本各自独立），两处须同步修改，已在代码注释标注。
- 技能数量与名称零改动，两条分发路径（安装脚本启用清单、`.claude-plugin/marketplace.json` 的 `skills` 数组）无需改动；既有技能为正文增补（新增可中止提交的前置校验与强制汇报的覆盖口径），安装器为工具能力增补，均不构成技能新增 / 删除 / 语义重写，按分级取**小版本**。
- `.claude-plugin/marketplace.json` 版本号 2.2.2 → 2.2.3

## [2.2.2] - 2026-09-15

吸纳外部技能 Ponytail（lazy senior dev，MIT）的三条通用工程原则到既有技能：`code-optimize` 新增「动手前先过阶梯」与「有意简化必须标注」，`feature-dev` 的方案设计把「不做 / 复用既有」固定为备选路线第 0 项；未新增技能，技能名与 `description` 不变。

### 变更

- **`code-optimize` 增补「最小改动优先」**：`references/optimize-checklist.md` 新增「## 0. 动手前先过阶梯」（是否真需要 → 复用本仓既有 → 标准库 / 框架是否已能做 → 既有依赖 / 平台特性是否覆盖 → 能否用更小改动达成 → 才动手，**命中即停在该级**），「2.3 范围自查」补「是否用更小的改动达成了同一效果」，末尾新增「## 4. 有意简化必须标注」（写明简化了什么 / 上限在哪 / 如何升级，且正确性不打折）；`SKILL.md` 注意事项补「最小改动优先」、执行步骤 2 的清单括注同步为新节
- **`feature-dev` 增补「方案设计的第 0 项候选」**：要求 3 与执行步骤 3 明确——备选路线的**第 0 项固定为「不做 / 复用既有实现 / 用标准库或既有依赖」**，先证明其不成立再讨论新增；注意事项补「最小改动优先、简化须标注」
- **文档同步**：`code-optimize` / `feature-dev` 的 `README.md` 能力清单与文件说明同步（`SKILL.md` 与面向人的 `README.md` 须一致）

### 说明

- **来源与取舍**：只吸纳 Ponytail 的决策阶梯与简化标注约定；**未吸纳**其「常驻编码风格」形态与已有等价实现的条款——根因取证（grep 全部调用方）、信任边界输入校验、安全与数据完整性等，本仓库既有技能已有更强实现。同批评估的 caveman（简洁沟通模式）**整体不吸纳**：其常驻输出风格与本仓库「按需触发的流程技能」定位冲突，其提交 / 评审格式已被 `commit-create` / `commit-review` 覆盖且更细，其「何时不启用」在本仓库已是每个技能的「适用与边界」章节且写明改道目标。
- **未新增技能、未改技能名与 `description`**：两条分发路径（安装脚本的启用清单、`.claude-plugin/marketplace.json` 的 `skills` 数组）与 `README.md` / `PLUGIN_README.md` 的技能表因此无需改动；`config.json`（本地启用清单，不入库）同样无需改动。
- 本次为既有技能正文的语义增补（`feature-dev` 执行步骤新增要求、`code-optimize` 检查清单新增两节），技能数量、脚本与分发能力零改动，按分级取**小版本**。
- `.claude-plugin/marketplace.json` 版本号 2.2.1 → 2.2.2

## [2.2.1] - 2026-09-14

授权许可从 MIT 改为 GPL-3.0（更严格的开源协议）：`LICENSE` 替换为 GPL-3.0 官方文本，README 许可说明同步更新，版权署名 lldwb。

### 变更

- **授权许可从 MIT 改为 GPL-3.0**：`LICENSE` 由 MIT 替换为 GPL-3.0 官方文本（copyleft，衍生作品须以相同协议开源），README 底部 `License: MIT` 改为 GPL-3.0 许可说明，版权署名 lldwb。
- **版本号同步**：`.claude-plugin/marketplace.json` 的 `version` 由 `2.2.0` → `2.2.1`。

### 说明

- 本次为文档与许可政策变更（不涉及技能功能），取**小版本**；技能正文、脚本与分发能力零改动。

## [2.2.0] - 2026-09-14

吸收合并 7 个外部技能：新增 5 个技能（`opencode-batch` / `nas-disk-diagnostic` / `git-clean-branches` / `git-rollback` / `git-worktree`），另将 `git-commit` 与 `workflow` 的能力分别并入既有技能 `commit-create` 与 `feature-dev`；技能总数 19 → 24。

### 新增

- **`opencode-batch`（新增）**：多模块并行改造编排（opencode CLI 版）——每模块一个 worktree + 一个子代理在 worktree 内 `opencode run --command <命令>`；阶段 0 前置检查（CLI 可用 / `.opencode` 已跟踪 / 测试凭据可解 / 外部依赖连通 / 主分支就绪 / 命令定义完备等）→ 阶段 1 并行执行与中断通报 → 阶段 2 合并 → 阶段 3 提交收尾；`references/lessons.md` 收录示例经验（占位符化，按项目技术栈替换）
  - 与 `module-batch` 的分工在两个技能中互指：`module-batch` = 通用 worktree 并行机制（子代理直接执行），本技能 = 经 opencode CLI 中转的执行编排（多出 CLI 与命令定义前置检查、opencode 中断处置）
- **`nas-disk-diagnostic`（新增）**：NAS 硬盘诊断与可视化报告——SSH 采集（文件系统 / RAID / 块设备 / dmesg）→ SMART 深度诊断 → 坏盘可修复性评估 → 报告 → 分级建议；核心知识点为扩展卡（如 ASMedia ASM1166）上的硬盘必须 `smartctl -d sat`，否则误报无 SMART 能力
  - `scripts/nas_diagnostic.py`（只取数不下结论；补 `_ensure_utf8()`、paramiko 延迟导入使 `--help` 不因缺依赖崩溃、支持 `NAS_PASSWORD` 传密码）、`references/smart-guide.md`、`references/report-guide.md`、`assets/report_template.html`（补建源技能缺失的模板）、`requirements.txt`（paramiko）
- **`git-clean-branches`（新增，仅显式调用）**：清理已合并 / 过期分支——默认 dry-run 只出清单、保护分支清单（`git config branch.cleanup.protected`，支持通配符）一律不删、未合并分支默认不删、远程删除单独确认；补「动分支前先核 HEAD 与工作区」护栏
- **`git-rollback`（新增，仅显式调用）**：分支回滚到历史版本（`reset` / `revert`）——默认 dry-run、`reset` 前先建备份分支、受保护分支额外确认、不提供 `--force`、不自动强推 / push；补「动非当前分支用 `git branch -f`，不用 `git reset --hard`」护栏
- **`git-worktree`（新增）**：worktree 管理（`add` / `list` / `remove` / `prune` / `migrate`）——统一目录约定（默认 `<主仓库同级>/.zcf/<项目名>/`，可按项目约定替换）、主仓库路径推导、绝对路径防嵌套、环境文件按 `.gitignore` 复制、内容 / stash 迁移

### 变更

- **`commit-create` 吸收 `git-commit`（增补，不重写）**：新增「可选能力」一节——emoji 前缀（type → emoji 映射）、显式指定 type / scope 覆盖自动推断、仅用 Git 的轻量路径（不依赖包管理器 / 构建工具）、`--amend` 修补上次提交（限未推送分支）、`BREAKING CHANGE` 与 git trailer 脚注、`--no-verify` 边界；「拆分判定」补规模阈值行（> 300 行或跨多个顶级目录先给拆分方案并给出各组的 pathspec）
  - **未采纳**源技能「默认可跳过钩子」的取向：仍保持「钩子报错修问题本身、默认不跳过」，仅用户显式要求时例外并在汇报中注明；提交规则仍单点定义在本技能（SSOT），不在他处重复
- **`feature-dev` 吸收 `workflow`（增补，不重写）**：澄清歧义步骤补需求完整性评分（目标明确性 3 / 预期结果 3 / 边界范围 2 / 约束条件 2，低于 7 分先补齐关键信息）；新增「可选：交互式六阶段模式」一节（研究 → 构思 → 计划 → 执行 → 优化 → 评审，含模式标签、阶段门禁、执行后**自动**优化自检（仅本次改动）、评审对账、时间戳取真值）
  - **未引入**源技能的计划目录约定（`.zcf/plan/current → history`）：计划文档位置与命名仍按 `references/plan-doc-template.md`，归档只作为该模式的可选收尾动作
- **新技能形态适配仓库约定**：源技能为「斜杠命令」形态（`allowed-tools` + slash 用法正文），统一改写为技能口径（`description` 写清「做什么 + 何时用 + 边界」、正文为执行指令）；`git-clean-branches` / `git-rollback` 保留 `disable-model-invocation: true`（含删除、历史改写的危险操作只允许显式调用），其余新技能可自动触发
- **脱敏与通用化**：源技能中的项目专属内容（模块名、包路径、业务符号、本机绝对路径）一律占位符化——`opencode-batch` 的经验教训移入 `references/lessons.md` 并标注「示例经验，按项目技术栈替换」；`nas-disk-diagnostic` 的本机 Python 解释器路径改为 `pip install -r requirements.txt`
- **外部依赖写明降级路径**：`nas-disk-diagnostic` 的内联展示改为「有内联能力则内联、否则落盘 HTML 并提示用浏览器打开」；`git-worktree` 的 IDE 打开命令不在 PATH 时跳过并提示，不报错中断
- **分发与文档同步**：`README.md`（技能表 19 → 24 行、首段数量、`disable-model-invocation` 例外说明、依赖子代理调度的技能清单补 `opencode-batch`）、`PLUGIN_README.md`（技能表与数量）、`.claude-plugin/marketplace.json`（`skills` 数组与插件 `description`）、`config.json`（本地启用清单，不入库）

### 说明

- 本次为**技能大改（新增技能）**，取**中版本**；既有 17 个技能零改动（`commit-create` / `feature-dev` 为增补式扩充，原有流程与安全条款不变）。
- 新技能均为自包含目录（`SKILL.md` + `README.md`；`nas-disk-diagnostic` 另含脚本 / 参考件 / 模板 / 依赖清单）。
- 未改 `install.py` / `uninstall.py` / `check-version.py`：新技能经既有清单机制自动覆盖两条分发路径。
- `.claude-plugin/marketplace.json` 版本号 2.1.3 → 2.2.0

## [2.1.3] - 2026-09-14

修复 `mr-create` 的推送前置条件：由「只要不是『已推送且与 upstream 一致』就先推送」改为按源分支状态键处置，修正在 `remote-only` 等状态下必然失败的推送指引。

### 修复

- **`mr-create` 推送前置条件改按状态键处置**：`SKILL.md` 新增「推送源分支（按状态键处置）」表，把 9 个状态键（`up-to-date` / `pushed-no-tracking` / `not-pushed` / `ahead` / `remote-only` / `behind` / `diverged` / `pushed-diverged` / `pushed-unknown`）逐行对应到处置——只有 `not-pushed` / `ahead` 需推送且每次单独征得用户同意，`remote-only` 不推送（远端分支本身就是合并请求的 head），`behind` / `diverged` / `pushed-diverged` / `pushed-unknown` 停下报告、一律不 `--force`；推送口径单点定义于该表，「要求 / 执行步骤 / 平台创建 / 验证 / 注意事项」改为指向它
  - 原规则对 `remote-only` 输出的 `git push -u origin <源分支>` 必然失败（本地无该分支，`src refspec ... does not match any`）；对 `diverged` / `pushed-diverged` 需 `--force`（本技能禁止）；对 `behind` 是空操作，且素材 diff 取本地分支、平台 head 取远端，描述与平台将合入的内容不一致
- **`prepare-mr.py`：素材与 stdout 暴露状态键、只报事实**：素材「源分支推送状态」段改为「状态键 + 事实 + 依据」，删除对全部非一致状态统一输出的推送命令；补「依据：本地 remote-tracking，未 fetch 时可能过期」与「本地与远端源分支提交不一致（素材 diff 取本地分支、平台 head 取远端）」两条事实行；状态键 `pushed` 更名 `pushed-unknown` 并写明领先 / 落后无法判定
- **取数前先 `git fetch origin`**：源分支与目标分支一致适用，fetch 失败则继续取数并注明状态可能过期——源分支推送状态取自本地 remote-tracking，未 fetch 时会把「已分叉」误报为「本地领先」
- **`README.md` 同步**：远端状态按状态键逐态列出、模板探测补齐脚本实际支持的仓库根 `PULL_REQUEST_TEMPLATE.md`（原文只列 `.github/PULL_REQUEST_TEMPLATE*` 与 `.gitlab/merge_request_templates/*`）、安全边界改为按状态推送；`SKILL.md` / `README.md` 同步补 fetch 建议

### 说明

- 本次为缺陷修复 + 文档同步（小版本）：未新增 / 删除技能，技能步骤数不变，常规路径（未推送 / 本地领先 / 已一致）行为不变；变化集中在 `remote-only` / `behind` / `diverged` / `pushed-diverged` 等此前会给出错误动作或误导性结论的状态。
- 验证：本地用例集 38 项全过，含 `remote-only` 下 `git push -u origin <分支>` 实测失败证据、未 fetch 与 fetch 后状态对比（`ahead` → `diverged`）、状态键与 `SKILL.md` 表格的一致性校验；用例集为本地过程产物（`.tasks/`），不入库。
- `.claude-plugin/marketplace.json` 版本号 2.1.2 → 2.1.3

## [2.1.2] - 2026-09-14

补齐版本号描述：把既有版本实际使用的分级（大版本 = 整体重构、中版本 = 技能大改、小版本 = 小修小改）写入约定，并校正一处与实际校验口径不符的描述。

### 变更

- **`AGENTS.md`「架构」第 4 条补版本号分级选取规则**：版本号按改动幅度选取——大版本 `vX` = 整体重构（结构性 / 破坏性改造，如技能改名）、中版本 `vX.Y` = 技能大改（新增 / 删除技能，或既有技能的流程与语义变更）、小版本 `vX.Y.Z` = 小修小改（表述统一、文档同步、小修小补与缺陷修复）；「常用命令」发版校验段同步点明脚本只核对一致性、不定级
- **三处对齐口径校正**：`CHANGELOG.md` 一项由「`## [x.y.z]` 标题」明确为「**顶部最新条目**的标题」，并写明校验只认顶部一条、历史条目同为该形式但不参与对齐；补 CHANGELOG 新条目末须列出 `marketplace.json` 版本号变更行的写法（历史条目不改写，记录当时事实）
- **`check-version.py` 与 `.githooks/pre-push` 说明同步**：明确本工具只核对三处一致与 tag 是否可达、**不定级**，选取由人按「架构」第 4 条判断（呼应「脚本只取数，判定归 agent」）；`--help` 输出与脚本行为零改动
- **`README.md` / `PLUGIN_README.md`**：面向使用者补版本号分级摘要（据此判断升级影响面），细则指向 `AGENTS.md`（规则正文单点定义，不复制）
- `.claude-plugin/marketplace.json` 版本号 2.1.1 → 2.1.2

### 说明

- 本次为纯描述补齐与口径校正：脚本逻辑与技能流程零改动；规则正文只在 `AGENTS.md` 定义，其余位置为摘要 + 指向。
- 本次改动本身即小修小改（小版本），按新写入的规则发版。

## [2.1.1] - 2026-09-14

统一规范来源：移除全部「项目开发手册」表述，项目的约定一律以 **`AGENTS.md` 为唯一权威源**。

### 变更

- **移除「项目开发手册」相关表述（全仓 50 余处）**：技能正文、参考件与仓库文档中凡「`AGENTS.md` / 开发手册」并列表述的，统一收敛为 `AGENTS.md` 单一权威源；「先理解再动手」类要求改为「阅读 `AGENTS.md`，按其章节按需加载与本改动相关的部分，勿全文加载」，不再引导查找开发手册
  - 涉及技能：`bug-fix` / `code-optimize` / `feature-dev` / `comment-supplement` / `refactor` / `commit-review` / `commit-create` / `doc-sync` / `unit-test` / `module-batch` / `repo-init` / `i18n-transform` / `mr-create` / `check-rule-extract`（各技能的 SKILL.md、README.md 与 references）；仓库根 `README.md`、`AGENTS.md`
  - 提交规则统一短段的权威依据由「项目开发手册 / `AGENTS.md`」改为「项目 `AGENTS.md`」，11 处保持逐字一致
- **`spec-route` 权威源由「开发手册」改为 `AGENTS.md`**（技能保留）：职责改为「按场景定位 `AGENTS.md` 的章节并按段读取」——Grep 章节标题取行号 + Read `offset/limit` 只读目标段，不全文加载；SKILL.md、README 与 `references/route-table-template.md` 同步改写，`README.md` / `PLUGIN_README.md` 的技能表同步
- `.claude-plugin/marketplace.json` 版本号 2.1.0 → 2.1.1

### 说明

- `spec-route` 技能**保留**（未删除）：原设计服务于体量较大的项目规范文档，现改以 `AGENTS.md` 为权威源；项目没有 `AGENTS.md` 时该技能不适用。
- 本次为纯表述与权威源收敛，不改任何技能的流程、安全条款与脚本接口；历史条目中的版本号与表述保持原样（记录事实）。

## [2.1.0] - 2026-09-14

统一子代理派发粒度：由「按数量分批」改为「**一个单元一个子代理**」；并清理了历史提交中的项目专属与敏感内容。

### 变更

- **`i18n-transform` 派发粒度改为单元级 1:1**：原「单批文件数上限（默认 ≤ 5）」的合并口径废弃，改为 **一个文件 = 一个改造子代理**——同一文件内跨多条改造线的内容由该子代理一次改完，不拆给多个子代理；**不存在「每批 N 个文件」的合并口径**；资源文件不参与单元计数；并发数（如需限速）只作**速率控制**，不改变 1:1 的对应关系
  - 同步改写：`SKILL.md`（角色 / 要求 3 / 阶段 0 第 3~4 步 / 阶段 1 标题与正文 / 阶段 2 / 验证 / 注意事项 / 输入）、`README.md`（编排流水线）、`references/subagent-prompts.md`（改造模板入参改为「指定的这一个文件」、报告格式由「批次 n/N」改为「单元：<文件路径>」）、`references/report-template.md`（「扫描与分批」→「扫描与单元划分」，批次数 → 单元数）
- **`AGENTS.md` 子代理调度约定补「派发粒度为单元级 1:1」**：一个单元（一个文件 / 一个模块 / 一个 Controller）一个子代理，不把多个单元合并给同一子代理；并发数只作限流，不改变 1:1 的对应关系

### 说明

- `check-rule-extract`、`module-batch`、`refactor` 本就是单元级 1:1（每个 Controller / 每个模块 / 每个重构单元一个子代理），其「并发窗口 / 并发上限」属于**速率控制**而非合并成批——本次未改其流程语义，只在 `AGENTS.md` 统一了表述。
- **历史提交脱敏**：清理了历史中的项目专属与敏感内容——业务术语例示、项目专属框架约定、项目技术栈痕迹、内部工具名、本机绝对路径；`Kibana` / `PostgreSQL` / `GaussDB` / `GitLab` 等**功能所需的产品名**与 `sys_user` / `del_flag` 等**通用占位示例**按仓库规范保留。为此重写了全部提交与 tag 的哈希（提交内容与版本号不变，仅脱敏），远程 `main` 与 9 个 tag 已同步更新；已有 clone 需重新 clone。

## [2.0.0] - 2026-09-14

技能标准化改造：统一命名与组织规范、补齐骨架与附属文件、修正脱敏与规范漂移，并新增两个技能（技能总数 17 → 19）。**技能名有破坏性调整，升级后旧名不可用**，对照表见下。

### 破坏性变更

- **技能改名（6 个）**：语序统一为「对象-动作」（名词在前、动词原形在后），消除同一仓库两种构词法并存；技能目录名与 frontmatter `name` 同步调整，旧名不再可用：

  | 旧名 | 新名 | 改名理由 |
  |------|------|---------|
  | `fix-bug` | `bug-fix` | 语序统一（"bug fix" 本身即标准名词短语） |
  | `create-mr` | `mr-create` | 语序统一 |
  | `commit-changes` | `commit-create` | 语序统一；与 `commit-review` 成对（创建提交 / 评审提交），消除两者混淆 |
  | `explain-project` | `project-explain` | 语序统一（同 `code-optimize` / `log-diagnose`） |
  | `lldwb-init` | `repo-init` | 技能名不携带仓库品牌；description 改述为「`/init` 的等价实现」 |
  | `controller-check` | `check-rule-extract` | 原名的动作落在 Controller 上，与实现（业务操作前置校验规则提取）不符 |

- 改名同步了四条分发路径（`config.json` / `.claude-plugin/marketplace.json` / `README.md` / `PLUGIN_README.md`）、`AGENTS.md` 的脚本路径、技能间交叉引用与 `install.py` / `uninstall.py` 的用法示例；本文件按惯例保留历史条目的旧名（记录当时事实）。

### 新增

- **新增 `i18n-transform` 技能（国际化改造）**：把硬编码文案改造为资源文件驱动，覆盖后端消息 / 前端文案 / 参数校验消息三条改造线
  - **编排流水线**：扫描分批（单批 ≤ 5 文件，资源文件不参与计数）→ 逐批派改造子代理 → 独立只读审查子代理（🔴 致命 / 🟡 警告分级）→ 独立验证子代理（Key 集合一致 / 编码 / 映射完整 / 命名规范）→ 汇总报告
  - **改造与审查分离**：审查与验证只读且不参与改造，两者对资源文件侧**刻意交叉覆盖**（以漏检为更大风险）；修复由独立子代理按最小改动执行、修复后必须复审；重试 ≤ 2 轮（全流程共享）后转「需人工介入」清单，不阻塞收尾也不静默放行
  - **零业务逻辑修改**：只动文案与资源文件，方法签名 / SQL / 权限注解 / 校验参数一概不动；校验消息中的数字改用框架占位符保持通用
  - **Key 规范**：命名结构（3~5 段按需取舍）、前缀归属表（按改造线分工、防前后端撞 Key）、多语言资源文件 Key 集合必须一致、非拉丁字符值侧转义而注释保留原文、追加不覆盖且改造前备份、本轮不收敛全局公共 Key
  - 含 3 份参考件：`references/key-conventions.md`（Key 与资源文件格式）、`references/subagent-prompts.md`（改造 / 审查 / 验证三类子代理提示词 + 高频缺陷速查 + 分级判据）、`references/report-template.md`（改造报告与遗留问题报告）
- **新增 `spec-route` 技能（开发规范路由）**：项目的开发手册是唯一权威源（SSOT），本技能只做「场景 → 章节」的路由与按段加载
  - 用 Grep 定位章节标题取行号 + Read `offset/limit` 只读目标段，**不全文加载**手册；引用规范时给出 `文件:行` 出处，不复制、不改写、不概括规则内容
  - 路由表（场景 / 章节序号 / 锚点标题 / 关键约束关键词）由项目填充并随使用回填；`references/route-table-template.md` 给出模板、填充步骤、读取指引与输出格式
  - 各技能正文里「项目提供的规范路由 skill」的泛称统一改为按技能名互指 `spec-route`，消除悬空引用
- **新增 11 份 references**（按「长模板 / 长清单 / 知识库才拆」的判据）：`bug-fix/root-cause-checklist.md`、`code-optimize/optimize-checklist.md`、`module-batch/{subagent-prompts,report-template,lessons}.md`、`check-rule-extract/output-and-rules.md`、`commit-review/review-checklist.md`、`unit-test/test-design-checklist.md`、`comment-supplement/comment-checklist.md`、`project-explain/explain-outline.md`、`frontend-error-diagnose/conclusion-template.md`、`feature-dev/plan-doc-template.md`

### 变更

- **统一 SKILL.md 七节骨架**：`角色 / 适用与边界 / 要求 / 执行步骤 / 验证 / 任务目标 / 注意事项 / 输入`；工具型技能允许在执行步骤后增列「用法 / 产出 / 描述结构」等节，基准节不得缺项。补齐了此前缺节的技能（`module-batch` 缺四节、`log-diagnose`、`db-query`、`check-rule-extract` 等），并把散在注意事项里的「技能边界」上提为独立的「适用与边界」节
- **统一 description 三段式**：`做什么 + 关键纪律` → `何时用（引用户原话）` → `即使未明确说"用 skill"…` → `边界互指`；触发场景关键词**只增不减**
- **统一 README 五段式**：`简介 / 使用（含边界）/ 能力 / 文件 / 依赖`
- **git 提交规则 SSOT 收敛**：8 个技能各自携带的 30~60 行重复条款收敛为**逐字一致的短段**（先审查 / 显式 add / 中文信息与标题正文空行 / 提交前后自检 / 默认提交后汇报 / 不自动 push），完整细则只在 `commit-create` 保留（提交环节的 SSOT 源，其余技能指向它）；同时消除已漂移的口径差异（重复的 `refact` 类型、三种确认口径、部分技能缺敏感信息自检）
- **`feature-dev` 引入变更提案制**：规划文档固定为 `proposal.md`（做什么 / 为什么）+ `design.md`（怎么做）+ `tasks.md`（可勾选步骤）三件套，任务完成一项**立即**勾 `- [x]`、收尾核对无未勾选项；「何时落盘三件套、何时只在对话里出方案」的判据见 `references/plan-doc-template.md`
- **`module-batch` 补全编排要素**：新增「要求 / 验证 / 注意事项」节、`## 任务目标` 纠位（原错嵌在提交规则之下）、子代理提示词模板（任务说明 / 异常回报 / 审查 / 修复）与收尾报告模板（含失败集合对比与需人工介入清单）；与 `refactor` 的分工写明（本技能供 worktree 并行机制，`refactor` 定改什么与怎么验收）；经验教训速查去技术栈化后抽到 `references/lessons.md`
- **`check-rule-extract` 减负**：正文由 28 KB 降至 23 KB，「最终输出模板」与「通用规则说明」抽到 `references/output-and-rules.md`；结构对齐七节骨架；CLI 用法示例中的本机绝对路径改为占位符
- **`commit-review` 检查维度清单化**：七个维度（逻辑与边界 / 依赖影响面 / 分层与耦合 / 契约变更影响面 / 废弃 API / 风格与仓库约定一致性 / 提交信息规范）连同「怎么查 → 命中后怎么写进结论」抽到 `references/review-checklist.md`，按「严重 / 规范 / 建议」分级并留项目扩展钩子
- **`unit-test` 用例设计与失败归属判定**抽到 `references/test-design-checklist.md`（用例设计 / 隔离策略 / 必须遵守与禁止 / 失败归属 / 验证循环）
- **`refactor` 落盘路径统一**为 `<项目根>/.tasks/refactor/`（此前契约写 `.claude/refactor/`、报告写 `.tasks/refactor/`，两处不一致）；`references/contract-template.md` 新增「子代理公共约定」一节（改造 / 审查 / 修复三类子代理共用）

### 修复

- **脱敏违规**：`bug-fix` 提交规则里把具体业务缩写当例示——整句删除；`check-rule-extract` CLI 示例里的本机绝对路径改为 `<输出目录>` 等占位符；`i18n-transform` 的 Key 示例去掉业务缩写
- **规范漂移**：`code-optimize` 与 `module-batch` 提交类型表中的非规范类别 `refact` 统一为 `refactor`；`module-batch` 正文提及的具体 AI CLI 工具名删除
- **结构缺陷**：`module-batch` 的 `### 任务目标` 从「提交 git 规则」节下提升为 `##`
- **文档与实现不符**：`db-query` README 的「SQL 白名单」改为与实际一致的「脚本拦截」（脚本实现为写关键字黑名单判定）；`log-diagnose` 文档中显式 `--config` 的产物路径与脚本实际输出对齐（`~/Downloads/<env>/`，不拼 `log-diagnosis` 段）并补 `--kw` 参数说明；`mr-create` 的校验结论来源写明为脚本 stdout
- **技能自包含**：`log-diagnose` 正文引用 `commit-review` 的脚本路径改为按技能名互指；全仓清理跨技能文件路径引用
- **补齐丢失的约束**：`repo-init` 补回「提交信息不带 `Co-Authored-By` 类署名」；`unit-test` 与 `check-rule-extract` 的提交口径恢复为「默认提交后汇报」（此前被静默收窄为条件提交）；`check-rule-extract` 补回 `<菜单权限表>` 与 `<扫描范围>` 的占位符定义

## [1.6.0] - 2026-09-14

新增 `refactor` 技能，把多个实际项目中沉淀的「结构改造、行为不变」编排实践抽象为通用重构工作流；同步收紧 `code-optimize` 的触发边界。

### 新增

- **新增 `refactor` 技能**（技能总数 16 → 17）：重构（结构改造、对外行为不变）的标准工作流
  - **契约先行（SSOT）**：目标形态、范围与单元划分、不可变更项（路径 / 签名 / 返回内容 / 异常行为 / 关键注解 / 视图名等，逐项可核对）、命名归属、验证命令固化为一份契约文件，编排方与所有子代理加载同一份；子代理为全新上下文须自行加载；契约确认前不改代码、变更须回用户确认（模板 `references/contract-template.md`）
  - **基线先行**：改造前建立可复跑的测试基线（既有测试 / 新生成契约级测试 / 契约快照降级，三档）；基线测试须满足「重构不变性」——只经对外契约交互，禁内部调用断言、禁替换被测装配、禁改写既有通过用例（含覆盖度判定与生成提示词要点）；基线未通过前不得动代码（规则 `references/test-baseline.md`）
  - **改造与审查分离**：改造子代理执行；未参与改造的独立只读子代理以对抗性立场审查——逐方法做「原逻辑 → 新逻辑」映射，按行为等价性 / 迁移完整性 / 保留完整性 / 新产物规范 / 依赖与编译风险 / 易错模式 / 清理项 / 测试不变性八维核对，输出严重 / 规范 / 建议分级报告；修复由独立修复子代理按最小改动执行，修复后必须复审，不得由改造者自证（模板 `references/agent-prompts.md`）
  - **验证循环**：编译 → 审查 → 测试，任一步产生代码改动即回到编译重跑全部三步；默认最多 3 轮，超出交用户介入、不静默放行；主代理串行执行编译 / 测试（避免并发构建冲突），改造 / 审查按单元并行派发
  - **失败分类**：既有且与本次无关的失败记入失败集合、标注不阻断，阶段三对比「一致或缩小即未破坏行为」；本次引入的回归必须修复
  - **契约快照脚本** `scripts/contract-snapshot.py`（仅标准库）：按语言（java / ts / js / py / generic）机械抓取改造前后的对外契约痕迹（公开签名、路由与关键注解、导出符号，引号感知去注释 + 空白归一化 + 去重排序），`capture` 落 JSON 快照、`diff` 输出新增 / 删除 / 变更文件与条目清单——**只取数不判定**，差异是否可接受由 agent 依据契约判定；用于防「路径 / 签名 / 注解被悄悄改动」的漏检（行级粗筛，跨行签名改写仍需人工与审查子代理核对）
  - 边界互指：小范围优化（可读性 / 重复代码抽取 / 局部性能）转 `code-optimize`；新增或改变对外行为转 `feature-dev`；缺陷修复转 `fix-bug`；需要多模块并行隔离执行时与 `module-batch` 组合（本技能定改什么与怎么验收）
- 同步技能清单分发路径：`README.md` / `PLUGIN_README.md` 技能表、`.claude-plugin/marketplace.json`（version 与 skills 数组）与 `config.json` 启用项

### 变更

- **`code-optimize` 让位重构**：description 与正文收敛为「小范围优化」（重复代码抽取、局部性能提升、可读性提升、命名与局部结构改进），移除「只要涉及代码优化/重构/清理就应使用」的宽口径；新增技能边界条目——结构性改造、分层/职责重构、实现迁移、批量同构改造指向 `refactor`；`README.md` 同步

## [1.5.0] - 2026-09-14

新增 `create-mr` 技能，补齐「提交改动 → 生成合并请求」链路的最后一环；描述与创建参数均以官方 CLI 文档实测核证。

### 新增

- **新增 `create-mr` 技能**（技能总数 15 → 16）：生成合并请求（MR/PR）的标准工作流——解析分支（源默认当前分支；目标默认探测 `origin/HEAD` → `main`/`master`，要求先确认默认主分支名）→ 前置校验 → 自动生成四段式描述 → 确认后经 `gh` / `glab` 创建
  - **防空合并请求**：前置校验覆盖「是 git 仓库 / 源与目标分支存在 / 源与目标非同一提交 / 有共同祖先 / 存在有效差异」五项，任一不满足即非零退出且不产出素材；「有领先提交但无文件差异」（空提交、仅合并）单列告警，避免描述里出现并不存在的代码改动
  - **描述自动生成**：综合用户补充说明与该分支相对目标分支的提交记录与变更范围撰写，至少含「变更背景/目的、主要改动点、影响范围、测试验证情况」四段；要求每条有出处、**测试验证情况不得编造**；仓库存在 PR/MR 模板时（`.github/PULL_REQUEST_TEMPLATE*`、`.gitlab/merge_request_templates/*`）以模板章节为准
  - **平台创建**：GitHub `gh pr create --base/--head/--title/--body-file`、GitLab `glab mr create --source-branch/--target-branch/--description-file/--yes`，并写明两条实测坑——`--head` 会跳过 gh 的建分支/建 fork 交互（源分支未推送时直接失败，须先推送）、`glab --fill` 会顺带 push 分支并覆盖描述（禁用）；无 CLI 或未识别平台时输出描述全文与手工创建页链接（GitHub `compare` / GitLab `merge_requests/new`）
  - **远端状态取数**（只报事实不判定）：未推送 / 已推送但本地领先 / upstream 一致 / 仅存于远端 / 同名分支提交不一致；源分支未推送时**征得用户同意后**才 `git push -u origin <源分支>`
  - **描述基线**：diff 以远端目标分支为基准（远端才是合并请求的基线），本地与远端不一致时素材提示先 `fetch` 再重算
  - 边界：创建前展示标题与完整描述待确认；不 merge / 不删分支 / 不 `--force` / 不改代码；素材与描述落在 `<仓库根>/.tasks/create-mr/`，目录未被忽略时脚本提示（不入库）
  - 含取数脚本 `scripts/prepare-mr.py`（只取数不判定，不创建合并请求）：分支解析与校验、`--pretty=medium` 保留标题与正文空行的提交记录、按目录聚合的变更范围、文件清单、diff（默认截断 400 行 + 完整 `raw.diff`）、平台识别与命令模板、模板探测
- 边界互指：`commit-changes` 与 `feature-dev` 的「不自动 push / merge / 建 PR」补「用户要求建 MR/PR 时转 `create-mr`」
- 同步技能清单分发路径：`README.md` / `PLUGIN_README.md` 技能表、`.claude-plugin/marketplace.json`（version 与 skills 数组）与 `config.json` 启用项

## [1.4.0] - 2026-09-12

按三份真实开发会话的复盘结论加固技能：补"提交信息结构"与"确认无应答"两类缺口，把子代理复核的口径从"仅代码"放开到通用"事实源"，并把两份参考件的读取写进执行步骤。

### 修复

- **提交信息结构**（`commit-changes` / `feature-dev` / `doc-sync` / `fix-bug` / `lldwb-init` / `code-optimize`）：明确「标题与正文之间空一行」（缺空行时 git 会把正文并进标题，`%s` 显示成一行、`%b` 为空）；多行信息改用 Write 落消息文件 + `git commit -F`（内联 heredoc 承载多行文本偶发丢空行）；新增提交后 `git log -1 --format='%s'` / `%b` 复核，信息被并入标题时 `--amend -F` 修正
- **提交前后自检**（`feature-dev` / `doc-sync` / `fix-bug` / `lldwb-init`）：补敏感信息扫描（凭据 / token / 内网地址 / 真实数据样例 / 本机绝对路径）——此前只有 `commit-changes` 有这一项
- **技能边界互指**：`feature-dev` 补"纯文档产出转 `doc-sync`"；`doc-sync` 补"代码改造转 `feature-dev`"；`fix-bug` 与 `comment-supplement` 互指分工（改动仅限注释层面 vs 注释与逻辑/结构改动并存）
- **确认请求无应答**：新增处置规则——可逆改动按推荐方案继续，并在汇报首段标注"该决策未获用户确认"；删除、历史改写、依赖或接口变更等不可逆/影响面大的改动停下等待（`commit-changes` / `feature-dev` / `doc-sync` / `fix-bug`）；`lldwb-init` 更严：询问无应答时不擅自提交，保留工作区改动待确认
- **提交确认口径统一**：默认"提交后汇报（sha + 文件清单 + 提交信息）"，含删除 / 重命名 / 生成物 / 二进制文件或拆分方案不唯一时才先给方案确认；修正 `code-optimize`、`controller-check` 与之冲突的"提交前先确认"措辞；`lldwb-init` 的"提交前先问"作为显式例外保留
- **`lldwb-init` 产出指引失真**：`references/output-templates.md` 的提交风格采集命令由 `git log --format='%s%n%b'` 改为 `git log -n 10 --pretty=medium`——前者看不出标题与正文之间的空行，抄进指引会把"正文跟在标题下一行"写成范例；并要求示例保留空行
- **`lldwb-init` 提交边界**：本技能自身的提交只含 `AGENTS.md` / `CLAUDE.md`；初始化过程中用户追加的改动（补 `README.md`、调构建配置等）按 `commit-changes` 的规则另起提交，不与指引文档混在一个提交里
- **`commit-changes` 拆分判定**：补「仓库尚无任何提交（首次提交）」一档（按最终工作区状态一次成型，不制造中间态）；新增「历史与对象清理默认不做」（`reflog expire` / `gc --prune=now` / `filter-repo` / 交互式 rebase 需先说明不可逆后果并取得明确同意，事后 `git fsck` 核验）
- **`fix-bug` 静态缺陷**：补"无法复现的静态缺陷（死代码、注释与实现漂移、规范偏差）以**现状取证**替代复现——全仓引用计数、定义处与调用处对照"
- **`feature-dev` / `fix-bug` 验证命令**：补"单模块项目去掉 `-pl <模块> -am`"
- **`commit-review`**：提交信息检查项补"标题与正文之间应有空行"

### 变更

- **`doc-sync` 复核口径泛化**：`references/verify-agent.md` 入参由"文档路径 + 代码范围"扩展为"文档路径 + **事实源**"（代码 / 外部仓库 / 日志 / 配置 / 会话记录），输出改「证据位置」，并写明事实源非代码时按同一结构替换措辞、证据要求不变；`SKILL.md` 的复核小节补"按同步方式调度（范围很大时才后台 + 轮询）"
- **`feature-dev` 参考件进入执行步骤**：核证前读 `references/feasibility-check.md`、实测前读 `references/e2e-verify.md`（原文只写"详见"，两份参考件在真实会话中被跳过）
- **`feasibility-check.md`**：新增"框架/依赖大版本升级先核命名与包名"（starter 名、包名、异常继承关系随大版本变化，按旧版本记忆写代码只会得到"找不到符号"）；新增取材通道降级（`WebFetch` 可能被域名安全策略拦截 → 本地 `curl` / 抓取类 MCP / `git clone`）与大文档先落盘再 `grep`
- **`e2e-verify.md`**：§四补"取证方式自检"（断言为负先看原始产物；禁止 `A | 解析器 || A` 式兜底以免重复发起请求；手工验证重复第二次即固化为脚本）；新增小节「五、自然语言 / 大模型驱动的链路：断言设计」（断言落在确定性事实、提问按"最小必然触发"构造、分清"被测行为不符预期"与"断言写死了一种合理实现"）
- 各技能 `README.md` 与仓库 `README.md` / `PLUGIN_README.md` 技能表同步上述边界与提交口径；`.claude-plugin/marketplace.json` 版本随之更新

## [1.3.0] - 2026-09-12

### 新增
- 新增 `lldwb-init` 技能（技能总数 14 → 15）：仓库指引初始化（`/init` 的 lldwb 版）——指引正文一律写入 `AGENTS.md`（唯一权威源，与既有内容合并、不覆盖），`CLAUDE.md` 只保留指向声明、不承载正文
  - 流程要点：前置检查（git 仓库根 / 既有指引 / `.gitignore` 是否忽略两份文档）→ 探索仓库并用 `git` / `grep` 核实事实 → 归纳"读多个文件才能拼出"的架构结论（每条标注出处）→ 按骨架动笔（既有 `AGENTS.md` 只降层级、文本零改动；既有 `CLAUDE.md` 的实质内容先并入再收敛为指向）→ `git status` / `git check-ignore` / `git diff` 三项核验 → 询问用户后提交
  - 红线：命令、路径与"唯一入口 / 共享模块 / 只改一处"类断言动笔前必须有佐证；不编造章节、不写通用开发实践、不罗列文件树；探索中发现的异常（`.gitignore` 误命中、逻辑两处重复）只记入「已知坑」并汇报，不擅自修
  - 含参考文件 `references/output-templates.md`（`AGENTS.md` 章节骨架与反例、`CLAUDE.md` 指向模板、合并既有内容的做法、动笔前核验清单）
- 同步技能清单分发路径：README.md / PLUGIN_README.md 技能表、`.claude-plugin/marketplace.json`（version 与 skills 数组）与 `config.json` 启用项

## [1.2.0] - 2026-09-12

### 新增
- 新增 `feature-dev` 技能（技能总数 13 → 14）：需求开发全流程工作流（需求分析 → 方案设计 → 规划文档 → 分层实现 → 验证 → 提交），沉淀自跨前后端、涉及外部依赖的完整开发实践
  - 流程要点：先理解再动手、先出方案再改（关键决策点交用户确认）；外部依赖能力/配置绑定/协议行为动手前用证据核证；分层小步实现；编译 → 单测 → 前端语法 → 端到端实测分层验证；部署-实测-证据定位根因-修复的迭代闭环
  - 含两个参考文件：`references/feasibility-check.md`（动手前可行性核证：三方组件 / 配置绑定 / 协议行为 / 契约）、`references/e2e-verify.md`（端到端实测取证：部署节奏 / 浏览器取证 / 日志 / 收尾检查）
- 同步技能清单分发路径：README.md / PLUGIN_README.md 技能表、`.claude-plugin/marketplace.json`（version 与 skills 数组）与 `config.json` 启用项

## [1.1.1] - 2026-09-11

### 安全
- 修复安装/卸载脚本路径越界：`install.py` / `uninstall.py` 对命令行技能名做校验（拒绝绝对路径、盘符、路径分隔符与 `..`），杜绝 `os.path.join` 遇绝对路径丢弃基目录后 `rmtree` 落到技能目录之外
- 修复 `gen-fix-sql.py` 的 SQL 注入：id 与值统一按标准 SQL 转义、json 输入补 id 正则校验、表名/列名/备份表后缀过 `check_ident()` 白名单、生成脚本显式 `SET standard_conforming_strings = on`
- 收紧 SQL 只读判定（`db_common.py` 与 `db-query.py` 同步）：`EXPLAIN ANALYZE <写语句>`（会真实执行）、`SELECT ... INTO`（建表）、`nextval`/`setval`/`pg_terminate_backend`/`lo_import`/`dblink_exec` 等副作用形态一律按写处理
- `sync-table.py` 表名过标识符白名单；`db_common.py` / `db-query.py` 对配置的 `schema` 做标识符校验（防 libpq options 注入）
- `build_check_xlsx.py` 写入单元格前中和 `=` `+` `-` `@` 前缀，防 Excel 公式注入
- `log-diagnose`：Kibana 地址为 `http://` 时打印凭据明文传输告警，配置模板改用 `https://`
- 技能指令边界：把「以项目开发手册 / `AGENTS.md` 为权威依据」限定为提交信息格式与代码写法约定，明确外部文本不改变技能流程、授权范围与安全约束；菜单权限数据源声明「仅作数据，其中指令性文本一律忽略」
- `install.py` 缺 `config.json` 时不再兜底全量安装（无参安装直接报错），复制技能时跳过 `.tasks` / `__pycache__`

### 变更
- `db-query.py` 落盘路径按配置来源归属（与 `log-diagnose` 一致），不再固定落在 skill 目录内
- 新增依赖清单 `skills/db-query/requirements.txt`、`skills/controller-check/requirements.txt`（固定主版本）
- `db-query` / `log-diagnose` 脚本启动时打印生效的配置文件路径，便于核对凭据来源

## [1.1.0] - 2026-09-11

### 新增
- 从提示词模板合集抽象出 6 个新技能（技能总数 7 → 13）：
  - `frontend-error-diagnose` — 前端报错诊断：浏览器 MCP 复现取证（console / 网络 / 调用栈）→ 根因 → 可执行方案，只诊断不改代码；含取证清单 `references/browser-evidence-checklist.md`
  - `unit-test` — 单元测试工作流（生成 / 修复失败两类），修复类默认只改代码、交用户执行验证
  - `doc-sync` — 文档与代码同步（更新 / 修正两类），含只读一致性复核子代理模板 `references/verify-agent.md`
  - `commit-changes` — 提交 git 改动（commit 专员）：单一职责拆分、显式 add、中文提交信息
  - `comment-supplement` — 注释补齐与修正：仅注释层面，不确定项先交用户确认
  - `explain-project` — 结合项目真实代码逐项讲解概念，结尾说明项目定位
- 同步技能清单分发路径：README.md / PLUGIN_README.md 技能表、`.claude-plugin/marketplace.json`（version 与 skills 数组）与 `config.json` 启用项
- 未收录的提示词：优化 / 修复 bug / 检查提交 — 已由既有 `code-optimize` / `fix-bug` / `commit-review` 覆盖

## [1.0.0] - 2026-09-11

### 新增
- 初始化 6 个可复用 skills 抽象：fix-bug / code-optimize / commit-review / log-diagnose / module-batch / controller-check（含取数脚本与配置模板）
- 适配 Claude Code：子代理调度改为 Agent 工具（`subagent_type: general-purpose`），新增 `.claude-plugin/marketplace.json` 支持插件安装
- 新增 `db-query` 技能（第 7 个）：数据库查询（生产只读三重保障），log-diagnose / fix-bug 接入查库佐证
- 新增 `db-query` 取数下游配套脚本：修复 SQL 生成（gen-fix-sql.py）、SQL 文件试跑（run-sql-file.py）、跨环境表同步（sync-table.py）
- 新增安装/卸载脚本（install.py / uninstall.py 及 .sh/.bat 包装）、config.json 技能启用配置、PLUGIN_README.md
- 每个技能补充 README.md（简介、用法、文件与依赖说明）

### 变更
- log-diagnose / fix-bug：数据佐证与查库验证环节引用 db-query skill
- module-batch：子代理直接用 Agent 工具执行改造，不再经外部 AI CLI 中转

### 安全
- 敏感凭据（Kibana / 数据库）仅存 gitignored 的本地配置文件，不入库；db-query 生产只读（SQL 白名单 + 会话只读 + 账号只读）
