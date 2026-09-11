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

`dev-skills` 插件包含 7 个技能：

| Skill | 用途 |
|-------|------|
| fix-bug | Bug 修复标准工作流 |
| code-optimize | 代码优化标准工作流 |
| commit-review | 提交评审（只检查不改代码） |
| log-diagnose | 日志自动诊断（Kibana，BUG 出双 MD） |
| db-query | 数据库查询（生产只读） |
| module-batch | 多模块并行改造（worktree + 子代理） |
| controller-check | Controller 校验规则提取 |

技能清单定义在 `.claude-plugin/marketplace.json`。

## 说明

- 敏感配置（Kibana/数据库凭据）不随插件安装，需按各技能 `references/config.example.json` 模板在 `~/.claude/skills/<技能>/` 下本地创建。
- 也可不用插件，直接运行 `install.sh` / `install.bat` 复制技能到 `~/.claude/skills/`。
