# frontend-error-diagnose

前端报错诊断的标准工作流：先用浏览器 MCP 复现报错，采集 console 报错、失败请求与 JS 调用栈等证据，定位根因后给出可执行的修复方案；**默认只诊断不改代码**。

## 使用

用户给出前端报错（APM/监控上报的 JS 报错、控制台报错、白屏、接口 4xx/5xx、CORS、资源加载失败等）并要求"分析是什么问题导致的报错""先复现再分析""给出解决方案"时自动触发；也可显式要求"用 frontend-error-diagnose skill 定位这个前端报错"。

## 能力

- 复现取证：浏览器 MCP 打开页面 → 触发报错 → 采集 console / 网络 / 调用栈 / 截图 / 环境版本（对照表见 `references/browser-evidence-checklist.md`）
- 结论结构：现象 → 证据 → 根因 → 修复方案 → 影响范围与回归点，每条判断可指回证据
- 无法复现时按档降级（换环境 → 索要报错原文 → 只给可能性排序），不静默跳过
- 接口/后端异常交叉验证：接 `log-diagnose`（日志）、`db-query`（数据佐证，生产只读）；确需修复转 `fix-bug`

## 文件

- `SKILL.md` — 技能指令（唯一入口）
- `references/browser-evidence-checklist.md` — 浏览器取证清单（工具能力对照、必采证据、按报错类型取证要点、APM 上报定位、降级档位）

## 依赖

- 浏览器 MCP（Chrome DevTools MCP / Playwright MCP 等；缺失时按降级档位执行）
