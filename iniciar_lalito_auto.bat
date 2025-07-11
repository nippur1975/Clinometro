@echo off
REM Obtiene la ruta del directorio donde se encuentra este archivo .bat
set "BATCH_DIR=%~dp0"

REM Cambia al directorio del script de Python
cd /d "%BATCH_DIR%"

REM Ejecuta el script de Python. 
REM Asegúrate de que 'python' esté en tu PATH o proporciona la ruta completa al ejecutable de Python.
REM Si clinometro.py está en un subdirectorio, ajusta la ruta.
echo Iniciando Lalito Clinometro...
python clinometro.py

REM Opcional: Pausa para ver mensajes si hay errores al inicio (puedes quitarla en producción)
REM pause
