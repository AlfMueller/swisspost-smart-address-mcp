@echo off
chcp 65001 >nul
echo [INFO] Starte Swisspost MCP Server mit HTTP Proxy...
echo.

REM Prüfe ob Python installiert ist
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python ist nicht installiert oder nicht im PATH
    pause
    exit /b 1
)

REM Prüfe ob .env Datei existiert
if not exist ".env" (
    echo [ERROR] .env Datei nicht gefunden
    echo.
    echo [INFO] Erstellen Sie die .env Datei:
    echo    copy config.env .env
    echo    Dann .env bearbeiten und echte Credentials eintragen
    echo.
    pause
    exit /b 1
)

REM Prüfe ob smart-address-agent.py existiert
if not exist "smart-address-agent.py" (
    echo [ERROR] smart-address-agent.py nicht gefunden
    echo Stellen Sie sicher, dass Sie im Projektverzeichnis sind
    pause
    exit /b 1
)

REM Prüfe ob aiohttp installiert ist
python -c "import aiohttp" >nul 2>&1
if errorlevel 1 (
    echo [ERROR] aiohttp nicht installiert
    echo.
    echo [INFO] Installieren Sie aiohttp:
    echo    pip install aiohttp
    echo.
    pause
    exit /b 1
)

echo [INFO] Teste Swisspost API Credentials...
python test-credentials.py

if errorlevel 1 (
    echo.
    echo [ERROR] Credentials-Test fehlgeschlagen
    echo Bitte überprüfen Sie Ihre .env Datei
    pause
    exit /b 1
)

echo.
echo [SUCCESS] Credentials-Test erfolgreich
echo.
echo [INFO] Starte HTTP Proxy (mit integriertem MCP Server)...
echo.
echo [INFO] MCP Server läuft intern im HTTP Proxy
echo [INFO] HTTP Proxy läuft auf http://localhost:3000
echo [INFO] Drücken Sie Ctrl+C zum Beenden
echo.

REM Starte produktiven HTTP Proxy
python n8n-workflows\http-proxy.py

echo.
echo [INFO] Service beendet
pause