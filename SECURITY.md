# Sicherheitsrichtlinien

## ⚠️ WICHTIG: Credentials niemals committen!

### Was passiert ist:
- Die `.env` Datei mit echten Swisspost API Credentials wurde versehentlich ins GitHub Repository committet
- Dies stellt ein Sicherheitsrisiko dar, da die Credentials öffentlich sichtbar waren

### Was wurde getan:
1. ✅ `.env` Datei aus dem Repository entfernt
2. ✅ `.env` ist bereits in `.gitignore` enthalten
3. ✅ `config.env` als sichere Vorlage beibehalten

### Richtige Verwendung:

#### 1. Lokale .env erstellen:
```bash
# Kopiere die Vorlage
cp config.env .env

# Bearbeite .env mit deinen echten Credentials
# .env wird NICHT committet (steht in .gitignore)
```

#### 2. Echte Credentials eintragen:
```bash
# In .env (lokal, nicht committen!)
SWISSPOST_CLIENT_ID=deine_echte_client_id
SWISSPOST_CLIENT_SECRET=dein_echtes_secret
SWISSPOST_SCOPE=DCAPI_ADDRESS_VALIDATE
```

#### 3. Credentials rotieren:
Da die Credentials möglicherweise kompromittiert wurden:
1. **Neue Credentials bei Swisspost beantragen**
2. **Alte Credentials deaktivieren**
3. **Neue Credentials in .env eintragen**

### Best Practices:

#### ✅ DO:
- Verwende `config.env` als Vorlage
- Erstelle `.env` lokal (wird ignoriert)
- Verwende Environment Variables in Produktion
- Rotiere Credentials regelmäßig

#### ❌ DON'T:
- Committe `.env` Dateien
- Teile Credentials in Code
- Speichere Credentials in Klartext
- Verwende Credentials in öffentlichen Repositories

### Für n8n:

#### MCP Server (empfohlen):
- MCP Server liest `.env` lokal
- n8n braucht keine Swisspost Credentials
- HTTP Request zu MCP Server

#### Direkte Swisspost API:
- n8n Credentials → OAuth2 API
- Client Credentials Grant
- Token URL: `https://api.post.ch/OAuth/token`

### Monitoring:
- Überwache API-Nutzung bei Swisspost
- Prüfe auf ungewöhnliche Aktivitäten
- Rotiere Credentials bei Verdacht

---

**🔒 Sicherheit ist wichtig - Credentials niemals committen!**
