@echo off
:: Script para deshacer la configuración automática y el acceso con Shift+H
:: By DeepSeek Chat - 2024

set "DESTINO_FOLDER=%APPDATA%\MiAppOculta"
set "SHORTCUT=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\MiAppOculta.lnk"

:: 1. Eliminar acceso directo del inicio
if exist "%SHORTCUT%" (
    attrib -h "%SHORTCUT%"
    del /q "%SHORTCUT%"
    echo [✓] Acceso directo eliminado: %SHORTCUT%
) else (
    echo [X] No se encontró el acceso directo en Inicio.
)

:: 2. Eliminar carpeta oculta y el EXE
if exist "%DESTINO_FOLDER%" (
    attrib -h -s "%DESTINO_FOLDER%"
    rmdir /s /q "%DESTINO_FOLDER%"
    echo [✓] Carpeta oculta eliminada: %DESTINO_FOLDER%
) else (
    echo [X] No se encontró la carpeta oculta.
)

:: 3. Eliminar entradas del registro
reg delete "HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run" /v "MiAppOcultaHotkey" /f >nul 2>&1
if %errorlevel% equ 0 (
    echo [✓] Entrada de registro 'Run' eliminada.
) else (
    echo [X] No se encontró la entrada en 'Run'.
)

reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced" /v "Hotkey_MiApp" /f >nul 2>&1
if %errorlevel% equ 0 (
    echo [✓] Entrada de tecla rápida (Shift+H) eliminada.
) else (
    echo [X] No se encontró la entrada del hotkey.
)

:: Mensaje final
echo.
echo [!] Desinstalación completada. Todos los restos se han eliminado.
pause