@echo off
rem ============================================================
rem  INSTALAR.bat - Viking Software BETA 0.5.0-beta (Etapa 1.8)
rem  Instala el entorno virtual, las 3 dependencias, corre la
rem  prueba automatica y crea el acceso directo en el escritorio.
rem  Requisito previo: Python 3.12 o superior, 64 bits, "Add to PATH".
rem ============================================================
setlocal
cd /d "%~dp0"

echo.
echo  [1/5] Verificando Python 3.12 o superior...
python --version >nul 2>&1
if errorlevel 1 (
    echo  ERROR: Python no esta instalado o no esta en el PATH.
    echo  Instala Python desde python.org marcando "Add python.exe to PATH".
    pause
    exit /b 1
)
python --version

echo.
echo  [2/5] Creando entorno virtual (venv)...
if not exist venv (
    python -m venv venv
)

echo.
echo  [3/5] Instalando dependencias (customtkinter, openpyxl, Pillow)...
call venv\Scripts\activate.bat
pip install -r requirements.txt
if errorlevel 1 (
    echo  ERROR: fallo la instalacion de dependencias. Revisa tu conexion a internet.
    pause
    exit /b 1
)

echo.
echo  [4/5] Ejecutando prueba automatica del sistema...
python test_manual.py
if errorlevel 1 (
    echo  ERROR: la prueba automatica fallo. Avisa a soporte antes de usar el sistema.
    pause
    exit /b 1
)

echo.
echo  [5/5] Creando acceso directo en el escritorio...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ws = New-Object -ComObject WScript.Shell;" ^
  "$lnk = $ws.CreateShortcut([Environment]::GetFolderPath('Desktop') + '\Viking Software.lnk');" ^
  "$lnk.TargetPath = '%~dp0venv\Scripts\pythonw.exe';" ^
  "$lnk.Arguments = '\"' + '%~dp0main.py' + '\"';" ^
  "$lnk.WorkingDirectory = '%~dp0';" ^
  "$lnk.Description = 'Viking Software BETA - Peluqueria Vikingos';" ^
  "$lnk.Save()"

echo.
echo  ============================================================
echo   INSTALACION COMPLETA. Abri "Viking Software" del escritorio
echo   o ejecuta:  venv\Scripts\python.exe main.py
echo  ============================================================
pause
