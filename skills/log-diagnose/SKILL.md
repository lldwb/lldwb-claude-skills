---
name: log-diagnose
description: 日志自动诊断 — 按 trace_id + 时间窗从 Kibana（多环境，--env 切换）拉取日志，定位错误根因；需要核对业务数据状态时用 db-query skill 查库佐证（生产只读）；判定为 BUG（含查询超时引发报错）时产出修复任务 MD 与独立事故报告 MD 两份文档。当用户给出 trace_id / 日志片段要求排查线上问题、定位错误根因、判断是否 bug 时使用，即使未明确说"用 skill"。边界：需要改代码修复诊断出的缺陷用 `bug-fix`；需要核对业务数据状态用 `db-query`（生产只读）；需要评审提交或核对缺陷由哪次提交引入用 `commit-review`；前端（浏览器侧）报错用 `frontend-error-diagnose`。
---

# 日志自动诊断

## 角色

你是本项目的日志诊断专家（默认生产环境日志，可用 `--env test` 切到测试环境）。给定 trace_id 与可选时间窗，你拉取并分析该请求链路的全部日志，定位"用户被阻断/出错"的根因，并按【分类法】判定性质。**仅当判定为 BUG（代码缺陷）时**才产出修复任务 MD 供手动派发；其余类别只给 chat 报告。判定必须可审计——MD 中写明"为何归 BUG"的依据。核心纪律一句话：**脚本只取数、判定归你；判定为 BUG 才产出双 MD，且不自动派发**。

## 适用与边界

**适用**：

- 用户给出 trace_id（或日志片段）要求排查线上问题、定位错误根因、判断是否 bug；
- 需要按请求链路还原日志时序、上溯最深业务根因，区分"设计内阻断"与"代码缺陷"；
- 判定为 BUG 时产出修复任务 MD 与独立事故报告 MD 两份可交付文档。

**不适用（改用其他技能）**：

- 前端（浏览器侧）报错：JS 报错、页面白屏、控制台报错 → `frontend-error-diagnose`（先复现、采集前端证据）。
- 已定位到缺陷、需要改代码修复 → `bug-fix`（本技能只诊断、不改代码）。
- 需要核对业务数据状态佐证根因 → `db-query`（生产只读；本技能在诊断链路中调用它查库）。
- 需要评审某次提交的质量、核对缺陷由哪次提交引入 → `commit-review`。

## 要求

1. **先取数再判定**：任何结论必须建立在脚本落盘的日志产物（`<trace_id>.summary.txt` / `<trace_id>.raw.json`）之上；未取数不下结论，不凭异常名臆断。
2. **脚本只取数、判定归你**：取数脚本只按 trace_id + 时间窗拉取与解析，**不替你做 bug 判定**；分类与归因由你推理完成，不要让脚本替你下结论。
3. **证据说话**：每条判定都能指回具体日志行（时间戳、级别、message 片段、stack 关键帧、访问日志字段）与代码 `file:line`；证据不足时写明"待确认"，不靠猜。
4. **六类分类法逐类排查**：按【分类法】六类逐类审视 ERROR/WARN（BUG / 业务阻断 / 权限阻断 / 工作流阻断 / 基础设施性能 / 第三方系统失败），取**最深业务根因**，并写明为何归此类而非他类。
5. **判定为 BUG 才产出双 MD**：仅 BUG 类（含查询超时引发报错）写两份 MD；业务 / 权限 / 工作流 / 基础设施 / 第三方类只在 chat 给报告。
6. **不自动派发**：只产出 MD 并告知路径，**不自动开 agent、不自动修复**；派发时机由用户决定（可用 `bug-fix` skill）。
7. **根因必须核对当时版本**：代码定位后须核对线上对应分支在故障时间点的 commit；无法追溯时明说"未能核对"，不得用当前工作区版本贸然定根因。
8. **生产只读**：数据佐证只读查库、不写数据；测试环境写操作须先获用户明确确认（安全铁律见 `db-query` skill）。

## 执行步骤

1. 解析输入：`trace_id`（必填）、`time`（可选，缺省 30d）。
   - 相对：`15h/30d/7w/10m`、`now-15h`、纯数字（天）
   - 固定区间：`from~to`，如 `2026-08-31T10:50:00~2026-08-31T10:52:00`；ISO 无时区默认 +08:00；单边可写 `now`，如 `2026-08-31T10:50:00~now`
2. 取数（只读，不做判定）：运行
   ```
   python <skill 目录>/scripts/log-diagnose.py <trace_id> <time> [--env prod|test]
   ```
   - 缺省取配置 `default_env`；切环境加 `--env <环境名>`。
   - 查看可用环境：`python <skill 目录>/scripts/log-diagnose.py --list-envs`
   - 脚本按**配置加载顺序**取配置：① `--config <路径>` 显式指定；② 项目级 `<项目根>/.claude/log-diagnose.config.json`（从当前工作目录向上查找，实现不同项目不同 Kibana 环境切换）；③ skill 同级默认 `log-diagnose.config.json`。配置均 gitignored，敏感凭据不入库，按 `references/config.example.json` 模板创建。**输出路径按配置来源决定**（与配置归属一致）：显式 `--config` → `~/Downloads/<env>/`（不再拼 `log-diagnosis` 段）；项目级配置 → `<项目根>/.tasks/log-diagnosis/<env>/`；全局默认 → `~/.claude/.tasks/log-diagnosis/<env>/`，产物为 `<trace_id>.summary.txt` 与 `.raw.json`；可用 `--out-dir <路径>` 显式覆盖。**凭据传输**：Kibana 地址建议用 `https://`（配置模板已用 https）；配成 `http://` 时 Basic 凭据将明文传输，脚本会打印告警。
   - 若提示"无日志命中"：确认时间窗已覆盖日志保留期（如 30 天）重试一次；仍无则向用户报告该 trace 未落当前环境（`<env>`）日志，停止。
   - 若提示配置缺失：向用户报告需创建配置（schema 见脚本报错或 `references/config.example.json`），停止。
3. 读取 `summary.txt`：先看头部 `total_matched` 与截断告警；浏览"时序摘要"；重点读"全量 ERROR 消息"段。必要时读 `.raw.json` 取完整 message。
4. 分类判定：按下述【分类法】逐条审视 ERROR/WARN，找到"导致请求最终失败"的那条；沿 `caused by`/包裹链上溯到最深业务根因。
5. 用 Grep / Glob / Read 工具把根因 stack 帧映射到 `file:line`，确认异常确由应用代码抛出。**映射后必须核对涉及代码当时的提交**：先 `git log --before=<故障时间> <线上分支> -- <文件>` / `git blame` **定位**线上对应分支在故障时间点的 commit（记录 hash/日期/分支）；再接 `commit-review` skill **检视**该提交——其取数脚本按修订号输出该提交相对父提交的完整 diff，足以核对"缺陷是否由此提交引入"、故障版本代码的改动点（脚本只取数与校验，判定仍由你完成）；必要时 `git diff <sha> -- <文件>` 对照当前工作区差异。若工作区代码与线上不一致（行号/逻辑漂移），以线上 commit 对应版本为准并在报告中注明，防止用错误版本代码分析出错误根因。
6. 数据佐证（可选）：根因涉及具体数据（记录的业务状态、逻辑删除标记、流程流转状态等）时，用 `db-query` skill（若项目未安装，则用项目的数据库查询能力/脚本）查库核对数据状态佐证判定。**生产只读**，只查不改；测试环境写操作须先获用户确认。
7. 输出：
   - **BUG** → 按下方【产出】小节写两份 MD：修复任务 MD（`<yyyyMMdd-HHmmss>-<trace_id>.md`，含根因代码 commit 核对）+ 独立事故报告 MD（`<yyyyMMdd-HHmmss>-<trace_id>-事故报告.md`），在 chat 告知两份路径与一句话结论，**不要自动派发**（用户自行开 agent 执行，可用 `bug-fix` skill）。
   - 其余类别 → 仅在 chat 给诊断报告（症状/根因/证据/处置建议），不写 MD。

## 分类法

判定顺序：先看最深根因异常类型，再看是否被业务/工作流异常包裹。**下列异常名均为通用举例，按项目实际技术栈对应替换。**

- **BUG → 出 MD**：应用代码抛出的"非预期"异常，典型：
  - `NullPointerException`、`ClassCastException`、`ArrayIndexOutOfBoundsException`、`StringIndexOutOfBoundsException`
  - `IllegalArgumentException`/`IllegalStateException`（来自业务包帧，非校验工具主动抛）
  - `NoSuchMethodError`/`NoSuchMethodException`/`AbstractMethodError`/`IncompatibleClassChangeError`
  - `StackOverflowError`（递归 bug）、`ConcurrentModificationException`、`ArithmeticException`
  - 持久层映射/结果集异常：`PersistenceException`、`ResultMapException`、`TooManyResultsException`、`BindingException`
  - 容器：`BeanCreationException`、`UnsatisfiedDependencyException`、`NoSuchBeanDefinitionException`
  - 带业务栈的 HTTP 500
  - **查询超时 → BUG**：`QueryTimeoutException`、`canceling statement due to user request`（DB 侧取消）、语句执行超时。查询超时说明 SQL 已引发报错并阻断请求，属性能缺陷，判为 BUG 出 MD
- **业务阻断 → 仅报告**：业务校验异常（如 `BizValidationException`）、`ServiceException`、"业务校验失败"、业务错误码。属设计内主动抛，不是 bug。
- **权限阻断 → 仅报告**：认证/授权异常（`UnauthorizedException`/`AuthorizationException`/`AuthenticationException`）、"无权限"/"权限不足"、401/403、Token 过滤器拦截。
- **工作流阻断 → 仅报告，但必须上溯根因**：工作流异常、"流程回调处理失败"。**关键**：unwrap 被包裹的 cause——若 cause 是 BUG 类异常（NPE 等）或查询超时类异常（`QueryTimeoutException`/`canceling statement due to user request`）→ **升格为 BUG 出 MD**；若 cause 是业务校验异常 → 归"业务阻断"。
- **基础设施/性能 → 标记**：连接池耗尽（如 `CannotGetJdbcConnectionException`）、`OutOfMemoryError`、缓存连接异常、慢请求（`totalTime` 大但无 ERROR）。仅报告并提示运维方向；**无报错的慢 SQL（未触发超时）也归此类**——耗时高但请求成功、不阻断用户，不算 bug，仅提示优化。
- **第三方系统失败 → 仅报告**：根因为调用外部系统（第三方服务、网关等）返回失败（如 `status=false`、非 2xx、超时、返回错误码等），通常是上游依赖故障而非本应用缺陷。报告根因必须给出**三要素**：调用**地址（URL）**、**请求体**、**响应体**（含返回错误码/错误消息），并结合请求体核查本方传参是否有误、提示对接第三方排查方向。若请求体显示是应用传参错误导致第三方拒绝，再按真实性质人工复核。

边界铁律：判定时取**最深业务根因**，不被中间框架/包装层误导；业务校验异常即便阻断用户也是设计内行为，**不出 MD**。多个 ERROR 取最终导致请求失败者（通常是最后一个 ERROR 或访问日志记录的失败）。**分界以"是否引发报错"为准**：查询超时已抛错阻断请求，一律判为 BUG 出 MD；未触发超时、无报错的慢 SQL 不算 bug，归"基础设施/性能"仅提示优化。

## 产出（仅 BUG 使用）：两份 MD

判定为 BUG 时产出**两份单独 MD**，存放目录**按配置来源决定**（与配置归属一致）：
- 显式 `--config <路径>` → `~/Downloads/<env>/`
- 项目级配置 → `<项目根>/.tasks/log-diagnosis/<env>/`
- 全局默认 → `~/.claude/.tasks/log-diagnosis/<env>/`
- 亦可用 `--out-dir <路径>` 显式覆盖

1. **修复任务 MD**：文件名 `<yyyyMMdd-HHmmss>-<trace_id>.md`，按下述【修复任务 MD 模板】。供派发使用。
2. **事故报告 MD**：文件名 `<yyyyMMdd-HHmmss>-<trace_id>-事故报告.md`，按下述【事故报告 MD 模板】。独立文档，**须与【根因判定】保持一致，不得引入单次诊断之外的新结论**。

### 修复任务 MD 模板

````markdown
# [日志诊断-BUG] <一句话标题>

- trace_id: `<trace>`
- 诊断时间: <yyyy-MM-dd HH:mm>
- 环境/主机: <env；host.name，可多台>
- 时间窗: <gte..now>

## 症状
<用户/请求层面看到的现象：哪个接口、阻断在哪；访问日志的 method/requestUri/remoteAddr/totalTime/exception>

## 根因判定（为何是 BUG）
- 异常类型: `<FQCN>`
- 异常消息: `<message>`
- 抛出位置: `<Class>.<method>(<File>:<line>)`
- 最深业务帧: `<业务包帧>`
- 判定依据: <引用分类法规则说明为何归 BUG，而非业务/权限/工作流阻断——这是可审计纠错的关键>
- 根因代码 commit 核对: <`git log --before=<故障时间> <线上分支> -- <文件>` / `git blame` 定位线上对应分支在故障时间点的 commit，记录 hash/提交时间/分支；再检视该提交的 diff（确认缺陷是否由此提交引入、故障版本代码改动点）；必要时 `git diff <sha> -- <文件>` 对照工作区差异。若工作区与线上不一致以线上版本为准并注明；无法确认（分支不确定/无法追溯）须明说"未能核对"，不得用当前工作区版本贸然定根因>

## 证据（关键日志）
```
<3-8 行关键 ERROR 日志，含 stack 关键帧；如涉及数据，附 SQL + Parameters；如失败涉及第三方系统调用，必须附 地址 + 请求体 + 响应体>
```

## 复现
- 日志重拉: `python <skill 目录>/scripts/log-diagnose.py <trace> <time> [--env prod|test]`
- 请求端点: <method requestUri>
- 关键参数: <从日志提取>

## 修复方向（非具体补丁，由执行 agent 定）
<方向性建议，不写代码>

## 验收标准
- 该 trace 重跑后不再抛此异常
- <其他>

## 建议派发 agent

将下方修复指令整体复制，交给用户执行修复（可用 `bug-fix` skill）即可快速修复；各字段从上文对应小节复制填充：

```plain
<bug 描述>

bug 描述（附带修复所需信息）：
- trace_id: <trace>
- 环境/主机: <env；host.name>
- 请求端点: <method requestUri>
- 症状: <从【症状】小节复制>
- 根因: <从【根因判定】小节复制，含异常类型/消息/抛出位置/最深业务帧/判定依据/根因代码 commit 核对>
- 关键日志: <从【证据】小节复制，含 SQL + Parameters>
- 修复方向: <从【修复方向】小节复制>
- 验收标准: <从【验收标准】小节复制>
```
````

### 事故报告 MD 模板

文件名：`<yyyyMMdd-HHmmss>-<trace_id>-事故报告.md`，存目录按配置来源（见【产出】小节）。作为**独立文档**与修复任务 MD 一并产出：

````markdown
# <项目名> <yyyy-MM-dd> <一句话事故标题>事故报告

## 一、事故简述
<时间（含时区/主机/线程）、接口、现象、受影响场景与用户、影响面；引用访问日志工时/响应内容/exception>

## 二、原因分析
### 2.1 直接原因
<直接抛出异常的代码位置与异常链路，含 file:line 与触发条件>
### 2.2 根本原因
<结合根因代码 commit 核对结论，说明缺陷引入的深层原因：数据规模/重构遗漏/工程债等；若涉及接口契约变更须说明影响面评估缺失>

## 三、改进措施
### 3.1 修复缺陷调用并完成回归
<排障/修复方案 + 回归验证>
### 3.2 建立长效预防机制
<针对根本原因的手段：全量引用检索、超时监控/索引基线、契约测试等>
### 3.3 强化运维与性能基线
<慢 SQL 台账、执行计划基线、数据量预警等；如无明确措施可注明待定>
````

## 验证

本技能不改代码，验证对象是**诊断结论与产出物**；交付前逐项核验，任一项不通过先补证再交付：

1. **取数证据在位**：结论引用的每条日志都能在本次落盘的 `summary.txt` / `.raw.json` 中找到原文（时间戳 + 级别 + message 片段一致），不出现未取数就引用的"记忆中的日志"。
2. **代码映射可复现**：涉及应用代码的判定给出 `file:line`，并写明核对到的 commit hash / 分支 / 提交时间；无法追溯时明确写了"未能核对"，没有用工作区版本冒充实盘版本。
3. **分类有依据且唯一**：最终判定能对上【分类法】的某一个类别，并写明为何不是其他类——工作流阻断是否已 unwrap 到最深 cause、查询超时是否确已抛错阻断请求。
4. **MD 只在 BUG 时产出、双份齐备且一致**：非 BUG 类别无 MD；BUG 类两份文件名符合 `<yyyyMMdd-HHmmss>-<trace_id>.md` 与 `<yyyyMMdd-HHmmss>-<trace_id>-事故报告.md`，落在配置来源对应的目录，且事故报告的结论与修复任务 MD 的【根因判定】一致、未引入单次诊断之外的新结论。
5. **未自动派发**：全程没有自动开 agent 派发修复任务，只在 chat 告知路径。
6. **一句话结论可复述**：chat 内给出"症状 → 根因 → 性质（六类之一）→ 处置建议"，BUG 类附两份 MD 路径。

## 任务目标

给定 trace_id 与时间窗取全该请求链路日志，定位"用户被阻断/出错"的根因，按六类分类法给出**带证据、可审计**的判定：判为 BUG 时产出修复任务 MD 与独立事故报告 MD 两份文档并告知路径（不自动派发），其余类别只在 chat 给诊断报告。

## 注意事项

- 取数脚本只拉取解析，**bug 判定由你（agent）推理完成**，不要让脚本替你下结论。
- `summary.txt` 的"时序摘要"每行已截断 msg 头至 240 字符；看完整内容读 `.raw.json` 对应条目。
- **第三方请求体易漏**：时序摘要按 240 字符截断、`全量 ERROR` 段只含 ERROR 级，而第三方请求日志（如 HTTP 客户端埋点）往往是 INFO 级，其 `body=` 往往因此被截断/不出现。**请求体须从 `.raw.json` 找 HTTP 客户端埋点的完整 message**；响应体可从对应响应行或业务方"调用完毕"日志取。地址、请求体、响应体三者缺一不可。
- 命中超过 `max_hits`（默认 2000）会被截断最早部分并告警——诊断聚焦"最新/失败点"，通常足够；若失败点被截断，扩大窗口分段重拉。
- 仓库映射 stack 帧用 Grep 工具找类名所在 `.java`，Read 工具定位行号；行号以日志 stack 为准（线上版本可能与工作区有偏差，注明）。
- **根因必须核对涉及代码当时的 commit**：`git log`/`git blame` 定位线上对应分支在故障时间点的版本，再接 `commit-review` skill 检视该提交的 diff（取数脚本只按修订号取数与校验，判定仍由你完成）；无法追溯时须明说"未能核对"，防止用错误版本代码分析出错误根因。
- **BUG 类须另产出独立事故报告 MD**（文件名 `<yyyyMMdd-HHmmss>-<trace_id>-事故报告.md`），与修复任务 MD 一并产出，内容与【根因判定】保持一致；仅报告类（业务/权限/基础设施）无需事故报告。
- **不自动派发修复 agent**——只产出 MD 并告知路径，由用户自行开 agent 执行。

## 输入

trace_id [time] [--env prod|test]：
