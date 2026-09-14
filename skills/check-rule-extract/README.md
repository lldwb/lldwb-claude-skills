# check-rule-extract

业务操作前置校验规则提取：以**菜单**为入口（范围参数支持菜单完整路径或菜单名称，也可直接按 Controller 类名），通过菜单权限明细数据源定位菜单地址 → Controller，协调调度子代理逐 Controller 追溯 Service/Validator 校验逻辑，合并生成**业务管控逻辑 Excel 工作簿（.xlsx）**。

## 使用

用户要求"提取/梳理各接口操作前校验规则"、"生成管控逻辑收集表/操作前检查表"、"梳理某菜单下保存/删除/锁定/解锁前置校验"时自动触发。

## 能力

- 范围：`菜单完整路径`（`系统管理-用户管理-用户查询`，`-` 分隔）/ `菜单名称`（`用户查询`）/ `Controller类名`（无菜单体系的项目），逗号分隔可多个
- 菜单 → 地址 → Controller 定位：读菜单权限明细数据源构建菜单树，地址反查 Controller 类级路径；菜单层级由数据源给出，不按模块组织
- 调度执行分离：本 skill 只编排，追溯由子代理执行（`Agent` 工具 `subagent_type: general-purpose`，prompt = `references/extract-agent.md` + Controller 类名 + 菜单路径）
- 并发窗口 `--parallel N`（默认 5）、`--step` 逐批确认、`--out` 输出位置、`--menu-url` 菜单数据源覆盖
- 输出脚本化：`scripts/build_check_xlsx.py` 合并生成 .xlsx（表头 3 行、冻结 A4、样式固化），权限控制条目按权限点代码自动附加有权限角色
- 中断恢复：落盘片段保留，重跑跳过已完成 Controller
- 递归子代理防上下文超限（索引层读签名区，方法体由嵌套实例追溯）

## 文件

- `SKILL.md` — 技能指令（唯一入口）
- `references/extract-agent.md` — 子代理提示词模板（递归遍历提取器，表格结构落盘）
- `scripts/build_check_xlsx.py` — 合并生成 xlsx 脚本（参数 `--tasks` / `--menu` / `--out` / `--source` / `--no-roles`）

## 依赖

- Python 3、`pip install xlrd openpyxl`（xlrd 读老式 xls 菜单权限明细，openpyxl 生成 xlsx）
- 菜单权限明细数据源（有菜单体系的项目；`--menu-url` 可覆盖）
