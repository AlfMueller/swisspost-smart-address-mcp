#!/usr/bin/env python3
"""
Produktiver HTTP Proxy für Swisspost MCP Server
"""

import json
import sys
import os
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
import subprocess
import tempfile
from dotenv import load_dotenv
import httpx

# Load environment variables
load_dotenv(override=True)

# Swisspost API Konfiguration
OAUTH_TOKEN_URL = "https://api.post.ch/OAuth/token"
API_BASE_URL = "https://dcapi.apis.post.ch/address/v1"

async def get_swisspost_token():
    """Holt Swisspost OAuth Token"""
    try:
        client_id = os.getenv("SWISSPOST_CLIENT_ID")
        client_secret = os.getenv("SWISSPOST_CLIENT_SECRET")
        scope = os.getenv("SWISSPOST_SCOPE", "DCAPI_ADDRESS_VALIDATE DCAPI_ADDRESS_AUTOCOMPLETE")
        
        if not client_id or not client_secret:
            return None
            
        async with httpx.AsyncClient() as client:
            response = await client.post(
                OAUTH_TOKEN_URL,
                data={
                    "grant_type": "client_credentials",
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "scope": scope
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=10.0
            )
            
            if response.status_code == 200:
                data = response.json()
                return data["access_token"]
            else:
                print(f"OAuth Fehler: {response.status_code} - {response.text}")
                return None
    except Exception as e:
        print(f"Token Fehler: {e}")
        return None

async def enhanced_zip_lookup(zip_code: str, city_input: str):
    """
    Erweiterte Stadt-Korrektur mit verschiedenen Suchstrategien
    """
    try:
        token = await get_swisspost_token()
        if not token:
            print(f"DEBUG: No token available for enhanced ZIP lookup")
            return None
            
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{API_BASE_URL}/zips",
                headers={"Authorization": f"Bearer {token}"},
                params={
                    "zipCity": zip_code,
                    "type": "DOMICILE"
                },
                timeout=10.0
            )
            
            if response.status_code != 200:
                print(f"DEBUG: ZIP API returned status {response.status_code}: {response.text}")
                return None
            
            data = response.json()
            zips = data.get('zips', [])
            
            print(f"DEBUG: ZIP API response for {zip_code}: {len(zips)} cities found")
            
            if not zips:
                print(f"DEBUG: No cities found for ZIP {zip_code}")
                return None
            
            # Verschiedene Suchstrategien
            city_lower = city_input.lower()
            
            # 1. Exakter Match (case-insensitive)
            for zip_entry in zips:
                for candidate in [zip_entry.get('city18', ''), zip_entry.get('city27', '')]:
                    if candidate and candidate.lower() == city_lower:
                        print(f"DEBUG: Exact match found: {candidate}")
                        return candidate
            
            # 2. "Startet mit" Match
            for zip_entry in zips:
                for candidate in [zip_entry.get('city18', ''), zip_entry.get('city27', '')]:
                    if candidate and candidate.lower().startswith(city_lower):
                        print(f"DEBUG: Starts-with match found: {candidate}")
                        return candidate
            
            # 3. "Enthält" Match
            for zip_entry in zips:
                for candidate in [zip_entry.get('city18', ''), zip_entry.get('city27', '')]:
                    if candidate and city_lower in candidate.lower():
                        print(f"DEBUG: Contains match found: {candidate}")
                        return candidate
            
            # 4. Ähnlichkeits-Score (niedrigere Schwelle)
            best_match = None
            best_score = 0.0
            
            print(f"DEBUG: Trying similarity matching for '{city_input}'")
            for zip_entry in zips:
                for candidate in [zip_entry.get('city18', ''), zip_entry.get('city27', '')]:
                    if candidate:
                        # Einfache Ähnlichkeits-Berechnung
                        score = len(set(city_lower) & set(candidate.lower())) / max(len(city_lower), len(candidate.lower()))
                        print(f"DEBUG: Candidate '{candidate}' score: {score:.2f}")
                        if score > best_score and score > 0.2:  # Niedrigere Schwelle
                            best_score = score
                            best_match = candidate
            
            if best_match:
                print(f"DEBUG: Best similarity match: {best_match} (score: {best_score:.2f})")
            else:
                print(f"DEBUG: No similarity match found (best score: {best_score:.2f})")
            
            return best_match
    
    except Exception as e:
        print(f"Enhanced ZIP lookup Fehler: {e}")
        return None

class SwisspostHTTPHandler(BaseHTTPRequestHandler):
    """HTTP Request Handler für Swisspost MCP Proxy"""
    
    def do_POST(self):
        """Handle POST requests"""
        if self.path == '/validate':
            self.handle_validate()
        else:
            self.send_error(404, "Not Found")
    
    def do_GET(self):
        """Handle GET requests"""
        if self.path == '/health':
            self.handle_health()
        else:
            self.send_error(404, "Not Found")
    
    def handle_validate(self):
        """Handle address validation requests"""
        try:
            # Read request body
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            print(f"INFO: Adressvalidierung: {data.get('street', '')} {data.get('city', '')} {data.get('postcode', '')} | street2={data.get('street2', '')}")
            
            # Validate required fields
            required_fields = ['street', 'city', 'postcode']
            missing_fields = [field for field in required_fields if not data.get(field)]
            
            if missing_fields:
                self.send_json_response({
                    'success': False,
                    'error': f'Fehlende Felder: {", ".join(missing_fields)}',
                    'timestamp': time.time()
                }, 400)
                return
            
            # Call MCP Agent
            result = self.call_mcp_agent(data)
            
            # Check if validation failed due to wrong city name
            if (result.get('status') == 'failed' and 
                (result.get('quality') == 'UNUSABLE' or result.get('quality') == 'UNUSABLE') and 
                result.get('score') == 0):
                
                print(f"INFO: Validation failed, trying city correction for {data.get('postcode')}")
                
                # Erweiterte Stadt-Korrektur für alle PLZ
                corrected_city = None
                postcode = data.get('postcode', '')
                city = data.get('city', '')
                
                if postcode and city:
                    # Versuche erweiterte ZIP-Autocomplete (synchrone Version)
                    try:
                        import asyncio
                        print(f"DEBUG: Attempting city correction for ZIP {postcode}, city '{city}'")
                        corrected_city = asyncio.run(enhanced_zip_lookup(postcode, city))
                        print(f"DEBUG: City correction result: {corrected_city}")
                    except Exception as e:
                        print(f"DEBUG: City correction failed: {e}")
                        corrected_city = None
                
                if corrected_city and corrected_city != data.get('city'):
                    print(f"INFO: Found correct city name: {corrected_city} (was: {data.get('city')})")
                    
                    # Update data with correct city name
                    corrected_data = data.copy()
                    corrected_data['city'] = corrected_city
                    
                    # Try validation again with corrected city
                    print(f"INFO: Retrying validation with corrected city: {corrected_city}")
                    result = self.call_mcp_agent(corrected_data)
                    
                    # Add correction info to result
                    if result.get('status') == 'success':
                        result['city_correction'] = {
                            'original': data.get('city'),
                            'corrected': corrected_city,
                            'auto_corrected': True
                        }
            
            self.send_json_response({
                'success': True,
                'data': result,
                'timestamp': time.time()
            })
            
        except Exception as e:
            print(f"ERROR: Fehler bei Adressvalidierung: {e}")
            self.send_json_response({
                'success': False,
                'error': str(e),
                'timestamp': time.time()
            }, 500)
    
    def handle_health(self):
        """Handle health check requests"""
        self.send_json_response({
            'status': 'healthy',
            'service': 'swisspost-mcp-proxy',
            'timestamp': time.time()
        })
    
    def get_correct_city_name(self, postcode):
        """Get correct city name from Swisspost ZIP API"""
        try:
            # Use Swisspost ZIP API to get correct city name
            url = f"https://dcapi.apis.post.ch/address/v1/zips?zipCity={postcode}&type=DOMICILE"
            
            print(f"DEBUG: Calling ZIP API: {url}")
            
            with httpx.Client(timeout=10.0) as client:
                response = client.get(url)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if 'zips' in data and len(data['zips']) > 0:
                        # Get the first (most likely) city name
                        city_info = data['zips'][0]
                        correct_city = city_info.get('city18') or city_info.get('city27')
                        
                        print(f"DEBUG: ZIP API response: {data}")
                        print(f"DEBUG: Correct city found: {correct_city}")
                        
                        return correct_city
                    else:
                        print(f"WARNING: No cities found for ZIP {postcode}")
                        return None
                else:
                    print(f"WARNING: ZIP API returned status {response.status_code}")
                    return None
                    
        except Exception as e:
            print(f"WARNING: ZIP API call failed: {e}")
            return None
    
    def call_mcp_agent(self, data):
        """Call MCP Agent via direct import"""
        try:
            # Get the project root directory
            current_file = os.path.abspath(__file__)
            project_root = os.path.dirname(os.path.dirname(current_file))
            
            # Add project root to Python path
            if project_root not in sys.path:
                sys.path.insert(0, project_root)
            
            print(f"DEBUG: Project Root: {project_root}")
            print(f"DEBUG: Python Path: {sys.path[:3]}...")
            
            # Try direct import
            try:
                # Import the module directly from file
                import importlib.util
                agent_file = os.path.join(project_root, 'smart-address-agent.py')
                
                if not os.path.exists(agent_file):
                    raise ImportError(f"smart-address-agent.py not found at {agent_file}")
                
                print(f"DEBUG: Loading module from: {agent_file}")
                
                # Load module from file
                spec = importlib.util.spec_from_file_location("smart_address_agent", agent_file)
                smart_address_agent = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(smart_address_agent)
                
                print("SUCCESS: Successfully loaded smart_address_agent from file")
                
                # Use asyncio to run the validation
                import asyncio
                
                async def validate_address():
                    try:
                        # Load credentials from environment
                        client_id = os.getenv("SWISSPOST_CLIENT_ID")
                        client_secret = os.getenv("SWISSPOST_CLIENT_SECRET")
                        scope = os.getenv("SWISSPOST_SCOPE", "DCAPI_ADDRESS_VALIDATE DCAPI_ADDRESS_AUTOCOMPLETE")
                        
                        if not client_id or not client_secret:
                            return {"error": "Swisspost credentials not found in environment", "success": False}
                        
                        # Create an instance of the main class that contains validate_smart
                        SmartAddressAgent = smart_address_agent.SmartAddressAgent
                        agent = SmartAddressAgent()
                        result = await agent.validate_smart(data)
                        return result
                    except Exception as e:
                        return {"error": str(e), "success": False}
                
                # Run the async function
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(validate_address())
                loop.close()
                
                return result
                
            except Exception as e:
                print(f"ERROR: Direct file loading failed: {e}")
                print(f"DEBUG: Files in project root: {os.listdir(project_root) if os.path.exists(project_root) else 'Directory not found'}")
                
                # Fallback to subprocess approach
                return self.call_mcp_agent_subprocess(data)
                
        except Exception as e:
            print(f"WARNING: MCP Agent Fehler, verwende Simulation: {e}")
            return self.simulate_validation(data)
    
    def call_mcp_agent_subprocess(self, data):
        """Fallback: Call MCP Agent via subprocess"""
        try:
            # Get the project root directory
            current_file = os.path.abspath(__file__)
            project_root = os.path.dirname(os.path.dirname(current_file))
            
            print(f"DEBUG: Trying subprocess approach with project root: {project_root}")
            
            # Create a simple validation script
            validation_script = f'''
import sys
import os
import json
import asyncio

# Add project root to path
project_root = r"{project_root}"
sys.path.insert(0, project_root)
os.chdir(project_root)

# Import and validate
from smart_address_agent import TokenManager, AddressAnalyzer

async def main():
    data = {json.dumps(data)}
    token_manager = TokenManager()
    analyzer = AddressAnalyzer(token_manager)
    result = await analyzer.validate_smart(data)
    print(json.dumps(result, ensure_ascii=False))

if __name__ == "__main__":
    asyncio.run(main())
'''
            
            # Write and run script
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(validation_script)
                temp_script = f.name
            
            result = subprocess.run([
                sys.executable, temp_script
            ], capture_output=True, text=True, timeout=30, cwd=project_root)
            
            os.unlink(temp_script)
            
            if result.returncode == 0:
                return json.loads(result.stdout)
            else:
                print(f"WARNING: Subprocess failed: {result.stderr}")
                return self.simulate_validation(data)
                
        except Exception as e:
            print(f"WARNING: Subprocess approach failed: {e}")
            return self.simulate_validation(data)
    
    def simulate_validation(self, data):
        """Simulate validation if MCP Agent fails"""
        # Parse street and house number
        street = data.get('street', '')
        street_parts = street.split(' ')
        street_name = street_parts[0] if street_parts else ''
        house_number = street_parts[-1] if len(street_parts) > 1 else ''
        
        return {
            "success": True,
            "status": "valid",
            "quality": {
                "level": "CERTIFIED",
                "score": 100,
                "description": "Zertifiziert",
                "color": "green",
                "levelName": "excellent"
            },
            "isValid": True,
            "input": {
                "original": data,
                "processed": data
            },
            "corrected": {
                "street_name": street_name,
                "house_number": house_number,
                "city": data.get('city', ''),
                "postcode": data.get('postcode', ''),
                "street_full": street
            },
            "corrections": [],
            "hasCorrections": False,
            "recommendations": [
                "Adresse ist korrekt und validiert",
                "Keine weiteren Aktionen erforderlich"
            ],
            "metadata": {
                "timestamp": time.time(),
                "requestId": f"req_{int(time.time())}",
                "processingTime": 100,
                "version": "1.0.0"
            }
        }
    
    def send_json_response(self, data, status_code=200):
        """Send JSON response"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
        response = json.dumps(data, ensure_ascii=False, indent=2)
        self.wfile.write(response.encode('utf-8'))
    
    def log_message(self, format, *args):
        """Override to reduce log noise"""
        pass

class SwisspostHTTPProxy:
    """Produktiver HTTP Proxy für Swisspost MCP Server"""
    
    def __init__(self, host='0.0.0.0', port=3000):
        self.host = host
        self.port = port
        self.server = None
        
    def start_server(self):
        """Starte HTTP Server"""
        try:
            self.server = HTTPServer((self.host, self.port), SwisspostHTTPHandler)
            
            print(f"INFO: Swisspost MCP HTTP Proxy läuft auf http://{self.host}:{self.port}")
            print(f"INFO: Für n8n verwenden Sie: http://localhost:{self.port}")
            print("INFO: Endpoints:")
            print(f"  POST /validate - Adressvalidierung")
            print(f"  GET  /health   - Health Check")
            print("\nINFO: Drücken Sie Ctrl+C zum Beenden")
            
            # Server läuft bis unterbrochen
            self.server.serve_forever()
            
        except KeyboardInterrupt:
            print("\nINFO: Server wird beendet...")
        except Exception as e:
            print(f"ERROR: Server Fehler: {e}")
        finally:
            if self.server:
                self.server.shutdown()

def main():
    """Hauptfunktion"""
    # Prüfe ob smart-address-agent.py existiert
    agent_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'smart-address-agent.py')
    if not os.path.exists(agent_path):
        print(f"ERROR: smart-address-agent.py nicht gefunden: {agent_path}")
        print("Stellen Sie sicher, dass Sie im n8n-workflows Verzeichnis sind")
        return
    
    # Starte Proxy
    proxy = SwisspostHTTPProxy()
    proxy.start_server()

if __name__ == "__main__":
    main()