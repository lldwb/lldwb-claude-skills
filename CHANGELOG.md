# Changelog

## [2.5.2] - 2026-09-21

按 github-desktop-zh-cn 仓库一次多单元重构会话（契约驱动的整体重构 + 跨会话续跑 + 独立复审）的实证教训，补强 `refactor` 技能的契约口径、基线体系与审查纪律；无新增技能，技能 `description` 未变。

### 变更

- **`refactor` 契约检查命令先自验证**：写进契约的每条检查命令（grep / 脚本 / 静态检查）先在改造前的代码上跑一遍——确认既不命中契约要求原样保留的代码（命令与自己的要求打架），也能抓全目标形态（拆成多行的调用、别名引用都算漏抓）；抓不全或误命中先修命令口径、不改代码迁就 grep，改不动的盲区作为已知边界写进契约与报告（要求 7 与 `references/contract-template.md` §5）。实测：契约里三处残留检查命令与自身要求不自洽（误命中要求保留的代码、前缀匹配带出例外、改造前就抓不全），两轮审查被绊住、用户裁决 3 项
- **`refactor` 死代码 / 死导出判定按全仓扫描**：扫描面必须含测试、工具脚本、构建脚本、GUI 层等全部可能的引用方，不只被重构目录——只扫被重构目录会把测试引用漏成假死代码，按契约删掉即断链（阶段 0 第 1 步）。实测：某共享符号被测试引用 8 次，摸底只扫源码目录而误判为死导出，靠派发前全仓复核救回
- **`refactor` 多单元项目每个有改动的单元都要有自己的独立审查**：编排方亲自验收不能替代任何一个单元的对抗性审查（规模适配条款）。实测：被省掉独立审查的单元，恰是问题最后漏出的那个
- **`refactor` 测试基线「三类」扩为「四类」**：新增第 ③ 类「输出快照」——无测试但入口有确定性文本输出（CLI 命令、`--help`、报告类输出）时，改造前采样命令输出落盘、改造后 diff 逐字一致即行为未变；并注明采样与对照产物别放测试收集器递归得到的位置（`node --test` 之类收集器对 `*.test.js` / `*-test.cjs` 整目录递归收集，对照用的旧测试副本与解包旧树会把用例统计从 142 撑到 257）；`SKILL.md` 阶段 1 增加对应入口、阶段 3 契约核对增加快照不可用时的替代口径，`references/report-template.md` 基线形态行同步（`references/test-baseline.md`）
- **`refactor` 新增「护栏的反向实测」一节**：新护栏（回归用例、冒烟判据、自动化断言）落地时至少做一次反向实测——把被防护的缺陷手工注入（正确实现改回错误形态），确认护栏真的变红、失败原因指向根因，还原后核对字节一致；只看护栏在正确代码上全绿，证明不了它能拦住它声称要拦的东西，判据为间接信号（哨兵回显等）时这是唯一能证明因果的证据（`references/test-baseline.md`）
- **`refactor` 报告遗留清单办结后回填处置状态表**：逐条写处置方式 + 对应提交，原始建议文字保持原样不改——改没改、怎么改的一眼能看出来；实际做法与当初建议形态不同时（如建议新增独立 CI 步骤、实际做成既有冒烟里的一条判据），写明形态差异与覆盖的根因一致（`references/report-template.md`「遗留与后续」）
- **`refactor` 写明 `contract-snapshot.py` 的语言局限**：该脚本抓取模式面向 Java 形态（路由 / 注解），对 JS / TS / Python 等项目可能命中 0 条——阶段 1 降级条款与阶段 3 契约核对补明此时降级为「测试基线 + 机械 grep 清单 + 输出 diff 快照」组合取证；脚本本身未改动
- **`refactor` 中断续跑先核现场**：会话中断（限流 / 崩溃 / 上下文耗尽）后接续，先核 HEAD 是否被并行线推进、工作区哪些改动已在盘上、中断的子代理产出是否已落盘且完整（往往已写完，续跑而非重做）；中断前留在暂存区 / 工作区的改动会混进后续提交，提交前逐笔核对归属（注意事项）

### 说明

- 本次为既有技能（`refactor`）的表述补强与流程补环节，无新增技能、`description` 未变，按分级取**小版本**。
- `.claude-plugin/marketplace.json` 版本号 2.5.1 → 2.5.2

## [2.5.1] - 2026-09-20

给 `git-worktree` 补「合回当前分支」环节——判例来自 github-desktop-zh-cn 仓库「worktree 隔离修复 CI 失败 → 合回 → 删除 → 推送」的完整收尾会话（用户要求「完成后合进当前分支」「删除工作树和分支」），此前技能只覆盖创建 / 列出 / 删除 / 迁移，合回无流程指引。

### 变更

- **`git-worktree` 补合回当前分支环节**：`description` / 适用与边界补「把 worktree 分支合回当前分支」触发语；要求新增「合回先判历史形态」（`git log --oneline --merges` 判纯线性——纯线性历史用 rebase + `--ff-only` 快进、不造合并提交，已有合并历史时按仓库规范或用户偏好选 merge 方式）；执行步骤新增 `merge` 节（两侧干净 → 变基拉平 → 快进合并 → 两树 `hash-object` 逐一比对 + 重跑验证命令 → 用户要求删除时 `worktree remove` + `branch -d` 安全删分支），同步命令表 / 验证 / 注意事项 / 任务目标 / 输入

### 说明

- 本次为既有技能流程补一步（小修小补），按分级取**小版本**。
- `.claude-plugin/marketplace.json` 版本号 2.5.0 → 2.5.1

## [2.5.0] - 2026-09-20

新增**技能路由判断**技能：任务描述无法唯一确定技能时（用户未指定 / 多技能重叠 / 边界模糊），由 AI 判断给出推荐——判例来自 github-desktop-zh-cn 仓库「给 AGENTS.md 增补分支命名规范」的会话（用户以 /feature-dev 发起纯文档任务、且该会话因命令包装被会话抽取脚本漏读用户原话）；同轮给 `repo-init` 增补分支命名规范可选条款与「规范条款先对齐再落笔」要求、显化「增补既有 AGENTS.md 规范条款」的适用场景，并修复 `session-summary` 抽取脚本对技能命令发起的会话漏抽用户输入的问题。

### 新增

- **新技能 `skill-router`（技能路由判断）**：盘点发现路径下实际可用的技能，按任务特征归类（改代码 / 只查不改 / 写文档 / git 动作 / 编排 / 查数 / 产出形态），用各技能 `description` 的边界互指排除，AI 判断给出「推荐 + 理由（引用 description 原句）+ 备选」——**不确认时由 AI 判断**，不问"你想用哪个"；两轮收敛不了列 2~3 个候选交用户拍板。只判断不代执行；推荐落在含删除 / 历史改写 / 强推等危险动作的技能时，把该技能自带的确认要求原样带上，路由不绕开安全流程。含 `references/skill-catalog-template.md`（分类路由表模板 + 通用决策口诀 + 易混对清单，项目有自定义技能时按表补行）
- **`repo-init` 增补分支命名规范可选条款**：新增「要求 10 规范条款先对齐再落笔」——规范是给项目的建议、不是读仓库读出来的事实，动笔前先与用户对齐（是否写 / 格式用哪套 / 存量动不动）；给出已实证的分支命名参考格式 `<type>/<内容>-<修改者>-<MMDD>`（type 限定词表、内容小写连字符、修改者 git 用户名、时间两位月两位日，`main` 与 `backup/` 类不受约束），单主干仓库可不写、存量分支默认**只规范不动存量**；`references/output-templates.md` 骨架同步补可选条款示例段

### 变更

- **`repo-init` 显化「增补既有 AGENTS.md 规范条款」的适用场景**：`description` 补「给仓库加个分支 / 提交规范」触发语，「适用与边界」补增补规范条款的说明——此前同类任务（实证：github-desktop-zh-cn 分支命名规范增补）用户走的是 `/feature-dev`，本技能边界不够显眼

### 修复

- **`session-summary` 的 `extract-session.py` 漏抽技能命令发起的用户输入**：`--user` 模式「跳过所有以 `<` 开头的文本」的过滤规则，把 `<command-message>…<command-args>` 包装的整条用户消息丢弃——技能启动的会话输出 0 条用户消息、时间线也不显示用户原话，取证只能靠 assistant 转述、未转述即丢源。改为仅对 `<command-message>` / `<command-name>` 开头的消息解析并提取 `<command-args>` 内的用户参数，纯命令注入仍跳过，用户粘贴的 XML 等 `<` 开头文本不再误杀。实测：被总结的会话（`/feature-dev` 发起）由 0 条恢复为 1 条用户原话

### 说明

- 本次为**新增技能**（`skill-router`，含 references 分类路由表）+ 既有技能能力增强（`repo-init`）+ 脚本缺陷修复（`extract-session.py`），按分级取**中版本**。
- 技能数量 27 → 28，两条分发路径（安装脚本启用清单、`marketplace.json` 的 `skills` 数组）均已同步；`config.json`（本地启用清单，不入库）按默认启用自动补全，无需改动。
- `.claude-plugin/marketplace.json` 版本号 2.4.6 → 2.5.0

## [2.4.6] - 2026-09-19

给 `session-summary` 的会话抽取脚本补「压缩摘要过滤」（长会话的 `--user` 输出里 harness 注入的续接摘要占六成，真实用户消息被淹没、总结时被迫另写辅助脚本过滤），并在 `AGENTS.md` 发版规则补「用户明确要求时发版条目可改」的例外条款——判例来自 github-desktop-zh-cn 仓库 v0.3.0（用户行使例外权修改发版条目，该仓库已回流同款条款）。

### 变更

- **`session-summary` 的 `extract-session.py` 默认过滤上下文压缩摘要**：harness 在上下文耗尽时以用户消息形式注入「This session is being continued」续接说明，长会话里动辄占 `--user` 输出一半以上行数、且内容与 assistant 尾部文本高度重复。`mode_user` 识别其起始文案并跳过，summary 注明「已过滤 N 条上下文压缩摘要」；新增 `--with-summary` 保留。`--timeline` 不动（压缩点是会话真实事件）。实测：30 MB 会话的 `--user` 从 52 条降到 22 条真实用户消息；SKILL.md 用法描述同步
- **`AGENTS.md` 发版规则补「用户明确要求」例外**：「发版条目一经创建不得在后续提交中修改」增加例外条款——用户明确要求时，改时 CHANGELOG 条目与 GitHub / gitee 两处 Release 正文一起改并逐字复核（GitHub 侧由 `release.py` 重写、gitee 侧由 `create-gitee-release.py` 回写）；判例为 github-desktop-zh-cn 仓库 v0.3.0，该仓库已按同一规则回流

### 说明

- 本次为技能脚本缺陷修复 + 仓库规则补充（无技能增删、无流程语义变更），按分级取**小版本**。
- 技能数量仍 27、技能名与分发路径不变；`config.json`（本地启用清单，不入库）无需改动。
- `.claude-plugin/marketplace.json` 版本号 2.4.5 → 2.4.6

## [2.4.5] - 2026-09-19

给 `session-summary` 补两条审视项（未提交改动去向、回流判据澄清），给 `app-packaging` 的坑位清单补「内置 token 不触发 release 事件」论据，并在 `AGENTS.md` 已知坑固化两条实测的通用开发坑（Windows zip 解压、跨主机重定向去凭据）——均出自一次「在别的仓库操作、产出未提交即被后续会话取代」的会话实证。

### 变更

- **`session-summary` 第 2 步补「未提交改动须注明去向」**：会话结束时未提交的工作可能在会话后被 `git reset` / 覆盖 / 方案被否决而消失（实测发生过：产出未提交，会话结束不久即被 reset 丢弃、方案被后续会话否决），需要保留就先落盘快照再总结
- **`session-summary` 第 4 步补回流判据澄清**：会话记录文件所在的项目目录 = 启动时的 cwd，**不代表操作对象**——判断是否回流以操作对象（提交所属仓库 / 时间线里 `cd` 的目标仓库 / 讨论目标）为准，别因「文件在本仓库目录下」就跳过回流
- **`app-packaging` pitfalls「令牌分工」节补第三条理由**：内置 token 建 Release 产生的 `release: published` 事件**不触发**新的 workflow 运行（`GITHUB_TOKEN` 驱动不了 `on: release` 自动化）——为「建 / 改 Release 用 PAT」再添一条不依赖署名场景的论据
- **`AGENTS.md` 已知坑补两条通用开发坑**：① Windows 下解压 zip 用系统 bsdtar（`C:\Windows\System32\tar.exe`），Git Bash 的 GNU tar 读不了 zip、还会把 `E:\...` 绝对路径当远程主机；② 下载带鉴权的重定向资源时**跨主机重定向必须去掉 Authorization**，并整体缓冲后再解码

### 说明

- 本次为文档约定与技能审视项的补充（无技能增删、无流程语义变更、无脚本改动），按分级取**小版本**。
- 技能数量仍 27、技能名与分发路径不变；`config.json`（本地启用清单，不入库）无需改动。
- `.claude-plugin/marketplace.json` 版本号 2.4.4 → 2.4.5

## [2.4.4] - 2026-09-18

固化「tmp/ 等过程目录默认不固化」的约定——gitignored 的 `tmp/`、`.tasks/` 里的中间脚本默认视作没有固化，反复复用的才视情况固化入库。

### 变更

- **`AGENTS.md` 跨技能共用约定补「`tmp/` 等过程目录默认不固化」**：`tmp/`、`.tasks/` 里的中间脚本（探针、验证器、mock 测试）默认视作没有固化——清掉即失、下次会话不保证还在；**反复复用**的要**视情况固化**（参数化去掉硬编码路径/凭据、自包含后入库并登记用法），判据是「换个电脑还用得上吗」
- **`session-summary` 注意事项补同一条审视项**：审视会话时把「本会话反复复用的中间脚本是否固化」列入教训落点判断（该技能会话实证：CI / Release 运维探针固化到 `build/tools/`）；README 能力段同步

### 说明

- 本次为文档约定与技能审视项的补充（无技能增删、无流程语义变更、无脚本改动），按分级取**小版本**。
- 技能数量仍 27、技能名与分发路径不变；`config.json`（本地启用清单，不入库）无需改动。
- `.claude-plugin/marketplace.json` 版本号 2.4.3 → 2.4.4

## [2.4.3] - 2026-09-18

给 `app-packaging` 补 CI 发 Release 的 GitHub 机制坑位清单——全部为跨项目通用的实测行为（在目标项目 v0.2.0 发版中反复踩到）。

### 变更

- **`app-packaging` 新增 `references/github-release-pitfalls.md`（发 Release 的 GitHub 机制坑位清单）**：10 个实测坑——① 令牌分工：控制面走作者 PAT（署名才是本人）、数据面走内置 token（附件传输稳定，PAT 上传实测三次尝试全败）；② `gh release create` 先建草稿后发布，草稿对匿名接口不可见、会误判「已存在」而跳过；③ 草稿复用续传（按 digest 比对跳过已传、缺什么补什么），且**只复用自己建的**——署名在建 Release 那一刻定死；④ 逐个上传 + 各自重试 + 全部成功才发布，失败附件名与 gh 错误原文写进 `::error::` 注解（**注解匿名可读，job 日志要仓库权限**）；⑤ Release 更新接口只认数字 id，按 tag 的 `PATCH` 是 404；⑥ `make_latest` 默认 true 会抢 Latest，归属按版本号现算不记忆；⑦ `actions/checkout` 会清空既有工作区，跨步骤传文件别在 checkout 前落盘；⑧ `workflow_dispatch` 读默认分支的 yml，改完不推选不到新任务；⑨ 显式 `permissions` 会把未列出的权限清零（如 `gh run download` 需 `actions: read`）；⑩ GitHub 没有重命名附件的接口，改名只能先传新名、校验和就位后再删旧名
- **`app-packaging` 的 `SKILL.md` / `README.md` 同步引用**该清单

### 说明

- 本次为**技能内容补充**（新增 1 个 references 坑位清单，无技能增删、无流程语义变更、无脚本改动），按分级取**小版本**。
- 技能数量仍 27、技能名与分发路径不变；`config.json`（本地启用清单，不入库）无需改动。
- `.claude-plugin/marketplace.json` 版本号 2.4.2 → 2.4.3

## [2.4.2] - 2026-09-17

把 `.tasks/` 里**有长期复用价值**的过程产物固化进仓库：新增 2 个仓库级工具（技能仓库自检、gitee 镜像发行版补齐）、1 个技能脚本（会话记录抽取）、1 组技能自测（`mr-create` 的 38 项用例）与 1 个历史改写模板，同时给 `release.py` 补上 Release 正文的回读与写回通道，并把过程中的规则沉淀进文档（批量替换教训、技能骨架与写法基准）。

### 新增

- **`check-skills.py`（技能仓库自检，仓库根）**：把可机械核对的部分一次跑完——① 技能清单与数量声明（磁盘技能数 vs marketplace 数组与正文里的「N 个技能」）② SKILL.md 骨架（七节基准）与 README 段位（四段）③ 技能名疑似拼错（提示层，不计入结论）④ 脱敏扫描 ⑤ 旧技能名残留 ⑥ 分发清单同步；只取数不判定，退出码 0/1
- **`create-gitee-release.py`（仓库根）**：按 tag 补齐 gitee 镜像发行版——owner/repo 从 gitee 远端解析，正文取 CHANGELOG 对应段落并用 `release.entry_mismatch` 校验与 tag 提交处一致（不一致即阻塞、不猜测正文），令牌取 `--token` / `GITEE_TOKEN` / `.tasks/gitee-token.txt`；默认只列计划、`--apply` 才创建，已发布的不修改，`--verify` 回读远端正文比对
- **`skills/session-summary/scripts/extract-session.py`**：会话记录抽取（四种模式：用户消息全文 / 尾部 N 条 assistant 文本 / 逐条时间线 / 紧凑全文转录），按项目路径转义规则定位 `~/.claude/projects/`，给会话 id 时可用 `--project` 指定所属项目，默认落盘 `.tasks/session-extract/`——填补技能「要求落盘抽取却没给工具」的缺口
- **`skills/mr-create/scripts/selftest.py`**：`prepare-mr.py` 自测 38 项（失败分支、六种推送状态、平台识别、模板探测、落盘与渲染），用例各自在临时目录建独立仓库；C36 顺带核对脚本状态键与 SKILL.md「推送源分支」表一致，跨盘符用例无第二个盘符时记 SKIP
- **`skills/git-history-rewrite/references/index-filter.sh`**：`filter-branch --index-filter` 批量替换脚本模板（改目标文件 / 命中模式 / sed 规则三处即可用，写明为何用 index-filter 而非 tree-filter）

### 变更

- **`release.py` 支持正文回读与写回**：`--verify` 分页回读全部 Release 并与 CHANGELOG 逐条比对（只读），`--sync-bodies --apply` 把不一致的正文写回（只改正文，不动 tag、标题与发布状态，无 `--apply` 时只列出）；无 token 与列表读取失败改为打印阻塞行
- **`AGENTS.md` 新增「技能骨架与写法基准」小节**：SKILL.md 七节基准、frontmatter 官方字段、README 四段基准、references 拆分判据与写法文风——`check-skills.py` 按此机械核对
- **脱敏扫描的业务词表外置**：`check-skills.py` 的通用模式（绝对路径 / IP / 凭据赋值 / owner 名）内置，业务专属词表放仓库根 `sensitive-terms.txt`（每行一个词、`re:` 前缀按正则；**词表本身不入库**——把敏感词提交进通用技能仓库等于换个地方泄露）
- **`git-history-rewrite` 补两条批量替换教训**：替换脚本按字节替换、不解码（替换片段不含换行时天然绕开行尾差异，纯文本替换别用正则）；多分支全历史批量替换用 `--tree-filter` + 独立幂等脚本
- **`app-packaging` / `git-history-rewrite` / `session-summary` 的 README 段位对齐基准**：补「能力」段、「用法」改「使用」、「文件与依赖」拆为「文件」「依赖」
- **`AGENTS.md` 常用命令与 `README.md` 目录结构同步**：登记三个新工具入口与两个技能脚本，技能表补三个技能的附属文件

### 说明

- 本次为**工具与文档的固化**（新增 3 个脚本、1 个模板、1 组自测，无技能增删、无技能流程语义变更），按分级取**小版本**。
- 技能数量仍 27、技能名与分发路径不变；`config.json`（本地启用清单，不入库）无需改动。
- `.claude-plugin/marketplace.json` 版本号 2.4.1 → 2.4.2

## [2.4.1] - 2026-09-17

`session-summary` 技能补「**目标项目的教训回流**」：被总结的会话操作的是**别的项目仓库**时，把该仓库本次实证过的教训回流进**它自己的** `AGENTS.md`，而不是只留在会话记录或本仓库技能里——教训的落点由「谁该记住它」决定，技能该记的进本仓库、项目该记的进那个项目；同轮同步三处分发文档的技能简介。

### 变更

- **`session-summary` 新增执行步骤「目标项目的教训回流（会话发生在别的项目仓库时）」**：读目标 `AGENTS.md` 全文摸清章节结构与颗粒度（新内容长在既有结构上）→ **落盘抽取**目标会话取证（用户消息全文 + 尾部 assistant 文本消息，不整份读十几 MB 的 transcript）→ 只收「本次实证 + 目标文档未固化」的教训（通用最佳实践、推测性建议、一次性操作失误不收）→ 写法对齐目标文档并脱敏 → **按目标仓库自己的规范提交** → 逐条汇报「教训 → 落点章节 → 新写 / 补充」与未收录原因
- **`session-summary` 要求补第 3 条「教训按归属分流」**：技能本身的缺陷与能力缺口留在本仓库（进优化点清单），项目特有的机制 / 边界 / 坑回流目标仓库，两边都沾时各写各的、不互相代替；归属判据是「换个项目还成立吗」；回流是本技能的固有环节，不另转 `doc-sync`
- **`session-summary` 角色 / 适用 / 验证 / 任务目标 / 注意事项同步**：回流守目标仓库规范（提交语言 / 署名 / 是否推送以它自己的 `AGENTS.md` 为准，不套用本仓库的发版与双远端规则）；执行步骤由 5 步顺延为 6 步
- **分发文档同步**：`README.md` / `PLUGIN_README.md` 技能表的 `session-summary` 行与技能目录 `README.md` 的简介、步骤串补入回流一步

### 说明

- 本次为既有技能的能力增强（新增一步流程与一条要求），按分级取**小版本**。
- 技能数量仍 27、技能名与分发路径不变；`config.json`（本地启用清单，不入库）无需改动。
- `.claude-plugin/marketplace.json` 版本号 2.4.0 → 2.4.1

## [2.4.0] - 2026-09-17

新增**打包与分发**技能：把「跨平台构建 → 打包 → 交付」这条链路沉淀为通用技能（产物形态决策、运行时依赖盘点、平台与架构矩阵、交叉构建边界、CI matrix 构建与 Release 附件分发、版本注入与校验和），并附可直接套用的 CI 与单文件可执行配置模板；同时修复 `release.py` 创建 Release 前未校验正文与 tag 提交处条目一致的问题——正文取自工作区 `CHANGELOG.md`，工作区停在未提交草稿或别的提交时，发出去的正文会带上未发布内容。

### 新增

- **新技能 `app-packaging`（打包与分发）**：角色为分发工程师，顺序固定「**先定产物形态 → 再定构建在哪跑 → 最后定怎么交付**」；8 条要求覆盖产物形态决策表（裸目录 / zip / 单文件可执行 / 安装包及各自代价）、运行时依赖盘点（要求目标机预装则写明最低版本，不要求则内嵌运行时换零依赖）、平台矩阵**含架构**（Windows x64 / macOS arm64 / Linux x64 是三个不同产物）、交叉构建边界（原生模块、字节码 / 快照 / 代码缓存、需平台签名的产物必须对应平台构建）、干净环境实测、版本号单一来源、交付带校验和、分发渠道按持久性与形态选（CI 中转用 Artifacts、给人下载用 Release 附件）；正文含 6 步执行步骤与验证清单
- **`references/node-sea.md`（Node 单文件可执行）**：入口先打成单文件 JS 的前提、两条路径对照（一步式配置文件 与 出 blob + 注入器注入）、平台支持与交叉构建边界、签名时机与顺序（任何二进制改动都会让已有签名失效，**先改后签**）、注入脚本的路径语义、已知坑与验证清单
- **`references/ci-distribution.md`（CI 构建与分发）**：触发方式（tag / 手动）、matrix 编排要点、**Artifacts 与 Release 附件对照**及各自坑位（Artifacts 会打 zip 且剥掉可执行位、有保留期；Release 附件是原始文件、同名重复上传会失败）、校验和、权限与可复现
- **`assets/` 模板**：`workflow-build-release.yml`（矩阵构建 → artifact 中转 → Release 附件，版本从 tag 注入、生成校验和清单）、`sea-config.json`（只含恒成立字段，交叉构建另加可执行文件路径）

### 变更

- **两条分发路径与文档同步**：`.claude-plugin/marketplace.json` 的 `plugins[].skills` 数组与插件 `description` 补入新技能；`README.md` / `PLUGIN_README.md` 技能表新增一行、技能数量声明 26 → 27；`AGENTS.md` 架构第 3 条的数量示例同步；`session-summary` 技能内两处技能数量同步为 27
- **`release.py` 模块说明补「创建前校验条目一致性」**：Release 正文应当等于 **tag 所指提交处**的条目，而不是工作区当前的状态

### 修复

- **`release.py` 补正文与条目一致性校验**：新增 `entry_at_tag` / `first_diff_line` / `entry_mismatch` 三个函数与行尾归一，用 `git show <tag>:CHANGELOG.md` 取 tag 提交处的 CHANGELOG，按版本标题切出**该版本那一段**与工作区同名段落比对（只比该段，回填历史 tag 不受后续版本条目影响；归一行尾以规避工作区 CRLF 与仓库对象 LF 的假差异）；不一致的版本标为「阻塞」并给出首个差异行、**不猜测正文**，且校验只作用于**确实会创建**的版本——已发布与未推 tag 的版本在此前分支已短路，不参与比对，避免把已发布版本误报为阻塞。此前已发布版本的 Release 正文曾出现两条从未进入任何提交的草稿条目行

### 说明

- 本次为**新增技能**（含两个 `references` 与两个 `assets` 模板）加一处脚本缺陷修复，按分级取**中版本**。
- 技能数量 26 → 27，两条分发路径（安装脚本启用清单、`marketplace.json` 的 `skills` 数组）均已同步；`config.json`（本地启用清单，不入库）按默认启用自动补全，无需改动。
- `.claude-plugin/marketplace.json` 版本号 2.3.5 → 2.4.0

## [2.3.5] - 2026-09-17

`AGENTS.md` 发版流程补双远端规则：推送从「只推 `origin`」改为「`origin`（GitHub）+ `gitee` 镜像都要推」，已知坑补 gitee 镜像容易漏推、推送凭据（账号密码）与 API 私人令牌的区别；仅仓库指引文档同步，无技能与代码改动。

### 变更

- **`AGENTS.md` 发版流程补双远端推送规则**：第 5 条 release 流程由「tag 与 main 一并推送（`git push origin main --follow-tags`）」补充为**两个远端都要推**——`git push gitee main --follow-tags`，只推 `origin` 会让 gitee 镜像静默落后（本地 `main` 的 upstream 恰指向 gitee）；gitee 走直连、不需要代理
- **`AGENTS.md` 已知坑补 gitee 镜像说明**：gitee 镜像远端容易漏推（曾出现 gitee 上连一个 tag 都没有、版本页长期为空）；`git credential fill` 取到的 gitee 凭据是**账号密码**（用于 git push），gitee API v5 只认**私人令牌**——gitee 发行版须用令牌另行创建（`POST /api/v5/repos/{owner}/{repo}/releases`，`access_token` 传令牌），不用推送凭据去试

### 说明

- 仅仓库指引文档同步，无技能与代码改动，按分级取**小版本**。
- `.claude-plugin/marketplace.json` 版本号 2.3.4 → 2.3.5

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
