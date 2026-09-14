# nas-disk-diagnostic

NAS 硬盘故障诊断与可视化报告：SSH 远程连接 Synology 等 NAS，执行「基础状态采集 → SMART 深度诊断 → 坏盘可修复性评估 → 可视化报告 → 分级建议」完整流程。

## 使用

用户要求"查 NAS 硬盘""排查坏盘""看 SMART""硬盘诊断""RAID 降级排查"时自动触发。

```bash
python scripts/nas_diagnostic.py --host <ip> --port 22 --user <用户> --pass '<密码>' --phase basic
python scripts/nas_diagnostic.py --host <ip> --user <用户> --pass '<密码>' --phase smart
python scripts/nas_diagnostic.py --host <ip> --user <用户> --pass '<密码>' --phase rescan   # 写操作，需用户确认
python scripts/nas_diagnostic.py --host <ip> --user <用户> --pass '<密码>' --phase all
```

密码也可经环境变量 `NAS_PASSWORD` 传入，避免出现在命令行历史中。

**边界**：仅做只读采集与诊断（`rescan` 除外，执行前须用户确认）；改动 RAID 配置（re-add / 重建）属阵列变更，先给评估结论交用户决策。

## 能力

- 基础采集：文件系统占用、RAID 阵列状态（`/proc/mdstat` + `mdadm --detail`）、块设备列表、控制器信息、dmesg 中的 ATA / I/O 错误
- SMART 深度诊断：**扩展卡硬盘必须用 `smartctl -d sat`**（否则误报无 SMART 能力——本技能最重要的非显然知识点）、错误日志、自测日志、`hdparm` 物理信息、md superblock 检查
- 坏盘可修复性评估：按 197 / 198 / 5 / 187 / 188 / 199 / 9 等指标与决策树判定（参考 `references/smart-guide.md`）
- 可视化报告：指标卡 + 槽位网格 + SMART 对数刻度柱状图 + 通电时间对比 + 详细参数表（品牌带中文对照），模板见 `assets/report_template.html`
- 分级操作建议：立即处理 / 短期关注 / 中期预防 / 长期优化

## 文件

- `SKILL.md` — 技能指令（唯一入口）
- `scripts/nas_diagnostic.py` — SSH 取数脚本（只取数，不下结论）
- `references/smart-guide.md` — SMART 指标解读与判断流程
- `references/report-guide.md` — 可视化报告结构与配色规范
- `assets/report_template.html` — 单文件报告模板（填 `REPORT` 数据区即可）
- `requirements.txt` — paramiko

## 依赖

- Python 3 + paramiko（`pip install -r requirements.txt`）
- 目标 NAS 已开启 SSH 且账号具备读取 SMART / mdadm 的权限（多数命令走 `sudo`）
