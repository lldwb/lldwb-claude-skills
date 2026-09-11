@echo off
rem 卸载 lldwb-claude-skills 已安装的技能
setlocal
set DIR=%~dp0
python "%DIR%uninstall.py" %*
if errorlevel 1 pause
