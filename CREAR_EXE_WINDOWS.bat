@echo off
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (set "PY=py -3") else (set "PY=python")
%PY% -m pip install --upgrade pyinstaller pystray pillow
if errorlevel 1 goto error
%PY% -m PyInstaller --noconfirm --clean --onefile --windowed --name ProduccionLiturgicaOBS --add-data "panel.html;." --add-data "overlay.html;." launcher.py
if errorlevel 1 goto error
echo Ejecutable generado en dist\ProduccionLiturgicaOBS.exe
pause
exit /b 0
:error
echo Error durante la compilacion. Revise Python y dependencias.
pause
exit /b 1
