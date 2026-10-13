@echo off
rem ============================================================
rem  VIKING SOFTWARE BETA - DIAGNOSTICO
rem  Ejecuta el programa con la consola visible y guarda cualquier
rem  error en logs\diagnostico.txt
rem
rem  USO: doble clic cuando el programa "no abre".
rem  Al terminar se abre solo el archivo logs\diagnostico.txt:
rem  mandalo completo (o una foto) a soporte.
rem ============================================================
cd /d "%~dp0"
if not exist logs mkdir logs

echo ==== DIAGNOSTICO VIKING SOFTWARE - %DATE% %TIME% ==== > logs\diagnostico.txt
echo. >> logs\diagnostico.txt
echo ---- SISTEMA ---- >> logs\diagnostico.txt
ver >> logs\diagnostico.txt 2>&1
echo. >> logs\diagnostico.txt

echo ---- EJECUCION DEL PROGRAMA (consola visible) ---- >> logs\diagnostico.txt
echo (Se abre el programa. Probalo y despues cerralo para completar el diagnostico.)
if exist venv\Scripts\python.exe (
    venv\Scripts\python.exe main.py >> logs\diagnostico.txt 2>&1
) else (
    python main.py >> logs\diagnostico.txt 2>&1
)

echo. >> logs\diagnostico.txt
echo ---- ULTIMAS LINEAS DE logs\viking.log ---- >> logs\diagnostico.txt
type logs\viking.log >> logs\diagnostico.txt 2>&1

echo. >> logs\diagnostico.txt
echo ==== FIN DEL DIAGNOSTICO ==== >> logs\diagnostico.txt
echo.
echo Listo. Se va a abrir logs\diagnostico.txt - mandalo a soporte.
start notepad.exe logs\diagnostico.txt
pause
