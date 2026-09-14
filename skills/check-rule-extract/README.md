# check-rule-extract

业务操作前置校验规则提取（编排调度）：以**菜单**为入口（范围参数支持菜单完整路径或菜单名称，无菜单体系的项目可直接按 Controller 类名），通过菜单权限明细数据源定位「菜单地址 → Controller」，协调调度子代理逐 Controller 追溯 Service / Validator 校验逻辑，合并生成**业务管控逻辑 Excel 工作簿（.xlsx）**。核心纪律：只编排、不追溯，只读业务代码、不修改任何文件。

## 使用

用户要求"提取/梳理各接口操作前校验规则""生成管控逻辑收集表/操作前检查表""梳理某菜单下保存/删除/锁定/解锁前置校验"时自动触发；也可显式要求"用 check-rule-extract skill 梳理某菜单下各接口的操作前校验"。

**边界**：本技能只提取、不改代码——需要修复提取中发现的业务缺陷用 `bug-fix`，需要把提取结论沉淀为项目文档并与代码对齐用 `doc-sync`。

## 能力

- 范围三档：`菜单完整路径`（`系统管理-用户管理-用户查询`，`-` 分隔）/ `菜单名称`（`用户查询`）/ `Controller类名`（无菜单体系的项目），逗号分隔可多个
- 菜单 → 地址 → Controller 定位：读菜单权限明细数据源构建菜单树，地址反查 Controller 类级路径；菜单层级由数据源给出，不按模块组织
- 调度执行分离：本 skill 只编排，追溯由子代理执行（`Agent` 工具 `subagent_type: general-purpose` + `run_in_background=true`，prompt = `references/extract-agent.md` 全文 + Controller 类名 + 菜单路径）
- 固定并发窗口 `--parallel N`（默认 5，硬上限）、`--step` 逐批确认、`--out` 输出位置、`--menu-url` 菜单数据源覆盖
- 输出脚本化：`scripts/build_check_xlsx.py` 合并生成 .xlsx（缺省 11 列通用模板、样式固化、冻结 A2；`--template` 可对接既有表格样式），权限控制条目按权限点代码自动附加有权限角色
- 中断恢复：落盘片段保留，重跑跳过已完成的 Controller；单 Controller 失败重试 ≤ 2 次，超限记「需人工介入」
- 递归子代理防上下文超限（索引层只读签名区，方法体由嵌套实例追溯）

## 文件

- `SKILL.md` — 技能指令（唯一入口）
- `references/extract-agent.md` — 子代理提示词模板（递归遍历提取器，按表格结构落盘片段）
- `references/output-and-rules.md` — 输出工作簿列定义、样式与模板覆盖说明 + 合并输出通用规则
- `scripts/build_check_xlsx.py` — 合并生成 xlsx 脚本（参数 `--tasks` / `--menu` / `--out` / `--source` / `--template` / `--no-roles`）
- `requirements.txt` — 三方依赖清单

## 依赖

- Python 3、`pip install -r requirements.txt`（xlrd 读老式 xls 菜单权限明细，openpyxl 生成 xlsx）
- 菜单权限明细数据源（有菜单体系的项目；`--menu-url` 可覆盖）
- 子代理调度能力（`Agent` 工具，`subagent_type: general-purpose`）
