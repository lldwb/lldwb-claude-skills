---
name: nas-disk-diagnostic
description: NAS 硬盘故障诊断与可视化报告：SSH 远程连接 Synology 等 NAS，按「基础状态采集 → SMART 深度诊断 → 坏盘可修复性评估 → 可视化报告 → 分级建议」流程排查，含扩展卡硬盘必须用 smartctl -d sat 等关键知识点。当用户要求"查 NAS 硬盘""排查坏盘""看 SMART""硬盘诊断""RAID 降级排查""存储空间不够看看盘"时使用——只做只读采集与诊断（rescan 除外，需用户确认），结论必须由 SMART 原始值支撑；诊断脚本只取数不下结论。边界：非 NAS 场景的磁盘/文件系统问题按通用系统排障处理；需要改动 RAID 配置（re-add / 重建）时先给出评估结论并交用户决策。
---

# NAS 硬盘诊断

通过 SSH 远程对 NAS（Synology 等）执行完整硬盘健康诊断，生成可视化报告，评估坏盘可修复性。

## 角色

你是存储排障工程师：**先采集、再解读、最后给分级建议**。诊断结论必须由 SMART 原始值与 RAID 状态支撑，不用"可能是""应该是"下结论。

## 适用场景

- NAS 存储空间查询、磁盘占用检查
- RAID 阵列降级（degraded）排查
- 硬盘 SMART 健康检查
- 定位故障物理硬盘并评估是否可修复
- 生成硬盘状态可视化报告

## 前置条件

1. 目标 NAS 已配置 SSH 访问（地址 / 端口 / 账号 / 密码）。
2. 已安装 `paramiko`：`pip install -r requirements.txt`。
3. 如项目已配置 NAS 的 SSH / MCP 连接信息，可直接复用连接参数。

## 诊断流程

### 阶段 1：基础状态采集

执行 `scripts/nas_diagnostic.py`（`--phase basic`），自动完成：

1. **文件系统占用**：`df -h`
2. **RAID 阵列状态**：`/proc/mdstat` + `mdadm --detail /dev/md*`
3. **块设备列表**：`/dev/sata*` / `/dev/sd*` / `/dev/nvme*`
4. **控制器信息**：`lspci` 中与 SATA / SAS / RAID / storage 相关的行
5. **内核错误日志**：`dmesg` 中 ATA / I/O error / failed command / md 相关行

```bash
python scripts/nas_diagnostic.py --host <ip> --port 22 --user <用户> --pass '<密码>' --phase basic
```

> 密码也可经环境变量 `NAS_PASSWORD` 传入，避免出现在命令行历史中（脚本优先取 `--pass`）。

### 阶段 2：SMART 深度诊断（关键）

**核心技术点：Synology / 扩展卡上的硬盘必须加 `-d sat`**

通过 ASMedia ASM1166 等扩展卡连接的硬盘，`smartctl` 默认查询会误报 “device lacks SMART capability”；必须用 `smartctl -d sat -a /dev/sataN` 才能读到真实 SMART 数据。**这是本技能最重要的非显然知识点**。

```bash
python scripts/nas_diagnostic.py --host <ip> --port 22 --user <用户> --pass '<密码>' --phase smart
```

采集内容：各盘完整 SMART 属性、SMART 错误日志（`-l error`）、SMART 自测日志（`-l selftest`）、`hdparm -I` 物理信息、mdadm 各阵列成员详情、各盘 md superblock 检查。

```bash
python scripts/nas_diagnostic.py --host <ip> --user <用户> --pass '<密码>' --phase all   # basic + smart
```

### 阶段 3：坏盘可修复性评估

按 `references/smart-guide.md` 解读 SMART 指标。关键判定：

| 指标 | 含义 | 可修复判断 |
|------|------|-----------|
| Current_Pending_Sector (197) | 待处理坏扇区 | >0 需关注，>1000 通常不可修复 |
| Offline_Uncorrectable (198) | 离线不可纠正扇区 | >0 表示盘片物理损坏 |
| Reallocated_Sector_Ct (5) | 已重映射扇区 | 持续增长说明盘片持续恶化 |
| Reported_Uncorrect (187) | 不可纠正错误次数 | >0 需警惕 |
| Command_Timeout (188) | 命令超时次数 | 异常高值表示通信故障 |
| UDMA_CRC_Error_Count (199) | 传输 CRC 错误 | 通常线缆问题，非盘体故障 |
| Power_On_Hours (9) | 通电小时数 | >40000h 进入高风险期 |

**修复决策树：**

1. 硬盘掉线 → 尝试在线 rescan（`--phase rescan`，会写 `/sys/class/scsi_host/host*/scan`，**属写操作，执行前需用户确认**）
2. rescan 后重新识别 → 检查 SMART：
   - 197 / 198 为 0 → 可重新加入阵列
   - 197 / 198 > 0 但 < 100 → 谨慎，建议先跑长自测
   - 197 / 198 > 1000 → **不可修复**，需物理更换
3. rescan 失败 → 硬盘或控制器损坏，需物理更换

### 阶段 4：可视化报告生成

报告结构与配色见 `references/report-guide.md`，模板见 `assets/report_template.html`。报告包含：

- 顶部指标卡片（在线硬盘数、故障数、降级阵列数、数据安全状态）
- 硬盘槽位状态网格（按实际盘位数，绿 / 黄 / 红三色标识）
- 故障盘 SMART 关键指标柱状图（Chart.js，**对数刻度**，数值跨度大）
- 各盘通电时间对比柱状图
- 详细参数表格（品牌带中文对照）

**产出方式**：环境如有内联展示能力（如内联 widget 工具）→ 内联展示；否则把渲染好的 HTML 落盘到 `<产物目录>`（默认 `<项目根>/.tasks/nas-report-<日期>.html`，过程产物不入库）并提示用户用浏览器打开。

**品牌中文对照表**（生成报告时使用）：

| 英文 | 中文 | 说明 |
|------|------|------|
| Phison | 群联 | 台湾 SSD 主控厂商 |
| LITEON | 建兴 | 台湾光宝科技旗下 |
| HGST | 昱科 | 原日立，现属 WD |
| Seagate | 希捷 | 美国硬盘厂商 |
| WD | 西部数据 | 美国硬盘厂商 |
| Samsung | 三星 | 韩国厂商 |
| Toshiba | 东芝 | 日本厂商（现 Kioxia 铠侠） |
| Kingston | 金士顿 | 美国内存厂商 |
| Crucial | 英睿达 | Micron 美光旗下 |

### 阶段 5：操作建议

按诊断结果给出分级建议：

1. **立即处理**：已损坏盘需物理更换，触发阵列重建（重建前先确认备份可用与阵列冗余度）
2. **短期关注**：CRC 错误盘检查线缆与接口
3. **中期预防**：老化盘（通电 > 30000h）制定更换计划
4. **长期优化**：混用硬盘型号的统一化建议

## 常见陷阱

1. **smartctl 误报**：扩展卡硬盘必须加 `-d sat`，否则误报无 SMART 能力
2. **rescan 假象**：坏盘 rescan 后可能重新被识别，但不代表可用——必须查 SMART
3. **mdadm re-add 风险**：坏盘直接 re-add 到阵列会导致重建再次失败，甚至阵列崩溃
4. **缓存未知**：现代硬盘不通过 ATA IDENTIFY 报告缓存，`hdparm` 返回 unknown，需查厂商规格表
5. **生产日期不可得**：SMART 不存储生产日期，只能按型号发布时间推断
6. **Seagate 原始值特性**：`Raw_Read_Error_Rate` / `Seek_Error_Rate` 原始值极大是算法特性，不代表故障——看标准化值（VALUE / WORST 是否高于 THRESH）

## 验证

- 采集完整性：每个阶段声明的命令都有对应输出段（缺失的说明原因，如设备不存在 / 权限不足），不静默跳过。
- 结论有据：每条故障判定都能指回具体的 SMART 属性值或 dmesg 行；**只有结论没有原始值的判定不成立**。
- 只读边界：除 `--phase rescan`（需用户确认）外，不做任何写操作（不改阵列、不 re-add、不改配置）。
- 报告与数据一致：报告中的盘位、容量、故障数与采集输出逐项对得上。

**判定口径**：四项均通过方可交付诊断结论；采集不完整或结论无原始值支撑时，说明缺哪一项、为什么缺，不给确定的修复建议。

## 任务目标

产出有原始数据支撑的 NAS 硬盘诊断结论：RAID 与 SMART 状态明确、故障盘定位到物理槽位、可修复性有判定依据、分级建议可执行。

## 注意事项

- **只读优先**：诊断本身只需读操作；`rescan`（写 `/sys`）与任何阵列变更（re-add / 重建）都必须先向用户说明影响并取得确认。
- **不要在报告里写凭据**：连接信息（地址 / 账号 / 密码）不得写进报告或诊断输出，报告只含设备与健康数据。
- **阵列降级时先保数据**：发现降级 / 掉盘时，第一建议是确认备份与冗余状态，而不是立刻 re-add 或重建。
- **结论分级不夸大**：CRC 类错误不要判为盘体故障；Seagate 原始值大不要判为坏盘——按 `references/smart-guide.md` 的判据说话。
- **确认请求无应答时**：只读采集继续；写操作（rescan / 阵列变更）停下等待确认并在汇报中标明"该决策未获用户确认"。

## 输入

诊断目标（可选）：NAS 地址 / 端口 / 账号、诊断阶段（basic / smart / rescan / all）、关注的盘位或阵列、报告产出位置：
