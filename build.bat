@echo off
echo Gerando build do LuiHome...
python -m PyInstaller LuiHome.spec
echo.
echo Build concluido! O executavel esta em: dist\LuiHome.exe
pause

