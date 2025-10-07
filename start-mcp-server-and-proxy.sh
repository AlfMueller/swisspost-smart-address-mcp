#!/bin/bash
echo "🚀 Starte Swisspost MCP Server mit HTTP Proxy..."
echo

# Prüfe ob Python installiert ist
if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        echo "❌ Python ist nicht installiert oder nicht im PATH"
        exit 1
    else
        PYTHON_CMD="python"
    fi
else
    PYTHON_CMD="python3"
fi

# Prüfe ob .env Datei existiert
if [ ! -f ".env" ]; then
    echo "❌ .env Datei nicht gefunden"
    echo
    echo "💡 Erstellen Sie die .env Datei:"
    echo "   cp config.env .env"
    echo "   Dann .env bearbeiten und echte Credentials eintragen"
    echo
    exit 1
fi

# Prüfe ob smart-address-agent.py existiert
if [ ! -f "smart-address-agent.py" ]; then
    echo "❌ smart-address-agent.py nicht gefunden"
    echo "Stellen Sie sicher, dass Sie im Projektverzeichnis sind"
    exit 1
fi

# Prüfe ob aiohttp installiert ist
$PYTHON_CMD -c "import aiohttp" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ aiohttp nicht installiert"
    echo
    echo "💡 Installieren Sie aiohttp:"
    echo "   pip install aiohttp"
    echo
    exit 1
fi

echo "📡 Teste Swisspost API Credentials..."
$PYTHON_CMD test-credentials.py

if [ $? -ne 0 ]; then
    echo
    echo "❌ Credentials-Test fehlgeschlagen"
    echo "Bitte überprüfen Sie Ihre .env Datei"
    exit 1
fi

echo
echo "✅ Credentials-Test erfolgreich"
echo
echo "🚀 Starte MCP Server mit HTTP Proxy..."
echo
echo "📡 MCP Server läuft auf STDIO"
echo "🌐 HTTP Proxy läuft auf http://localhost:3000"
echo "🛑 Drücken Sie Ctrl+C zum Beenden"
echo

# Starte beide Prozesse im Hintergrund
$PYTHON_CMD smart-address-agent.py &
MCP_PID=$!

# Warte kurz
sleep 2

# Starte HTTP Proxy
$PYTHON_CMD n8n-workflows/mcp-http-proxy.py &
PROXY_PID=$!

echo
echo "✅ Beide Services gestartet"
echo "📡 MCP Server (PID: $MCP_PID): STDIO"
echo "🌐 HTTP Proxy (PID: $PROXY_PID): http://localhost:3000"
echo
echo "🛑 Drücken Sie Ctrl+C zum Beenden..."

# Warte auf Interrupt
trap 'echo; echo "🛑 Beende Services..."; kill $MCP_PID $PROXY_PID 2>/dev/null; echo "✅ Services beendet"; exit 0' INT

# Warte auf Prozesse
wait
