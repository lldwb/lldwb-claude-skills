@echo off
rem 卸载 lldwb-claude-skills 已安装的技能
setlocal
set DIR=%~dp0
python "%DIR%uninstall.py" %*
if errorlevel 1 python -X utf8 -c "print('\u8bf7\u6309\u4efb\u610f\u952e\u7ee7\u7eed. . .', flush=True); input()"
