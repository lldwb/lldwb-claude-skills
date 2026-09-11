# controller-check

业务操作前置校验规则提取：以 Controller 接口为入口，协调调度子代理逐 Controller 追溯 Service/Validator 校验逻辑，按「模块 → 一级菜单 → 二级菜单 → 权限点 → 操作」模板合并输出"系统各业务点操作前检查"文档。

## 使用

用户要求"提取/梳理各接口操作前校验规则"、"生成操作前检查文档"、"梳理 Controller 的保存/删除/锁定/解锁前置校验"时自动触发。

## 能力

- 范围三档：`all`（全量）/ `mod:<模块名>` / `<Controller类名>`（逗号分隔多个）
- 调度执行分离：本 skill 只编排，追溯由子代理执行（`Agent` 工具 `subagent_type: general-purpose`，prompt = `references/extract-agent.md` + Controller 参数）
- 并发窗口 `--parallel N`（默认 5）、`--step` 逐批确认、`--out` 输出位置
- 中断恢复：落盘片段保留，重跑跳过已完成 Controller
- 递归子代理防上下文超限（索引层读签名区，方法体由嵌套实例追溯）

## 文件

- `SKILL.md` — 技能指令（唯一入口）
- `references/extract-agent.md` — 子代理提示词模板（递归遍历提取器）

## 依赖

- git、Python 3（无脚本，仅目录检查）
