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

`dev-skills` 插件包含 13 个技能：

| Skill | 用途 |
|-------|------|
| fix-bug | Bug 修复标准工作流 |
| code-optimize | 代码优化标准工作流 |
| commit-review | 提交评审（只检查不改代码） |
| log-diagnose | 日志自动诊断（Kibana，BUG 出双 MD） |
| db-query | 数据库查询（生产只读） |
| module-batch | 多模块并行改造（worktree + 子代理） |
| controller-check | Controller 校验规则提取 |
| frontend-error-diagnose | 前端报错诊断（浏览器 MCP 复现，只诊断不改代码） |
| unit-test | 单元测试生成 / 失败修复 |
| doc-sync | 文档与代码同步（更新 / 修正 + 子代理复核） |
| commit-changes | 提交 git 改动（拆分 / 显式 add / 中文信息） |
| comment-supplement | 注释补齐与修正（仅注释层面） |
| explain-project | 结合项目讲解概念 |

技能清单定义在 `.claude-plugin/marketplace.json`。

## 说明

- 敏感配置（Kibana/数据库凭据）不随插件安装，需按各技能 `references/config.example.json` 模板在 `~/.claude/skills/<技能>/` 下本地创建。
- 也可不用插件，直接运行 `install.sh` / `install.bat` 复制技能到 `~/.claude/skills/`。
