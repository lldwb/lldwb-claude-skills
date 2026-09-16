# 浏览器取证清单（浏览器 MCP）

本文件是 `frontend-error-diagnose` 的取证参考：用浏览器 MCP 复现前端报错时「采什么、怎么采」。
工具名以项目实际安装的浏览器 MCP 为准，下表给出常见两类实现的等价能力对照；没有对应工具时用同类工具或原生命令替代。

## 一、工具能力对照

| 取证目标 | Chrome DevTools MCP | Playwright MCP |
|---|---|---|
| 打开 / 切换页面 | `new_page` / `list_pages` / `select_page` | `browser_navigate` / `browser_tabs` |
| 跳转 / 后退 / 刷新 | `navigate_page`（url/back/forward/reload） | `browser_navigate` / `browser_navigate_back` |
| 页面可交互元素快照 | `take_snapshot` | `browser_snapshot` |
| 截图 | `take_screenshot`（可 `fullPage`） | `browser_take_screenshot` |
| 点击 / 填表 / 按键 | `click` / `fill` / `fill_form` / `press_key` | `browser_click` / `browser_fill_form` / `browser_press_key` |
| 控制台（含 stack） | `list_console_messages` / `get_console_message` | `browser_console_messages` |
| 网络请求 | `list_network_requests` / `get_network_request` | `browser_network_requests` |
| 执行 JS 读运行时状态 | `evaluate_script` | `browser_evaluate` |
| 等待元素 / 条件 | `wait_for` | `browser_wait_for` |
| 视口 / 弱网 / UA 模拟 | `emulate` / `resize_page` | `browser_resize` 等 |

> 证据要**落盘**（截图、控制台与网络导出），并把文件路径写进结论便于复核；不要只在会话里口述。

## 二、必采证据清单

1. **报错原文**：console 报错类型、文案、完整 stack（含 sourcemap 还原后的源码位置）；同一错误的重复记录一并采全（判断是否连锁触发）。
2. **触发入口**：页面 URL（含参数）、操作路径（按顺序点了什么）、触发时间点。
3. **网络**：失败请求的 method / URL / 状态码 / 响应体 / 请求参数；静态资源（js、css、图片）的 404 / 403 / 加载失败。
4. **运行时状态**：关键变量取值、全局状态或 store、登录态与权限（必要时用 `evaluate_script` 读）。
5. **环境**：环境标识、前端版本或构建号、浏览器与版本、账号角色。
6. **可视化证据**：报错瞬间的页面截图（白屏、错位、异常弹窗时必采）。

## 三、按报错类型的取证要点

| 报错类型 | 重点取证 | 常见根因方向 |
|---|---|---|
| JS 运行时异常（`TypeError` / `Cannot read properties of undefined` 等） | 完整 stack → 源码位置；触发时的入参与数据 | 空值未判、接口返回结构与约定不符、异步时序 |
| 资源加载失败 | 失败资源 URL、状态码、实际部署路径 | 静态资源前缀/路径错误、版本不一致、强缓存未失效 |
| 接口 4xx / 5xx | 请求参数、响应体、后端返回约定 | 参数校验不通过、鉴权过期、后端异常（转 `log-diagnose`） |
| **接口 403/401 但直连同一接口正常** | **请求头完整性：`Host` / `Origin` / `sec-fetch-*` 是否自相矛盾；失败是否成片包含静态资源；WS 握手是否正常** | **浏览器侧统一改写请求头——扩展 DNR 规则 / 代理 / 本地中间层（见 `extension-header-forensics.md`）** |
| CORS / 跨域 | `Origin` 请求头、`Access-Control-Allow-*` 响应头、是否有预检 | 网关或服务端跨域配置、代理配置、**请求 `Origin` 被第三方改写** |
| 白屏 | console 首个报错、入口 js 是否加载、路由是否命中 | 入口脚本报错中断渲染、资源版本不一致 |
| 渲染 / 样式异常 | DOM 快照、计算样式、容器尺寸 | 数据为空未兜底、样式冲突、组件库版本 |

> 「直连正常却在浏览器里失败」这类报错，**先做一次请求头对照实验**（curl 复刻失败请求的头 vs 去掉可疑头）再往下查，别急着翻页面代码——判据与完整取证路径见 `extension-header-forensics.md`。

## 四、APM / 监控上报报错定位要点

- 上报里的 **stack 是压缩后的**，需用**同版本**的 sourcemap 还原到源码（版本不一致会串行号）。
- 上报常带**聚合计数与首次出现时间**：先看影响面与是否随某次发布出现，快速区分「新引入缺陷」与「存量偶发」。
- 上报只有一句文案时，回到「二、必采证据清单」用浏览器 MCP 复现补齐证据，不要只凭文案下结论。

## 五、无法复现时的降级

1. 换环境 / 账号 / 数据复现（测试环境通常日志更全、数据可操作）。
2. 无浏览器 MCP 时：向用户索要 console 报错原文与 stack、失败请求的完整响应，或**浏览器 HAR 导出**——`entries[].request.headers` 里含 `Host` / `Origin` / `sec-fetch-*` / `Cookie`，是请求头类问题最直接的证据；或用项目既有手段取证（本地起服务、直接调接口复现——接口类问题可用 curl **复刻失败请求的请求头**做对照，见 `extension-header-forensics.md`）。
3. 仍无法复现：明确说明「未复现」及原因，只按已有证据给出**可能性排序**与下一步取证建议，不给确定性结论。
