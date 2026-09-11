# 可复用 Claude Skills

从业务项目实践中抽象出的 6 个通用工作流技能（Agent Skills），供其他项目复用。
每个技能是一个自包含目录，含 `SKILL.md`（frontmatter: `name` + `description`）及所需的脚本/参考文件。

## 技能列表

| Skill | 用途 | 附属文件 |
|-------|------|---------|
| fix-bug | Bug 修复标准工作流：先理解再动手、四段式定位、编译/测试验证、按仓库规范提交 | — |
| code-optimize | 代码优化工作流：SSOT、保持对外行为不变、commit 专员式提交 | — |
| commit-review | 提交评审：取数落盘 → 探索调用链 → 分层/契约/@Deprecated 检查，只检查不改代码 | scripts/check-commit.py |
| log-diagnose | 日志自动诊断：按 trace_id + 时间窗从 Kibana 拉日志、六类故障分类法、BUG 时产出双 MD（修复任务 + 事故报告） | scripts/log-diagnose.py、references/config.example.json |
| module-batch | 多模块并行改造：worktree 隔离 + 并行子代理 + 合并回主分支，含中断处理与经验教训速查 | — |
| controller-check | Controller 校验规则提取：协调调度子代理逐 Controller 追溯，按「模块→菜单→权限点→操作」模板合并输出文档 | references/extract-agent.md |

## 目录结构

```
skills/
├── <skill-name>/
│   ├── SKILL.md            # 技能指令（frontmatter: name + description）
│   ├── scripts/            # 取数/辅助脚本（可选）
│   └── references/         # 配置模板/子代理提示词等参考文件（可选）
```

## 安装到 Claude Code

```bash
# 复制到用户级 skills 目录（每个技能一个子目录）
cp -r skills/* ~/.claude/skills/
```

或作为 Plugin marketplace 安装（见 `.claude-plugin/marketplace.json`）。

## 使用注意

- 各技能为通用模板，正文中的占位符（`<skill 目录>`、`<模块>` 等）由调用时按项目实际情况填充。
- 敏感配置（如 `log-diagnose.config.json` 的 Kibana 凭据）不入库，按 `references/config.example.json` 模板在本地创建。
- 提交信息规范以各项目开发手册 / `AGENTS.md` 为权威依据，技能内仅保留通用约定。

## License

MIT
