# app-packaging

打包与分发：把应用做成「使用者拿到就能用」的产物并交付——产物形态决策、跨平台构建边界、CI 构建与 Release 附件分发、版本注入与校验和。

## 使用

当用户要求"把脚本打成 exe""做成不装依赖就能跑的单文件""多平台打包""加 CI 自动构建产物""把产物发到 Release 附件""怎么做校验和"时触发。

流程：定形态与平台矩阵 → 打通单平台本地构建 → 多平台编排（能跨则跨、不能跨则对应平台）→ 分发（附件 + 校验和）→ 干净环境实测。

**边界**：构建 / 打包报错的缺陷定位用 `bug-fix`；只管版本号、tag 与 Release 正文的发版流程（不涉及产物）按项目自身发版规范；MR/PR 生成用 `mr-create`。

## 能力

- 产物形态决策：裸目录 / zip / 单文件可执行 / 安装包四选一，判据是**使用者在目标机上要做几步操作**，并给出各形态的代价（体积、可执行位、签名成本）
- 依赖盘点与版本注入：运行时是否内嵌、最低版本写进 `--version`；产物版本与 git tag 单一来源，文件名含版本 / 平台 / 架构
- 平台矩阵与交叉构建边界：Windows x64 / macOS arm64 / Linux x64 是三个不同产物；原生模块、字节码快照、需平台签名的产物必须对应平台构建，拿不准按「不跨」处理
- CI 构建与分发：多平台 matrix（模板 `assets/workflow-build-release.yml`）、**Artifacts 与 Release 附件的区别与坑**（保留期、打 zip、剥可执行位）、`SHA256SUMS`
- 验证口径：在**干净环境**跑 `--version` 与冒烟命令——构建机 / CI 上能跑不构成证据；签名与改动的顺序不可颠倒（先改后签）

## 文件

| 文件 | 说明 |
|------|------|
| `SKILL.md` | 执行指令（形态决策 → 依赖盘点 → 平台矩阵 → 构建编排 → 分发 → 验证） |
| `references/node-sea.md` | Node 单文件可执行：`--build-sea` 与 blob + postject 两条路径、签名顺序、交叉构建限制、已知坑 |
| `references/ci-distribution.md` | GitHub Actions：触发方式、matrix、**Artifacts 与 Release 附件的区别与坑**、校验和、权限 |
| `assets/workflow-build-release.yml` | 多平台构建 + 发 Release 附件的 workflow 模板（占位符待替换，版本号需现核） |
| `assets/sea-config.json` | Node SEA 配置模板 |

## 依赖

- Node SEA 旧路径需 `postject`（用 `npx` 按需拉取）
- 分发走 GitHub Actions 与 `gh` CLI（runner 预装）
- 正文与 references 为流程知识，无强制依赖
