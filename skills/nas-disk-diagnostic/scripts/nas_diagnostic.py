#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NAS 硬盘诊断脚本（SSH 远程取数，不做判定——判定由调用方 agent 完成）。

用法:
    python nas_diagnostic.py --host <ip> --port 22 --user <用户> --pass '<密码>' --phase basic
    python nas_diagnostic.py --host <ip> --user <用户> --pass '<密码>' --phase smart
    python nas_diagnostic.py --host <ip> --user <用户> --pass '<密码>' --phase rescan
    python nas_diagnostic.py --host <ip> --user <用户> --pass '<密码>' --phase all

阶段说明:
    basic  - 文件系统 / RAID / 块设备 / 控制器 / dmesg 基础采集
    smart  - 全盘 SMART 深度诊断（关键：扩展卡硬盘用 -d sat）
    rescan - 在线 rescan 尝试恢复掉线硬盘（写 /sys，需用户确认后再执行）
    all    - 依次执行 basic + smart

密码也可经环境变量 NAS_PASSWORD 传入，避免出现在命令行历史与进程列表中。

依赖: paramiko（pip install -r requirements.txt）
"""
import sys
import os
import argparse
import codecs

# Windows 控制台缺省 GBK，强制 UTF-8 输出，规避中文乱码。
# reconfigure 不可用时回退到基于底层 buffer 的 UTF-8 写入器兜底。
def _ensure_utf8():
    for name in ("stdout", "stderr"):
        stream = getattr(sys, name, None)
        if stream is None:
            continue
        try:
            stream.reconfigure(encoding="utf-8", errors="backslashreplace")
            continue
        except Exception:
            pass
        try:
            buf = getattr(stream, "buffer", None)
            if buf is not None and hasattr(stream, "write"):
                setattr(sys, name, codecs.getwriter("utf-8")(buf, errors="backslashreplace"))
        except Exception:
            pass


_ensure_utf8()


def _load_paramiko():
    """延迟导入 paramiko：缺依赖时给出安装提示，而不是让 --help 也崩掉。"""
    try:
        import paramiko  # noqa: F401
        return paramiko
    except ImportError:
        print("缺少依赖 paramiko：请先执行 pip install -r requirements.txt", file=sys.stderr)
        sys.exit(2)


def connect_ssh(host, port, user, password):
    paramiko = _load_paramiko()
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, port=port, username=user, password=password, timeout=15)
    return ssh


def run_sudo(ssh, script, password):
    """通过 sudo 执行 bash 脚本，自动传入密码。"""
    cmd = f"echo '{password}' | sudo -S bash -c '{script}' 2>&1"
    _, stdout, stderr = ssh.exec_command(cmd, timeout=120)
    out = stdout.read().decode('utf-8', errors='replace')
    err = stderr.read().decode('utf-8', errors='replace')
    return out + (f'\n[stderr]\n{err}' if err.strip() else '')


def phase_basic(ssh, password):
    """阶段 1：基础状态采集（只读）。"""
    script = r'''
echo "=================================================="
echo "1. 文件系统占用 (df -h)"
echo "=================================================="
df -h

echo ""
echo "=================================================="
echo "2. RAID 阵列状态 (cat /proc/mdstat)"
echo "=================================================="
cat /proc/mdstat

echo ""
echo "=================================================="
echo "3. 各阵列详情 (mdadm --detail)"
echo "=================================================="
for md in /dev/md*; do
    if [ -b "$md" ]; then
        echo "--- $md ---"
        mdadm --detail $md 2>/dev/null | head -40
        echo ""
    fi
done

echo "=================================================="
echo "4. 块设备列表"
echo "=================================================="
ls -la /dev/sata* /dev/sd* /dev/nvme* 2>/dev/null | head -40

echo ""
echo "=================================================="
echo "5. 控制器信息 (lspci)"
echo "=================================================="
lspci 2>/dev/null | grep -iE "sata|sas|raid|storage" || echo "lspci 不可用"

echo ""
echo "=================================================="
echo "6. 近期硬盘/ATA 错误日志 (dmesg)"
echo "=================================================="
dmesg 2>/dev/null | grep -iE "ata[0-9]+|I/O error|exception Emask|SError|hard resetting link|failed.*Command|md_error|md/raid|blk_update_request" | tail -60
'''
    print(run_sudo(ssh, script, password))


def phase_smart(ssh, password):
    """阶段 2：SMART 深度诊断（只读）。关键：扩展卡硬盘必须用 -d sat。"""
    script = r'''
echo "=================================================="
echo "SMART 深度诊断 (使用 -d sat 参数)"
echo "=================================================="
echo "注意:通过扩展卡(如 ASMedia ASM1166 等)连接的硬盘"
echo "必须使用 smartctl -d sat 才能读取 SMART"
echo ""

# 自动发现所有 sata/sd 设备
for dev in $(ls /dev/sata* /dev/sd[a-z] 2>/dev/null | grep -v p | sort); do
    if [ -b "$dev" ]; then
        echo "=================================================="
        echo "[$dev] 完整 SMART"
        echo "=================================================="
        # 先尝试 -d sat,失败则回退默认
        smartctl -d sat -a $dev 2>&1 | head -80
        echo ""
        echo "--- SMART 错误日志 ---"
        smartctl -d sat -l error $dev 2>&1 | tail -20
        echo ""
        echo "--- SMART 自测日志 ---"
        smartctl -d sat -l selftest $dev 2>&1 | tail -15
        echo ""
        echo "--- hdparm 物理信息 ---"
        hdparm -I $dev 2>/dev/null | grep -iE "Model Number|Serial Number|Firmware Revision|Transport|Serial ATA|speed|Nominal Media Rotation Rate|Logical.*Sector|Physical.*Sector|device size" | head -10
        echo ""
    fi
done

echo "=================================================="
echo "RAID 各阵列成员状态 (mdadm --detail)"
echo "=================================================="
for md in /dev/md*; do
    if [ -b "$md" ]; then
        echo "--- $md ---"
        mdadm --detail $md 2>/dev/null | grep -E "State|Active|Working|Failed|Spare|Raid Level|Raid Devices|sync|rebuild|sata|sd"
        echo ""
    fi
done

echo "=================================================="
echo "各盘 md superblock 检查"
echo "=================================================="
for dev in $(ls /dev/sata*p[0-9] /dev/sd[a-z][0-9] 2>/dev/null | sort); do
    result=$(mdadm --examine $dev 2>&1 | head -5)
    if echo "$result" | grep -q "Magic"; then
        echo "$dev: 有 md superblock"
        echo "$result"
        echo ""
    fi
done
'''
    print(run_sudo(ssh, script, password))


def phase_rescan(ssh, password):
    """阶段 3：在线 rescan（写 /sys，属写操作——执行前须获用户确认）。"""
    script = r'''
echo "=================================================="
echo "在线 SATA Rescan (尝试恢复掉线硬盘)"
echo "=================================================="

echo "--- rescan 前块设备列表 ---"
ls /dev/sata* /dev/sd* 2>/dev/null | grep -v p | sort

echo ""
echo "--- 触发所有 SCSI host rescan ---"
for h in /sys/class/scsi_host/host*/; do
    echo "- - -" > ${h}scan 2>/dev/null && echo "$(basename $h): rescan triggered" || true
done

echo ""
echo "等待 3 秒..."
sleep 3

echo ""
echo "--- rescan 后块设备列表 ---"
ls /dev/sata* /dev/sd* 2>/dev/null | grep -v p | sort

echo ""
echo "--- dmesg 最新 30 行 ---"
dmesg 2>/dev/null | tail -30

echo ""
echo "--- 各阵列当前状态 ---"
cat /proc/mdstat
'''
    print(run_sudo(ssh, script, password))


def main():
    parser = argparse.ArgumentParser(description='NAS 硬盘诊断脚本（只取数，不下结论）')
    parser.add_argument('--host', required=True, help='NAS 主机地址')
    parser.add_argument('--port', type=int, default=22, help='SSH 端口')
    parser.add_argument('--user', required=True, help='SSH 用户名')
    parser.add_argument('--pass', dest='password', default=None,
                        help='SSH 密码（缺省时读环境变量 NAS_PASSWORD）')
    parser.add_argument('--phase', choices=['basic', 'smart', 'rescan', 'all'], default='all',
                        help='诊断阶段:basic/smart/rescan/all')
    args = parser.parse_args()

    password = args.password or os.environ.get('NAS_PASSWORD')
    if not password:
        print('缺少密码：请用 --pass 传入，或设置环境变量 NAS_PASSWORD', file=sys.stderr)
        sys.exit(2)

    try:
        ssh = connect_ssh(args.host, args.port, args.user, password)
    except Exception as e:
        print(f"SSH 连接失败: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        if args.phase in ('basic', 'all'):
            phase_basic(ssh, password)
        if args.phase in ('smart', 'all'):
            phase_smart(ssh, password)
        if args.phase == 'rescan':
            phase_rescan(ssh, password)
    finally:
        ssh.close()

    print('\n[诊断完成]')


if __name__ == '__main__':
    main()
