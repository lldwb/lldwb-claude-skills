# frontend-error-diagnose

前端报错诊断的标准工作流：先用浏览器 MCP 复现报错，采集 console 报错、失败请求与 JS 调用栈等证据，定位根因后给出可执行的修复方案；不凭报错文案猜结论，**默认只诊断不改代码**。

## 使用

用户给出前端报错（APM/监控上报的 JS 报错、控制台报错、白屏、接口 4xx/5xx、CORS、资源加载失败等）并要求"分析是什么问题导致的报错""先复现再分析""给出解决方案"时自动触发；也可显式要求"用 frontend-error-diagnose skill 定位这个前端报错"。

**边界**：需要直接改代码完成修复用 `bug-fix`；报错指向后端、需拉日志定位根因用 `log-diagnose`；需核对业务数据状态用 `db-query`（生产只读）。

## 能力

- 复现取证：浏览器 MCP 打开页面 → 触发报错 → 采集 console / 网络 / 调用栈 / 截图 / 环境版本（对照表见 `references/browser-evidence-checklist.md`）
- 结论结构：现象 → 证据 → 根因 → 修复方案 → 影响范围与回归点，每条判断可指回证据（模板见 `references/conclusion-template.md`）
- 无法复现时按三档降级（换环境 → 索要报错原文 / HAR → 只给可能性排序），不静默跳过
- 浏览器侧改写请求头取证：接口直连正常却在浏览器里 403/401 时，按「对照实验 → 扩展 DNR 规则 → 扩展源码」定位改写源（见 `references/extension-header-forensics.md`）
- 接口/后端异常交叉验证：接 `log-diagnose`（日志）、`db-query`（数据佐证，生产只读）；确需修复转 `bug-fix`
- 默认只诊断不改代码：诊断环节不产生任何代码改动，产出为可审计的结论

## 文件

- `SKILL.md` — 技能指令（唯一入口）
- `references/browser-evidence-checklist.md` — 浏览器取证清单（工具能力对照、必采证据、按报错类型取证要点、APM 上报定位、降级档位）
- `references/extension-header-forensics.md` — 请求头被改写类报错取证（适用判据、curl 对照实验、扩展 DNR 规则与 storage 的磁盘取证、处置与验证、环境能力限制）
- `references/conclusion-template.md` — 结论输出模板（逐段填写要求、未复现时的写法、常见不合格写法）

## 依赖

- 浏览器 MCP（Chrome DevTools MCP / Playwright MCP 等；缺失时按降级档位执行）
