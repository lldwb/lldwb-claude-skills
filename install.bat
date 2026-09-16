@echo off
rem 安装 lldwb-claude-skills 到 ~/.claude/skills/（按 config.json 启用清单）
setlocal
set DIR=%~dp0
python "%DIR%install.py" %*
if errorlevel 1 python -X utf8 -c "print('\u8bf7\u6309\u4efb\u610f\u952e\u7ee7\u7eed. . .', flush=True); input()"
