# MCP Servers Directory

A curated list of Model Context Protocol (MCP) servers for Claude Desktop, n8n, and other MCP clients.

## 🇨🇭 Swisspost Smart Address MCP Server

**Repository:** [https://github.com/AlfMueller/swisspost-smart-address-mcp](https://github.com/AlfMueller/swisspost-smart-address-mcp)

**Description:** Intelligent Swiss address validation with automatic error correction using Swisspost APIs.

**Features:**
- PLZ/City swap detection
- House number normalization
- Street name abbreviation handling
- Quality scoring (0-100)
- Swisspost API integration

**Keywords:** `swisspost` `mcp` `address-validation` `claude-desktop` `n8n` `switzerland`

**Installation:**
```bash
git clone https://github.com/AlfMueller/swisspost-smart-address-mcp.git
cd swisspost-smart-address-mcp
pip install -r requirements.txt
```

**Claude Desktop Config:**
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

**Pfad anpassen:** `/path/to/your/swissspost_mcp/smart-address-agent.py` (anpassen an Ihren Installationsort)

---

## Contributing

To add your MCP server to this list:

1. Fork this repository
2. Add your server information
3. Create a pull request

## License

MIT License - see LICENSE file for details.
