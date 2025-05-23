@echo off
setlocal enabledelayedexpansion

echo ===================================
echo    Build do Sistema Fiado v1.0.8
echo ===================================
echo.

:: Verificar se o Inno Setup está instalado
if not exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" (
    echo [ERRO] Inno Setup nao encontrado!
    echo Por favor, instale o Inno Setup em C:\Program Files (x86)\Inno Setup 6
    pause
    exit /b 1
)

:: Verificar se o Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python nao encontrado!
    echo Por favor, instale o Python e adicione ao PATH
    pause
    exit /b 1
)

:: Verificar se o pip está instalado
pip --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] pip nao encontrado!
    echo Por favor, instale o pip
    pause
    exit /b 1
)

:: Verificar se o Node.js está instalado
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Node.js nao encontrado!
    echo Por favor, instale o Node.js
    pause
    exit /b 1
)

:: Verificar se o npm está instalado
npm --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] npm nao encontrado!
    echo Por favor, instale o npm
    pause
    exit /b 1
)

:: Verificar se o PyInstaller está instalado
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo [INFO] Instalando PyInstaller...
    pip install pyinstaller
)

:: Verificar se o PySide6 está instalado
pip show PySide6 >nul 2>&1
if errorlevel 1 (
    echo [INFO] Instalando PySide6...
    pip install PySide6
)

:: Verificar se o requests está instalado
pip show requests >nul 2>&1
if errorlevel 1 (
    echo [INFO] Instalando requests...
    pip install requests
)

:: Verificar se o whatsapp-web.js está instalado
if not exist "whatsapp_bot\node_modules\whatsapp-web.js" (
    echo [INFO] Instalando dependencias do WhatsApp Bot...
    cd whatsapp_bot
    npm install
    cd ..
)

echo [INFO] Verificando arquivos necessarios...

:: Verificar diretórios necessários
set "DIRS=icons whatsapp_bot views dist build"
for %%d in (%DIRS%) do (
    if not exist "%%d" (
        echo [ERRO] Diretorio '%%d' nao encontrado
        pause
        exit /b 1
    )
)

:: Verificar arquivos necessários
set "FILES=LICENSE.txt release.md installer.iss"
for %%f in (%FILES%) do (
    if not exist "%%f" (
        echo [ERRO] Arquivo '%%f' nao encontrado
        pause
        exit /b 1
    )
)

echo [INFO] Limpando builds anteriores...
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"
if exist "Sistema_Fiado_Setup.exe" del /f /q "Sistema_Fiado_Setup.exe"

echo [INFO] Compilando o Sistema Fiado...

:: Sincronizar versões antes de compilar
python sync_version.py

:: Compilar o executável com PyInstaller
echo [INFO] Compilando executavel...
pyinstaller --noconfirm --onefile --windowed --icon "icons\ICONE-LOGO.ico" --add-data "icons;icons" --add-data "whatsapp_bot;whatsapp_bot" --add-data "LICENSE.txt;." --add-data "version.json;." --add-data "release.md;." "main.py"

:: Compilar o instalador com Inno Setup
echo [INFO] Compilando instalador...
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss

:: Verificar se a compilação foi bem sucedida
if not exist "dist\Sistema Fiado.exe" (
    echo [ERRO] Executavel nao encontrado apos compilacao
    pause
    exit /b 1
)

:: Verificar se o instalador foi criado
if not exist "Sistema_Fiado_Setup.exe" (
    echo [ERRO] Instalador nao encontrado apos compilacao
    pause
    exit /b 1
)

echo.
echo [SUCESSO] Instalador criado com sucesso: Sistema_Fiado_Setup.exe
echo.
echo Tamanho do instalador: 
for %%A in (Sistema_Fiado_Setup.exe) do echo %%~zA bytes
echo.
pause 