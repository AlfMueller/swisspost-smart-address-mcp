# Changelog

All notable changes to this project will be documented in this file.

## [1.0.1] - 2025-01-02

### Added
- Added comprehensive .gitignore for Python projects
- Enhanced README with detailed installation instructions
- Added Claude Desktop configuration examples
- Added troubleshooting section

### Security
- Sensitive .env files are now properly excluded from version control

## [1.0.0] - 2025-01-02

### Added
- Initial release of Swisspost Smart Address MCP Server
- Intelligent address validation with Swisspost API integration
- Automatic error detection and correction:
  - PLZ/City swap detection
  - House number normalization
  - Street name abbreviation handling
  - Stuck house number separation
- MCP (Model Context Protocol) server implementation
- Support for Claude Desktop, n8n, and MCP Inspector
- Comprehensive test suite with 5 test scenarios
- Quality scoring system (0-100)
- Swisspost API integration with OAuth2 authentication
- ZIP, Street, and House number autocomplete
- Full documentation and examples

### Features
- **Smart Address Analysis**: Detects common address input errors
- **Swisspost API Integration**: Uses official Swisspost APIs for validation
- **Automatic Corrections**: Fixes errors and normalizes addresses
- **Quality Assessment**: Provides scoring and quality ratings
- **MCP Server**: Integrates seamlessly with Claude Desktop and n8n
- **Comprehensive Testing**: Automated test suite for all scenarios

### Technical Details
- Python 3.8+ support
- Async/await implementation
- OAuth2 token management
- Error handling and logging
- Type hints throughout
- MIT License
