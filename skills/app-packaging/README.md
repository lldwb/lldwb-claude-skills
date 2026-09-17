# app-packaging

打包与分发：把应用做成「使用者拿到就能用」的产物并交付——产物形态决策、跨平台构建边界、CI 构建与 Release 附件分发、版本注入与校验和。

## 用法

当用户要求"把脚本打成 exe""做成不装依赖就能跑的单文件""多平台打包""加 CI 自动构建产物""把产物发到 Release 附件""怎么做校验和"时触发。

流程：定形态与平台矩阵 → 打通单平台本地构建 → 多平台编排（能跨则跨、不能跨则对应平台）→ 分发（附件 + 校验和）→ 干净环境实测。

## 文件与依赖

| 文件 | 说明 |
|------|------|
| `SKILL.md` | 执行指令（形态决策 → 依赖盘点 → 平台矩阵 → 构建编排 → 分发 → 验证） |
| `references/node-sea.md` | Node 单文件可执行：`--build-sea` 与 blob + postject 两条路径、签名顺序、交叉构建限制、已知坑 |
| `references/ci-distribution.md` | GitHub Actions：触发方式、matrix、**Artifacts 与 Release 附件的区别与坑**、校验和、权限 |
| `assets/workflow-build-release.yml` | 多平台构建 + 发 Release 附件的 workflow 模板（占位符待替换，版本号需现核） |
| `assets/sea-config.json` | Node SEA 配置模板 |

依赖：Node SEA 旧路径需 `postject`（用 `npx` 按需拉取）；分发走 GitHub Actions 与 `gh` CLI（runner 预装）。正文与 references 为流程知识，无强制依赖。
