#!/usr/bin/env bash
# 安装 lldwb-claude-skills 到 ~/.claude/skills/（按 config.json 启用清单）
set -e
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python "$DIR/install.py" "$@"
