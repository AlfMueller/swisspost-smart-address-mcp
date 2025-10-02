#!/bin/bash
echo "🚀 Starte Swisspost MCP Server..."
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
echo "🚀 Starte MCP Server..."
echo
echo "📡 MCP Server läuft auf STDIO"
echo "🛑 Drücken Sie Ctrl+C zum Beenden"
echo

$PYTHON_CMD smart-address-agent.py
