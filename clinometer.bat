@echo off
:: Script para configurar la ejecución automática y acceso con Shift+H

:: 1. Copiar el EXE a una ubicación oculta (si no está allí)
set "EXE_ORIGINAL=clinometro.exe"  :: Reemplaza con el nombre de tu EXE
set "DESTINO_FOLDER=%APPDATA%\MiAppOculta"
set "DESTINO_EXE=%DESTINO_FOLDER%\%EXE_ORIGINAL%"

if not exist "%DESTINO_FOLDER%" (
    mkdir "%DESTINO_FOLDER%"
    attrib +h +s "%DESTINO_FOLDER%"
)

if not exist "%DESTINO_EXE%" (
    copy "%EXE_ORIGINAL%" "%DESTINO_EXE%"
    attrib +h "%DESTINO_EXE%"
)

:: 2. Crear acceso directo en el inicio
set "SHORTCUT=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\MiAppOculta.lnk"

:: Si no existe el acceso directo, crearlo
if not exist "%SHORTCUT%" (
    echo Creando acceso directo...
    set "VBS_SCRIPT=%TEMP%\CrearAccesoDirecto.vbs"
    
    > "%VBS_SCRIPT%" (
        echo Set oWS = WScript.CreateObject("WScript.Shell"^)
        echo sLinkFile = "%SHORTCUT%"
        echo Set oLink = oWS.CreateShortcut(sLinkFile^)
        echo oLink.TargetPath = "%DESTINO_EXE%"
        echo oLink.WorkingDirectory = "%DESTINO_FOLDER%"
        echo oLink.Save
    )
    
    cscript /nologo "%VBS_SCRIPT%"
    del "%VBS_SCRIPT%"
    attrib +h "%SHORTCUT%"
)

:: 3. Configurar tecla de acceso rápido (Shift + H)
reg add "HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run" /v "MiAppOcultaHotkey" /t REG_SZ /d "%DESTINO_EXE%" /f

:: Crear entrada en el registro para el hotkey (Shift + H)
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced" /v "Hotkey_MiApp" /t REG_SZ /d "H" /f

:: Mensaje final
echo Configuración completada:
echo - El programa se ejecutará al iniciar Windows
echo - Está configurado para abrir con Shift + H
echo - Los archivos están ocultos en %DESTINO_FOLDER%

pause