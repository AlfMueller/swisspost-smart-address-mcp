# Swisspost Address Validation n8n Workflow

Produktiver n8n Workflow für intelligente Adressvalidierung mit Swisspost API Integration.

## 🎯 Features

### 🧠 Intelligente Adressanalyse
- **Automatische City-Correction** - Korrigiert falsch geschriebene Ortsnamen (z.B. "Musterstadt" → "Musterstadt-Korrekt")
- **PLZ/Ort-Vertauschung** - Erkennt und korrigiert vertauschte PLZ und Ortsnamen
- **Hausnummer-Erkennung** - Trennt automatisch Hausnummern von Straßennamen
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

### 🔧 Produktive Integration
- **REST API Webhook** - Einfache Integration in bestehende Systeme
- **Dauerhaft aktiv** - Läuft kontinuierlich ohne manuelle Aktivierung
- **Robuste Fehlerbehandlung** - Graceful Degradation bei API-Fehlern
- **Strukturiertes Logging** - Detaillierte Protokollierung für Monitoring

## 📋 Workflow Übersicht

### **Swisspost Workflow** (`swisspost-workflow.json`)
- Intelligente Adressvalidierung mit Swisspost API
- Webhook-basierte API
- Automatische Fehlerkorrektur
- Qualitätsbewertung und Empfehlungen
- Strukturiertes Logging und Monitoring
- Produktionsreif

## 🚀 Installation

### Schritt 1: Mit Start-Skript (empfohlen)
```bash
# MCP Server + HTTP Proxy starten (mit Credentials-Test)
cd /path/to/your/swissspost_mcp
start-mcp-server-and-proxy.bat    # Windows
./start-mcp-server-and-proxy.sh   # Linux/macOS
```

### Schritt 2: Manuell
```bash
# HTTP Proxy starten
cd /path/to/your/swissspost_mcp/n8n-workflows
python http-proxy.py
```

Der Proxy läuft auf `http://localhost:3000` und konvertiert HTTP Requests zu MCP STDIO Calls.

### Schritt 3: n8n Workflow importieren
```bash
# In n8n Editor:
# 1. Menu (☰) → Import workflow
# 2. swisspost-workflow.json auswählen
# 3. Workflow aktivieren
```

### Schritt 4: Webhook URL konfigurieren
- **Swisspost Workflow**: `http://your-n8n-instance/webhook/swisspost-validate`

## 📡 API Verwendung

### Request Format
```json
POST /webhook/swisspost-validate
Content-Type: application/json

{
  "firstname": "Max",
  "lastname": "Mustermann", 
  "company": "Test AG",
  "street": "Bahnhofstrasse 1",
  "city": "Zürich",
  "postcode": "8001"
}
```

### Response Format
```json
{
  "success": true,
  "status": "valid",
  "quality": {
    "level": "CERTIFIED",
    "score": 100,
    "description": "Zertifiziert",
    "color": "green",
    "levelName": "excellent"
  },
  "isValid": true,
  "input": {
    "original": {...},
    "processed": {...}
  },
  "corrected": {
    "street_name": "Bahnhofstrasse",
    "house_number": "1",
    "city": "Zürich",
    "postcode": "8001",
    "street_full": "Bahnhofstrasse 1"
  },
  "corrections": [],
  "hasCorrections": false,
  "recommendations": [
    "Adresse ist korrekt und validiert",
    "Keine weiteren Aktionen erforderlich"
  ],
  "metadata": {
    "timestamp": "2025-01-27T10:00:00.000Z",
    "requestId": "2025-01-27T10:00:00.000Z",
    "processingTime": 1250,
    "version": "1.0.0"
  }
}
```

## 🧪 Testing

### Automatische Tests
```bash
# Test Script ausführen
node test-swisspost-workflow.js
```

**Voraussetzungen:**
1. MCP HTTP Proxy läuft: `python mcp-http-proxy.py`
2. n8n Workflow importiert und aktiviert
3. Test Script ausführen

### Manuelle Tests
```bash
# cURL Beispiel
curl -X POST http://localhost:5678/webhook/swisspost-validate \
  -H "Content-Type: application/json" \
  -d '{
    "firstname": "Max",
    "lastname": "Mustermann",
    "street": "Bahnhofstrasse 1",
    "city": "Zürich", 
    "postcode": "8001"
  }'
```

## 🔧 Konfiguration

### Umgebungsvariablen
```bash
# n8n Environment Variables
N8N_BASE_URL=http://localhost:5678
MCP_PROXY_URL=http://localhost:3000
```

### Webhook Konfiguration
- **Path**: `/webhook/swisspost-validate`
- **Method**: `POST`
- **Authentication**: Keine (intern)
- **Rate Limiting**: 1000 requests/hour

## 📊 Monitoring

### Logs
```javascript
// Strukturierte Logs in n8n Console
{
  "timestamp": "2025-01-27T10:00:00.000Z",
  "level": "INFO",
  "service": "swisspost-address-validation",
  "requestId": "2025-01-27T10:00:00.000Z",
  "status": "valid",
  "quality": "CERTIFIED",
  "score": 100,
  "hasCorrections": false,
  "processingTime": 1250
}
```

### Metriken
- **Success Rate**: % erfolgreicher Validierungen
- **Average Processing Time**: Durchschnittliche Verarbeitungszeit
- **Quality Distribution**: Verteilung der Qualitätsstufen
- **Correction Rate**: % Adressen mit Korrekturen

## 🛠 Troubleshooting

### Häufige Probleme

#### 1. MCP Proxy nicht erreichbar
```
Error: MCP Proxy Fehler
```
**Lösung**: MCP HTTP Proxy starten und Port 3000 prüfen

#### 2. Ungültige Eingabedaten
```
Error: Fehlende Felder: street, city, postcode
```
**Lösung**: Alle Pflichtfelder ausfüllen

#### 3. PLZ Format Fehler
```
Error: PLZ muss 4 Ziffern haben
```
**Lösung**: Schweizer PLZ Format verwenden (4 Ziffern)

#### 4. Timeout Fehler
```
Error: Request timeout
```
**Lösung**: Timeout in n8n HTTP Request Node erhöhen

### Debug Schritte
1. **n8n Logs prüfen**: Console Output in n8n
2. **MCP Proxy Status**: `python mcp-http-proxy.py` testen
3. **Webhook URL**: Korrekte URL in n8n prüfen
4. **Credentials**: Swisspost API Credentials validieren

## 🔄 Workflow Anpassungen

### Custom Validierung hinzufügen
```javascript
// In "Validate Input" Node
if (normalizedData.city.toLowerCase().includes('test')) {
  throw new Error('Test-Adressen nicht erlaubt');
}
```

### Zusätzliche Felder
```javascript
// In "Call MCP Proxy" Node
{
  "name": "custom_field",
  "value": "={{ $json.custom_field }}"
}
```

### Response Format anpassen
```javascript
// In "Process Response" Node
result.customField = 'Custom Value';
result.timestamp = new Date().toISOString();
```

## 📈 Performance

### Optimierungen
- **Caching**: MCP Proxy Response cachen
- **Batch Processing**: Mehrere Adressen gleichzeitig
- **Connection Pooling**: HTTP Verbindungen wiederverwenden
- **Retry Logic**: Automatische Wiederholung bei Fehlern

### Limits
- **Rate Limit**: 1000 requests/hour
- **Timeout**: 30 Sekunden pro Request
- **Payload Size**: Max 1MB
- **Concurrent Requests**: 10 parallel

## 🔐 Sicherheit

### Best Practices
- **Input Validation**: Alle Eingaben validieren
- **Error Handling**: Keine sensiblen Daten in Fehlermeldungen
- **Logging**: Keine Credentials in Logs
- **Rate Limiting**: Schutz vor Missbrauch

### Sensitive Data
- **Credentials**: Nur in n8n Credentials speichern
- **Logs**: Keine persönlichen Daten loggen
- **Errors**: Generische Fehlermeldungen

## 📚 Weitere Ressourcen

- [Swisspost API Dokumentation](https://developer.post.ch/)
- [n8n Dokumentation](https://docs.n8n.io/)
- [MCP Server Repository](https://github.com/AlfMueller/swisspost-smart-address-mcp)
- [n8n Community](https://community.n8n.io/)

## 🤝 Support

Bei Problemen oder Fragen:
1. **n8n Logs** prüfen
2. **MCP Proxy** testen
3. **GitHub Issues** erstellen
4. **Community Forum** nutzen

## 🧪 Beta Testing & Feedback

### **Aktuelle Beta-Features:**
- ✅ Grundlegende Adressvalidierung funktioniert
- ✅ Webhook-Integration implementiert
- ✅ Error-Handling vorhanden
- 🚧 Erweiterte Monitoring-Features
- 🚧 Performance-Optimierungen
- 🚧 Zusätzliche Validierungsregeln

### **Bekannte Einschränkungen:**
- ⚠️ Rate Limiting noch nicht vollständig implementiert
- ⚠️ Erweiterte Metriken in Entwicklung
- ⚠️ Batch-Processing noch nicht verfügbar
- ⚠️ Erweiterte Error-Recovery in Arbeit

### **Feedback geben:**
1. **Issues melden**: [GitHub Issues](https://github.com/AlfMueller/swisspost-smart-address-mcp/issues)
2. **Feature Requests**: Neue Funktionen vorschlagen
3. **Bug Reports**: Probleme detailliert beschreiben
4. **Verbesserungsvorschläge**: Workflow-Optimierungen

### **Beta-Tester werden:**
- Testen Sie den Workflow in Ihrer Umgebung
- Melden Sie Bugs und Verbesserungen
- Teilen Sie Ihre Erfahrungen mit der Community
- Helfen Sie bei der Weiterentwicklung

---

**🎯 Dieser Workflow bietet eine vollständige Lösung für intelligente Adressvalidierung in n8n mit Swisspost API Integration!**

> **⚠️ BETA VERSION** - Bitte testen Sie gründlich und geben Sie Feedback für Verbesserungen.