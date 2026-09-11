#!/usr/bin/env bash
# 卸载 lldwb-claude-skills 已安装的技能
set -e
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python "$DIR/uninstall.py" "$@"
