# 请求头被改写类报错的取证（浏览器扩展 / 代理）

本文件是 `frontend-error-diagnose` 的取证参考：当出现「同一接口**直连正常**、浏览器里却稳定失败」时，如何把根因定位到**浏览器侧改写请求头**的第三方（扩展 DNR 规则、代理、本地中间层）。

> 适用前提：已排除页面代码与服务端逻辑（见第三节对照实验）。本文件只解决「谁改了请求头」。

## 一、何时走这条路径

满足以下任一条，就把取证范围从「页面代码 / 服务端」扩展到「浏览器环境」：

- 同一接口用 curl 直接请求**正常**（或返回与浏览器里**不同**的状态码），浏览器里稳定失败；
- 失败状态码为 **403 / 401 / 被 CORS 拦截**，而服务端日志显示请求**根本没到**、或到了却被判定为不可信来源；
- 请求头出现**自相矛盾**的组合——典型是 `sec-fetch-site: same-origin`（浏览器原生头，页面与扩展都改不了）却带着**与目标不同源**的 `Origin`；或 `Host` 与 `Origin` 的 host 不一致；
- 失败请求**成片包含静态资源**（js / css / 图片 / manifest）——页面代码不会给自己的资源请求附加 `Origin`，成片出现说明存在**统一改写**；
- 同一页面内 **WebSocket 握手正常、普通请求异常**——多数请求头改写机制不作用于 WS 握手，这个反差本身就是判据。

## 二、先做对照实验（最低成本的定性）

不改任何配置，直接用 curl 复刻两种请求头，对比服务端判定：

```bash
# A. 复刻浏览器里失败的那个请求（Origin / Host 等原样抄 HAR 或 Network 面板）
curl -s -o /dev/null -w "%{http_code}\n" -X POST \
  -H "Origin: <可疑 Origin>" -H "sec-fetch-site: same-origin" \
  -H "Content-Type: application/json" -d '{}' <接口 URL>

# B. 对照组：Origin 与 Host 同源（或干脆不带 Origin）
curl -s -o /dev/null -w "%{http_code}\n" -X POST \
  -H "Origin: <接口 URL 自身的 origin>" \
  -H "Content-Type: application/json" -d '{}' <接口 URL>
```

**A 失败、B 通过** → 根因锁定在被改写的那一个头上，与页面代码、服务端逻辑都无关，接下来只需找「谁改的」。

注意用状态码区分成因：**403** 多来自服务端的来源信任判定（信任围栏 / 风控 / 防盗链），**401** 是认证失败——两者含义不同，不要混为一谈；同一个接口在「头被改」与「未认证」下可能分别返回这两种码。

## 三、找「谁改的」：扩展 DNR 规则

Chromium 系浏览器用 `declarativeNetRequest`（DNR）改写请求 / 响应头。**动态规则会持久化到磁盘**，因此不必依赖扩展运行即可离线取证：

| 取证目标 | 路径（以 Edge 为例；Chrome 把 `Edge` 换成 `Chrome`） |
|---|---|
| DNR 规则持久化 | `<用户数据目录>/<Profile>/DNR Extension Rules/<扩展 ID>/rules.json` |
| 扩展配置（sync 区） | `<用户数据目录>/<Profile>/Sync Extension Settings/<扩展 ID>/`（LevelDB） |
| 扩展配置（local 区） | `<用户数据目录>/<Profile>/Local Extension Settings/<扩展 ID>/`（LevelDB） |
| 扩展启用状态 | `<用户数据目录>/<Profile>/Secure Preferences` → `extensions.settings.<扩展 ID>`（看 `disable_reasons`） |
| 扩展清单与源码 | `<用户数据目录>/<Profile>/Extensions/<扩展 ID>/<版本>/` |

- 用户数据目录 Windows 下典型为 `%LOCALAPPDATA%\Microsoft\Edge\User Data` 或 `%LOCALAPPDATA%\Google\Chrome\User Data`；macOS / Linux 按其惯例路径。
- **别漏 Profile 层级**：扩展实际装在 `<Profile>/Extensions/` 下（`Default`、`Profile 1` …），少一层会得到「无 Extensions 目录」的假阴性。
- `rules.json` 重点看 `action.requestHeaders` / `responseHeaders` 里的 `header` 与 `operation`，以及 `condition`（`requestDomains` / `urlFilter` / `initiatorDomains`）——**`condition` 决定影响面**：匹配一个网段或宽泛域名的规则，会连带误伤同主机上的**其他**本地服务。
- LevelDB 是二进制，**不必解析格式**，直接按关键字（域名、端口、配置键名）搜字节即可定位配置值：

```bash
grep -a -o -E ".{80}<关键字>.{80}" <LevelDB 文件>
```

## 四、辅助判据：扩展源码

定位到可疑扩展后，在其 `Extensions/<扩展 ID>/<版本>/` 下搜关键字，确认它是否真的改写请求头：

```bash
grep -rn "declarativeNetRequest\|modifyHeaders\|requestHeaders\|\"Origin\"" <扩展目录>
```

- 只出现 `Access-Control-Allow-Origin`（响应头）→ 属于 CORS 类扩展的常规做法，**不是**本类根因；
- 出现 `requestHeaders` + `"Origin"` + `operation: "set"` → 命中，再核对写入的值与 `condition` 的影响面。

同时留意扩展配置里的「目标服务地址」类字段（本地服务 URL / 端口），**改写用的值往往就取自这里**——它可能与失败目标毫无关系，只是被无差别地安到了所有匹配请求上。

## 五、处置与验证

- **改配置**：进入该扩展设置，关闭对应开关（请求头改写类能力常以「修复 CORS」「URL 重写」「自动修复」等名义**默认开启**）；
- **禁用 / 卸载**：不再需要时直接禁用或卸载；
- **注意残留**：DNR 动态规则的磁盘文件**不随禁用而删除**，浏览器重启会重新加载——只「禁用」可能不够，需确认规则已被覆盖，或直接卸载；
- **验证**：重启浏览器后重放第二节的对照实验，并回到页面 Network 面板确认失败请求的头已恢复正常。

## 六、环境能力限制（按需绕行）

- 浏览器 MCP **不允许打开 `chrome-extension://` 页面**，也读不到扩展的 DNR 规则 → 走本文件的**磁盘取证**路径，不要在这上面反复试；
- 浏览器 MCP 依赖调试端口，**浏览器重启后连接即失效**（需重新以带调试端口的参数启动才能接回）；取证中途断连时，改用磁盘证据继续，不要中断结论；
- 无浏览器 MCP 时，请求头证据可向用户索取 **HAR 导出**：`entries[].request.headers` 已包含 `Host` / `Origin` / `sec-fetch-*` / `Cookie`，足以完成第二节的对照（HAR 里的响应头还能顺带确认是否有人加了 CORS 响应头）。
