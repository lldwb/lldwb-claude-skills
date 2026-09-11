@echo off
rem 安装 lldwb-claude-skills 到 ~/.claude/skills/（按 config.json 启用清单）
setlocal
set DIR=%~dp0
python "%DIR%install.py" %*
if errorlevel 1 pause
