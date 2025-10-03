# 🇨🇭 Swisspost Smart Address MCP Server

Ein intelligenter Adress-Validator mit Swisspost API Integration, der als MCP (Model Context Protocol) Server fungiert. Der Agent erkennt und korrigiert automatisch häufige Adressfehler und nutzt die Swisspost Autocomplete-APIs für maximale Genauigkeit.

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![MCP](https://img.shields.io/badge/MCP-1.15+-green.svg)](https://modelcontextprotocol.io)
[![Swisspost](https://img.shields.io/badge/Swisspost-API-orange.svg)](https://developer.post.ch)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Keywords:** `swisspost` `mcp` `address-validation` `claude-desktop` `n8n` `switzerland` `postal-api` `address-correction` `automation`

## 🚀 Features

### 🧠 Intelligente Adressanalyse
- **PLZ/Ort-Vertauschung** - Erkennt automatisch wenn PLZ und Ort vertauscht wurden
- **Hausnummer-Erkennung** - Trennt automatisch Hausnummern von Straßennamen
- **Stadtname-Korrektur** - Korrigiert falsch geschriebene Ortsnamen (z.B. "Musterstadt" → "Musterstadt-Korrekt")
- **Adress-Normalisierung** - Standardisiert Adressformate für bessere Validierung

### 🔗 Swisspost API Integration
- **ZIP-Autocomplete** - Findet korrekte Ortsnamen basierend auf Postleitzahl
- **Street-Autocomplete** - Korrigiert Straßennamen und Schreibweisen
- **House-Autocomplete** - Validiert und korrigiert Hausnummern
- **Vollständige Adressvalidierung** - Überprüft komplette Adressen mit Personendaten

### ⚡ Automatische Korrekturen
- **Echtzeit-Korrektur** - Korrigiert Fehler während der Validierung
- **Fallback-Mechanismen** - Bekannte Korrekturen für häufige Fehler
- **Qualitätsbewertung** - Score von 0-100 basierend auf Swisspost-Qualitätsstufen
- **Detaillierte Rückmeldung** - Zeigt alle durchgeführten Korrekturen an

### 🔧 Integration & Automatisierung
- **MCP Server** - Nahtlose Integration in Claude Desktop und andere MCP-fähige Tools
- **n8n Workflow** - Produktiver Webhook für Automatisierung
- **HTTP Proxy** - Brücke zwischen n8n und MCP Server
- **REST API** - Einfache Integration in bestehende Systeme

### 🔐 Sicherheit & Best Practices
- **Umgebungsvariablen** - Credentials nur in .env Datei, keine hardcodierten Werte
- **OAuth2 Authentifizierung** - Sichere API-Zugriffe mit Token-Management
- **Fehlerbehandlung** - Robuste Behandlung von API-Fehlern und Timeouts
- **Logging** - Detaillierte Protokollierung für Debugging und Monitoring

## 📋 Voraussetzungen

- Python 3.8+
- Swisspost API Credentials
- MCP Inspector (optional, für Testing)

## 🛠️ Installation

### 1. Repository klonen/herunterladen
```bash
git clone <repository-url>
cd swissspost_mcp
```

### 2. Python Dependencies installieren

**Option A: Mit requirements.txt (empfohlen)**
```bash
pip install -r requirements.txt
```

**Option B: Einzeln installieren**
```bash
pip install httpx mcp python-dotenv
```

**Hinweis:** Falls Sie PlatformIO installiert haben, können Dependency-Konflikte auftreten. Diese beeinträchtigen die MCP-Funktionalität nicht.

### 3. Swisspost API Credentials besorgen
1. Registrieren Sie sich bei [Swisspost Developer Portal](https://developer.post.ch/)
2. Erstellen Sie eine neue App
3. Notieren Sie sich `Client ID` und `Client Secret`

### 4. Umgebungsvariablen konfigurieren

**Option A: .env Datei (empfohlen)**
```bash
# .env Datei erstellen
# Linux/macOS:
cp config.env .env

# Windows:
copy config.env .env

# .env bearbeiten und echte Credentials eintragen
SWISSPOST_CLIENT_ID=ihre_echte_client_id
SWISSPOST_CLIENT_SECRET=ihr_echtes_secret
# Verfügbare Scopes siehe Abschnitt "API Scopes" unten
# WICHTIG: Für City Correction wird auch DCAPI_ADDRESS_AUTOCOMPLETE benötigt!
SWISSPOST_SCOPE=DCAPI_ADDRESS_VALIDATE DCAPI_ADDRESS_AUTOCOMPLETE DCAPI_ADDRESS_AUTOCOMPLETE
```

**Hinweis:** Die .env Datei wird automatisch geladen (python-dotenv). Keine manuellen Umgebungsvariablen nötig!

**Option B: Direkt in PowerShell setzen**
```powershell
$env:SWISSPOST_CLIENT_ID="ihre_client_id"
$env:SWISSPOST_CLIENT_SECRET="ihr_secret"
$env:SWISSPOST_SCOPE="DCAPI_ADDRESS_VALIDATE DCAPI_ADDRESS_AUTOCOMPLETE"
```

**Option C: config.env verwenden**
```bash
# config.env Datei bearbeiten
notepad config.env

# Umgebungsvariablen laden (Windows PowerShell)
Get-Content config.env | ForEach-Object { 
    if($_ -match "^([^#][^=]+)=(.*)") { 
        [Environment]::SetEnvironmentVariable($matches[1], $matches[2], "Process") 
    } 
}
```

### 5. MCP Inspector installieren (optional)
```bash
npm install -g @modelcontextprotocol/inspector
```

## 🧪 Testing

### Automatische Tests ausführen
```bash
python mcp-test-script.py
```

Das Test-Skript prüft automatisch 5 Problem-Szenarien:

1. ✅ **PLZ und Ort vertauscht** - `"8005"` im Stadtfeld, `"Zürich"` im PLZ-Feld
2. ✅ **Hausnummer am Anfang** - `"94 Pfingstweidstrasse"` statt `"Pfingstweidstrasse 94"`
3. ✅ **Abkürzungen** - `"Hauptstr."` statt `"Hauptstrasse"`
4. ✅ **Verklebte Hausnummer** - `"Bahnhofstrasse43"` ohne Leerzeichen
5. ✅ **Korrekte Adresse** - Sollte ohne Änderungen durchgehen

### MCP Inspector verwenden
```bash
# MCP Inspector starten
mcp-inspector

# Server starten (in separatem Terminal)
python smart-address-agent.py
```

### Server direkt testen
```bash
# Server im MCP-Modus starten
python smart-address-agent.py

# In anderem Terminal: MCP Inspector verbinden
mcp-inspector
```

## 📖 Verwendung

### Als MCP Server

**WICHTIG: Der MCP Server muss immer zuerst gestartet werden!**

#### **Schritt 1: MCP Server starten**
```bash
# Im Projektverzeichnis
python .\smart-address-agent.py
```
Der Server läuft dann im Hintergrund und wartet auf Verbindungen.

#### **Schritt 2: Client verbinden**

**Option A: Claude Desktop**
1. **Konfigurationsdatei erstellen** `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "swisspost-address": {
      "command": "python",
      "args": ["/path/to/your/swissspost_mcp/smart-address-agent.py"],
      "cwd": "/path/to/your/swissspost_mcp"
    }
  }
}
```
2. **Datei speichern** in Claude Desktop Konfigurationsordner:
   - **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
   - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Linux**: `~/.config/claude/claude_desktop_config.json`
3. **Pfad anpassen** in der Konfiguration (args-Array) auf Ihren tatsächlichen Pfad
4. **.env Datei erstellen** im Projektverzeichnis mit Ihren echten Credentials
5. **Claude Desktop starten** - Verbindet sich automatisch und lädt .env
6. **Verwenden**: "Validiere diese Adresse: Pfingstweidstrasse 94, 8005 Zürich"

**Option B: MCP Inspector (für Tests)**
```bash
# Terminal 1: Server starten
python .\smart-address-agent.py

# Terminal 2: Inspector starten
mcp-inspector
```

**Option C: n8n Workflow (produktiv)**
1. **MCP Server + HTTP Proxy starten**:
   ```bash
   # Windows:
   start-mcp-server-and-proxy.bat
   
   # Linux/macOS:
   chmod +x start-mcp-server-and-proxy.sh
   ./start-mcp-server-and-proxy.sh
   ```

2. **n8n Workflow importieren**:
   - Workflow: `n8n-workflows/swisspost-workflow.json`
   - Webhook URL: `https://your-n8n-instance.com/webhook/swisspost-validate`

3. **Features des n8n Workflows**:
   - ✅ **Automatische City-Correction** (z.B. "Musterstadt" → "Musterstadt-Korrekt")
   - ✅ **Vollständige Adressvalidierung** mit Personendaten
   - ✅ **Qualitätsbewertung** (Score 0-100)
   - ✅ **Detaillierte Korrekturen** mit Rückmeldung
   - ✅ **REST API** für einfache Integration
   - ✅ **Produktiver Webhook** der dauerhaft läuft

## 🔌 MCP Kommunikation

**WICHTIG: MCP nutzt KEINEN Port!**

### **Kommunikationsart:**
- **STDIO** (Standard Input/Output)
- **JSON-RPC** über stdin/stdout
- **Prozess-zu-Prozess** Kommunikation

### **Warum kein Port?**
- **Sicherer** - keine Netzwerk-Exposition
- **Einfacher** - keine Port-Konflikte
- **Standard** - MCP-Protokoll nutzt STDIO

### **Verbindungsarten:**
- **Claude Desktop**: Startet Server als Subprozess
- **n8n**: Verbindet sich über MCP-Connector
- **MCP Inspector**: Testet über STDIO-Verbindung

## ⚠️ WICHTIG: MCP Server muss auf dem Client laufen

### **Warum lokal?**
- **STDIO-Kommunikation** erfordert lokale Prozesse
- **Keine Netzwerk-Verbindung** möglich
- **Sicherheit** - keine externe Server nötig

### **Deployment-Optionen:**

#### **Option 1: Lokal auf jedem Client**
```bash
# Auf jedem Rechner installieren
git clone <repository>
cd swissspost_mcp
pip install -r requirements.txt
python smart-address-agent.py
```

#### **Option 2: Docker Container (lokal)**
```dockerfile
# Dockerfile erstellen
FROM python:3.12
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
CMD ["python", "smart-address-agent.py"]
```

#### **Option 3: Windows Service**
```bash
# Als Windows Service installieren
sc create SwisspostMCP binPath="python C:\path\to\smart-address-agent.py"
```

### **Für n8n:**
- **n8n Server** muss auf demselben Rechner laufen
- **MCP Server** muss lokal verfügbar sein
- **Keine Remote-Verbindung** möglich

### Direkt als Python Modul

```python
from smart_address_agent import SmartAddressAgent

agent = SmartAddressAgent()
result = await agent.validate_smart({
    'street': 'Pfingstweidstrasse 94',
    'city': 'Zürich',
    'postcode': '8005'
})
print(result)
```

## 🔧 API Referenz

### Tool: `validate_address_smart`

**Eingabe:**
- `street` (required): Straße mit oder ohne Hausnummer
- `city` (required): Ort
- `postcode` (required): Postleitzahl
- `firstname` (optional): Vorname
- `lastname` (optional): Nachname
- `company` (optional): Firma

**Ausgabe:**
```json
{
  "status": "success|failed",
  "quality": "CERTIFIED|VERIFIED|USABLE|UNUSABLE",
  "score": 0-100,
  "corrections": [
    {
      "type": "swap_plz_city|city_corrected|street_corrected|house_number_corrected",
      "message": "Beschreibung der Korrektur",
      "old": "Ursprünglicher Wert",
      "new": "Korrigierter Wert"
    }
  ],
  "corrected": {
    "street_name": "Korrigierter Straßenname",
    "house_number": "Korrigierte Hausnummer",
    "city": "Korrigierter Ort",
    "postcode": "PLZ",
    "street_full": "Vollständige Straße"
  }
}
```

## 🏗️ Architektur

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Input         │    │  Address Analyzer│    │  Swisspost APIs │
│   Adresse       │───▶│  - PLZ/Ort Swap  │───▶│  - ZIP Lookup   │
│                 │    │  - Street Split  │    │  - Street Lookup│
└─────────────────┘    │  - Normalization │    │  - House Lookup │
                       └──────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌──────────────────┐    ┌─────────────────┐
                       │  Corrections     │    │  Final          │
                       │  - Auto-fix      │    │  Validation     │
                       │  - Quality Score │    │  - Swisspost    │
                       └──────────────────┘    └─────────────────┘
```

## 📁 Projektstruktur

```
swissspost_mcp/
├── smart-address-agent.py    # Haupt-MCP-Server
├── mcp-test-script.py        # Automatische Tests
├── config.env               # Umgebungsvariablen Template
├── .env                     # Ihre echten Credentials (wird automatisch geladen)
├── start-mcp-server.bat     # Start-Skript MCP Server (Windows)
├── start-mcp-server.sh      # Start-Skript MCP Server (Linux/macOS)
├── start-mcp-server-and-proxy.bat  # Start-Skript MCP + Proxy (Windows)
├── start-mcp-server-and-proxy.sh   # Start-Skript MCP + Proxy (Linux/macOS)
├── n8n-workflows/           # n8n Workflow für Adressvalidierung
│   ├── swisspost-workflow.json      # n8n Workflow
│   ├── http-proxy.py                # HTTP-Proxy für MCP
│   ├── test-swisspost-workflow.js   # Test Script
│   ├── package.json
│   └── README.md
├── README.md                # Diese Dokumentation
└── requirements.txt         # Python Dependencies (optional)
```

## 🔧 Verfügbare Tools

### `validate_address_smart`
Das einzige verfügbare Tool für die intelligente Adressvalidierung.

**Eingabeparameter:**
- `street` (required): Straße mit oder ohne Hausnummer
- `city` (required): Ort  
- `postcode` (required): Postleitzahl
- `firstname` (optional): Vorname
- `lastname` (optional): Nachname
- `company` (optional): Firma

**Ausgabeformat:**
- `status`: "success" oder "failed"
- `quality`: Swisspost Qualitätsbewertung
- `score`: Numerischer Score (0-100)
- `corrections`: Array aller vorgenommenen Korrekturen
- `corrected`: Finale, validierte Adresse
- `validation`: Vollständige Swisspost API Antwort

## 🐛 Troubleshooting

### Häufige Probleme

**1. "Credentials müssen gesetzt sein"**
```bash
# Prüfen Sie Ihre Umgebungsvariablen
echo $env:SWISSPOST_CLIENT_ID
echo $env:SWISSPOST_CLIENT_SECRET
```

**2. "Kann server.py nicht importieren"**
```bash
# Stellen Sie sicher, dass Sie im richtigen Verzeichnis sind
cd /path/to/your/swissspost_mcp
```

**3. "OAuth Fehler"**
- Überprüfen Sie Ihre API Credentials
- Stellen Sie sicher, dass Ihr API-Account aktiv ist
- Prüfen Sie die Scope-Berechtigung

**4. "Timeout Fehler"**
- Überprüfen Sie Ihre Internetverbindung
- Swisspost API könnte temporär nicht verfügbar sein

**5. "Import mcp.server could not be resolved"**
```bash
# MCP Paket installieren
pip install mcp
```

**6. "Kann server.py nicht importieren" (Test-Skript)**
```bash
# Stellen Sie sicher, dass smart-address-agent.py im gleichen Verzeichnis ist
# Das Test-Skript sucht nach 'server.py', aber die Datei heißt 'smart-address-agent.py'
```

**7. ".env Datei wird nicht geladen"**
```bash
# Stellen Sie sicher, dass python-dotenv installiert ist
pip install python-dotenv

# .env Datei im gleichen Verzeichnis wie smart-address-agent.py
# Format: SWISSPOST_CLIENT_ID=ihre_client_id
```

### Debug-Modus

```python
# In smart-address-agent.py Debug-Ausgaben aktivieren
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📝 Lizenz

MIT License - siehe LICENSE Datei für Details.

## 🤝 Contributing

1. Fork das Repository
2. Erstellen Sie einen Feature Branch
3. Committen Sie Ihre Änderungen
4. Pushen Sie zum Branch
5. Erstellen Sie einen Pull Request

## 📚 API Dokumentation

### **n8n Webhook API**

**Endpoint:** `https://your-n8n-instance.com/webhook/swisspost-validate`
**Method:** `POST`
**Content-Type:** `application/json`

#### **Request Format:**
```json
{
  "company": "Firmenname GmbH",
  "firstname": "Max",
  "lastname": "Mustermann",
  "street": "Bahnhofstrasse 1",
  "city": "Zürich",
  "postcode": "8001"
}
```

#### **Response Format:**
```json
{
  "success": true,
  "data": {
    "status": "success",
    "quality": "CERTIFIED",
    "score": 100,
    "corrections": [
      {
        "type": "city_corrected",
        "message": "Ortsname korrigiert via Fallback-Lookup",
        "old": "Musterstadt",
        "new": "Musterstadt-Korrekt"
      }
    ],
    "input": {
      "street": "Musterstrasse 123",
      "city": "Musterstadt",
      "postcode": "8001"
    },
    "corrected": {
      "street_name": "Musterstrasse",
      "house_number": "123",
      "city": "Musterstadt-Korrekt",
      "postcode": "8001",
      "street_full": "Musterstrasse 123"
    },
    "validation": {
      "quality": "DOMICILE_CERTIFIED",
      "expires": "20251003T002909+0200",
      "address": {
        "type": "DOMICILE",
        "addressee": {
          "firstName": "Max",
          "lastName": "Mustermann",
          "companyName": "Beispiel GmbH"
        },
        "geographicLocation": {
          "house": {
            "street": "Musterstrasse",
            "houseNumber": "123",
            "houseKey": "12345678"
          },
          "zip": {
            "zip": "8001",
            "city": "Musterstadt-Korrekt"
          }
        },
        "id": "dba6e3d2-904d-4676-978b-0f86558db187"
      }
    },
    "has_corrections": true
  },
  "timestamp": 1759440549.6417124
}
```

#### **Qualitätsstufen:**
- `CERTIFIED` / `DOMICILE_CERTIFIED` - Höchste Qualität (Score: 100)
- `USABLE` - Gute Qualität (Score: 80-99)
- `UNUSABLE` - Niedrige Qualität (Score: 0-79)

#### **Korrektur-Typen:**
- `city_corrected` - Ortsname korrigiert
- `street_corrected` - Straßenname korrigiert
- `house_number_corrected` - Hausnummer korrigiert
- `swap_plz_city` - PLZ und Ort waren vertauscht

### **cURL Beispiel:**
```bash
curl -X POST https://your-n8n-instance.com/webhook/swisspost-validate \
  -H "Content-Type: application/json" \
  -d '{
    "company": "Beispiel GmbH",
    "firstname": "Max",
    "lastname": "Mustermann",
    "street": "Musterstrasse 123",
    "city": "Musterstadt",
    "postcode": "8001"
  }'
```

## 📞 Support

Bei Problemen oder Fragen:
- Erstellen Sie ein Issue im Repository
- Überprüfen Sie die Swisspost API Dokumentation
- Schauen Sie in die Troubleshooting Sektion

---

## 🚀 Quick Start

### **Option A: Mit Start-Skripten (empfohlen)**

**Nur MCP Server (für Claude Desktop):**
```bash
# Windows:
start-mcp-server.bat

# Linux/macOS:
chmod +x start-mcp-server.sh
./start-mcp-server.sh
```

**MCP Server + HTTP Proxy (für n8n):**
```bash
# Windows:
start-mcp-server-and-proxy.bat

# Linux/macOS:
chmod +x start-mcp-server-and-proxy.sh
./start-mcp-server-and-proxy.sh
```

### **Option B: Manuell**

```bash
# 1. Dependencies installieren
pip install -r requirements.txt

# 2. .env Datei erstellen und Credentials eintragen
# Linux/macOS:
cp config.env .env

# Windows:
copy config.env .env

# .env bearbeiten mit echten Credentials

⚠️ **SICHERHEIT**: Die `.env` Datei ist in `.gitignore` und wird nicht committet!

# 3. Testen
python mcp-test-script.py

# 4. MCP Server starten (WICHTIG: Immer zuerst!)
python smart-address-agent.py

# 5. Client verbinden (Claude Desktop, n8n, oder MCP Inspector)
```

## 🔄 Workflow für verschiedene Clients

### **n8n Workflow**
Für n8n Integration siehe den separaten `n8n-workflows/` Ordner:

```bash
cd n8n-workflows
npm test  # Teste den n8n Workflow
```

**Verfügbarer n8n Workflow:**
- **Swisspost Workflow**: Intelligente Adressvalidierung mit Monitoring
- **HTTP Proxy**: HTTP-Proxy für MCP-Integration
- **Test Script**: Automatische Tests für alle Szenarien

Siehe `n8n-workflows/README.md` für detaillierte Anleitung.

### **Claude Desktop**
1. **Konfiguration erstellen**: `claude_desktop_config.json`
2. **Pfad anpassen** und **Credentials eintragen**
3. **Claude Desktop starten** (startet Server automatisch)
4. **Verwenden**: "Validiere diese Adresse: ..."

#### **Detaillierte Claude Desktop Anleitung:**

**Schritt 1: Konfigurationsdatei erstellen**
```bash
# Beispiel-Konfiguration kopieren
cp claude_desktop_config.json %APPDATA%\Claude\claude_desktop_config.json
```

**Schritt 2: Konfiguration anpassen**
```json
{
  "mcpServers": {
    "swisspost-address": {
      "command": "python",
      "args": ["/path/to/your/swissspost_mcp/smart-address-agent.py"],
      "cwd": "/path/to/your/swissspost_mcp"
    }
  }
}
```

**Wichtige Änderungen:**
- ✅ **Keine hardcodierten Credentials** mehr in der Konfiguration
- ✅ **`cwd` Parameter** hinzugefügt für korrekte .env Ladung
- ✅ **Sicherheit verbessert** - Credentials nur in .env Datei

**Pfad anpassen:**
- **Windows:** `C:\\swissspost_mcp\\smart-address-agent.py`
- **macOS:** `/Users/username/swissspost_mcp/smart-address-agent.py`
- **Linux:** `/home/username/swissspost_mcp/smart-address-agent.py`

**Schritt 3: .env Datei erstellen**
```bash
# Im Projektverzeichnis .env Datei erstellen
# Linux/macOS:
cp config.env .env

# Windows:
copy config.env .env

# Dann .env bearbeiten und echte Credentials eintragen:
SWISSPOST_CLIENT_ID=ihre_echte_client_id
SWISSPOST_CLIENT_SECRET=ihr_echtes_secret
SWISSPOST_SCOPE=DCAPI_ADDRESS_VALIDATE DCAPI_ADDRESS_AUTOCOMPLETE
```

**Schritt 4: Claude Desktop starten**
- Claude Desktop startet automatisch den MCP Server
- MCP lädt automatisch die .env Datei
- Kein manueller Server-Start nötig

### **n8n**
1. **Server starten**: `python smart-address-agent.py`
2. **n8n MCP-Connector** konfigurieren
3. **Workflow** mit Adressvalidierung erstellen

### **MCP Inspector (Tests)**
1. **Terminal 1**: `python smart-address-agent.py`
2. **Terminal 2**: `mcp-inspector`
3. **Verbindung** herstellen und testen

## 📊 Qualitätsbewertungen

| Quality | Score | Beschreibung |
|---------|-------|--------------|
| `DOMICILE_CERTIFIED` | 100 | Vollständig zertifiziert |
| `CERTIFIED` | 100 | Zertifiziert |
| `VERIFIED` | 90 | Verifiziert |
| `USABLE` | 50 | Verwendbar |
| `COMPROMISED` | 60 | Kompromittiert |
| `UNUSABLE` | 0 | Nicht verwendbar |

## 🔍 Korrekturtypen

- `swap_plz_city`: PLZ und Ort waren vertauscht
- `city_corrected`: Ortsname via ZIP-Lookup korrigiert
- `street_corrected`: Straßenname via Street-Lookup korrigiert  
- `house_number_corrected`: Hausnummer via House-Lookup korrigiert

## 🔐 Sicherheit & Best Practices

### **Sichere Konfiguration (NEU!)**

**✅ Empfohlene Konfiguration:**
```json
{
  "mcpServers": {
    "swisspost-address": {
      "command": "python",
      "args": ["/path/to/your/swissspost_mcp/smart-address-agent.py"],
      "cwd": "/path/to/your/swissspost_mcp"
    }
  }
}
```

**❌ Vermeiden Sie:**
```json
{
  "mcpServers": {
    "swisspost-address": {
      "command": "python",
      "args": ["/path/to/your/swissspost_mcp/smart-address-agent.py"],
      "env": {
        "SWISSPOST_CLIENT_ID": "hardcoded_credentials",  // ❌ Sicherheitsrisiko!
        "SWISSPOST_CLIENT_SECRET": "hardcoded_secret"    // ❌ Sicherheitsrisiko!
      }
    }
  }
}
```

### **Warum .env verwenden?**

1. **Sicherheit** - Credentials werden nicht in Git committet
2. **Flexibilität** - Einfacher Wechsel zwischen Umgebungen
3. **Wartbarkeit** - Keine doppelten Credential-Definitionen
4. **Best Practice** - Standard für sensible Konfigurationsdaten

### **.env Datei Setup**

```bash
# .env Datei im Projektverzeichnis erstellen
SWISSPOST_CLIENT_ID=ihre_echte_client_id
SWISSPOST_CLIENT_SECRET=ihr_echtes_secret
SWISSPOST_SCOPE=DCAPI_ADDRESS_VALIDATE DCAPI_ADDRESS_AUTOCOMPLETE
```

**Wichtig:** Die `.env` Datei ist in `.gitignore` und wird **NICHT** hochgeladen!

## 🔐 API Scopes

Die Swisspost Digital Commerce API bietet verschiedene Berechtigungsbereiche (Scopes):

### **Adress-Services**
- `DCAPI_ADDRESS_READ` - Lesen von Adressdaten
- `DCAPI_ADDRESS_VALIDATE` - Validierung von Adressen *(Standard für dieses Projekt)*
- `DCAPI_ADDRESS_AUTOCOMPLETE` - Autocomplete für Städte, Straßen und Hausnummern *(Für City Correction erforderlich)*

### **Versand-Services**  
- `DCAPI_SHIPPING` - Zugriff auf Versanddienste
- `DCAPI_TRACKING` - Sendungsverfolgung

### **Barcode-Services**
- `DCAPI_BARCODE` - Barcode-Generierung für Sendungen

### **Scope-Konfiguration**

**Für Adressvalidierung (empfohlen):**
```bash
SWISSPOST_SCOPE=DCAPI_ADDRESS_VALIDATE DCAPI_ADDRESS_AUTOCOMPLETE
```

**Für erweiterte Adressfunktionen:**
```bash
SWISSPOST_SCOPE=DCAPI_ADDRESS_READ DCAPI_ADDRESS_VALIDATE DCAPI_ADDRESS_AUTOCOMPLETE
```

**Für Versanddienste:**
```bash
SWISSPOST_SCOPE=DCAPI_SHIPPING DCAPI_TRACKING
```

**Hinweis:** Die genauen verfügbaren Scopes können je nach API-Version und Ihrem Account variieren. Konsultieren Sie die [Swisspost API Dokumentation](https://developer.post.ch/en/api-and-documentation) für die aktuellsten Informationen.

---

**Entwickelt mit ❤️ für die Schweizer Adressvalidierung**
