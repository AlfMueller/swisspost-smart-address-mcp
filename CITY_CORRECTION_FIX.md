# City Correction Fix für Swisspost MCP Server

## Problem
Die City Correction funktionierte nicht auf dem Server, obwohl sie in der `smart-address-agent.py` korrekt implementiert war.

## Ursache
1. **HTTP-Proxy Scope**: Im HTTP-Proxy (`n8n-workflows/http-proxy.py`) wurde der falsche OAuth-Scope verwendet:
   - **Falsch**: `scope = "api"`
   - **Richtig**: `scope = os.getenv("SWISSPOST_SCOPE", "DCAPI_ADDRESS_VALIDATE DCAPI_ADDRESS_AUTOCOMPLETE")`

2. **Environment Scope**: In der `.env` Datei fehlte der `DCAPI_ADDRESS_AUTOCOMPLETE` Scope:
   - **Falsch**: `SWISSPOST_SCOPE=DCAPI_ADDRESS_VALIDATE`
   - **Richtig**: `SWISSPOST_SCOPE=DCAPI_ADDRESS_VALIDATE DCAPI_ADDRESS_AUTOCOMPLETE`

## Behobene Dateien

### 1. `n8n-workflows/http-proxy.py`
- **Zeile 302**: Scope korrigiert von `"api"` zu korrektem Scope
- **Debug-Logging hinzugefügt** für bessere Fehlerdiagnose:
  - OAuth Token Status
  - ZIP API Response Details
  - City Correction Ergebnisse
  - Ähnlichkeits-Score Berechnungen

### 2. Neue Test-Skripte
- **`test-city-correction.py`**: Testet die City Correction über HTTP-Proxy
- **`test-zip-api.py`**: Testet die ZIP API direkt

## Verwendung

### 1. Server starten
```bash
cd F:\mcp\swisspost-smart-address-mcp
start-mcp-server-and-proxy.bat
```

### 2. City Correction testen
```bash
python test-city-correction.py
```

### 3. ZIP API direkt testen
```bash
python test-zip-api.py
```

## Erwartete Ausgabe
Nach dem Fix sollte die City Correction funktionieren:

```
INFO: Validation failed, trying city correction for 4586
DEBUG: Attempting city correction for ZIP 4586, city 'Kyburg'
DEBUG: ZIP API response for 4586: 1 cities found
DEBUG: Exact match found: Kyburg
DEBUG: City correction result: Kyburg
INFO: Found correct city name: Kyburg (was: Kyburg)
```

## Debug-Informationen
Der HTTP-Proxy gibt jetzt detaillierte Debug-Informationen aus:
- OAuth Token Status
- ZIP API Response Details
- City Matching Strategien
- Ähnlichkeits-Scores
- Korrektur-Ergebnisse

Diese helfen bei der Fehlerdiagnose, falls weitere Probleme auftreten.
