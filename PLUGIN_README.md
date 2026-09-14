# Plugin 使用说明（lldwb-claude-skills）

本仓库可作为 Claude Code Plugin marketplace 使用，通过 `/plugin` 命令安装与更新技能。

## 安装 Plugin

在 Claude Code 中执行（`<仓库地址>` 为本仓库本地路径或 git 远程地址）：

```
/plugin marketplace add <仓库地址>
/plugin install dev-skills@lldwb-claude-skills
```

安装后可查看/管理插件：

```
/plugin
/plugin marketplace list
```

## 更新

仓库内容更新后，拉取更新并重新安装：

```
/plugin marketplace update
```

## 包含的技能

`dev-skills` 插件包含 24 个技能：

| Skill | 用途 |
|-------|------|
| bug-fix | Bug 修复标准工作流（纯注释问题转 comment-supplement） |
| feature-dev | 需求开发全流程（需求分析 → 方案 → 规划文档三件套 → 实现 → 实测 → 提交；支持六阶段交互模式；纯文档产出转 doc-sync） |
| code-optimize | 代码优化（小范围）标准工作流（结构性/分层重构转 refactor） |
| refactor | 重构（结构改造、行为不变）：契约先行 + 测试基线 + 改造与审查分离 + 循环验证（小范围优化转 code-optimize） |
| commit-review | 提交评审（七维核查，只检查不改代码） |
| log-diagnose | 日志自动诊断（Kibana，BUG 出双 MD） |
| db-query | 数据库查询（生产只读） |
| module-batch | 多模块并行改造（worktree + 子代理 + 独立审查） |
| check-rule-extract | 业务操作前置校验规则提取（输出 Excel 工作簿） |
| frontend-error-diagnose | 前端报错诊断（浏览器 MCP 复现，只诊断不改代码） |
| unit-test | 单元测试生成 / 失败修复 |
| doc-sync | 文档与代码同步（更新 / 修正 + 子代理复核；代码改造转 feature-dev） |
| commit-create | 提交 git 改动（拆分 / 显式 add / 中文信息 + 提交后结构复核；提交环节 SSOT；可选 emoji / type·scope / `--amend`） |
| mr-create | 合并请求（MR/PR）生成（分支校验 / 四段式描述 / gh·glab 创建） |
| comment-supplement | 注释补齐与修正（仅注释层面；与代码改动并存时用 bug-fix） |
| project-explain | 结合项目讲解概念（引用真实代码位置） |
| repo-init | 仓库指引初始化（AGENTS.md 正文 + CLAUDE.md 指向） |
| i18n-transform | 国际化改造（三条改造线，改造 / 审查 / 验证三角分离） |
| spec-route | 规范路由（`AGENTS.md` 场景 → 章节定位，不复制约定） |
| opencode-batch | 多模块并行改造编排（opencode CLI 版：worktree + 子代理 + 前置检查 + 中断处置） |
| nas-disk-diagnostic | NAS 硬盘诊断与可视化报告（RAID / SMART，扩展卡硬盘须 `-d sat`） |
| git-clean-branches | 分支清理（已合并 / 过期；默认 dry-run + 保护清单） |
| git-rollback | 分支回滚（reset / revert；默认 dry-run + 备份分支） |
| git-worktree | worktree 管理（统一目录 + 内容迁移 + 环境文件复制） |

技能清单定义在 `.claude-plugin/marketplace.json`。

## 说明

- 插件版本号（`.claude-plugin/marketplace.json` 的 `version`）与仓库 `CHANGELOG.md` 顶部条目、注解 tag `vX.Y.Z` 三处对齐——大版本 = 整体重构、中版本 = 技能大改、小版本 = 小修小改，可据此判断升级影响面（细则见 `AGENTS.md`「架构」第 4 条）。
- 敏感配置（Kibana/数据库凭据）不随插件安装，需按各技能 `references/config.example.json` 模板在 `~/.claude/skills/<技能>/` 下本地创建。
- 也可不用插件，直接运行 `install.sh` / `install.bat` 复制技能到 `~/.claude/skills/`。
