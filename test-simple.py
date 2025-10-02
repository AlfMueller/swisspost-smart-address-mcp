"""
Einfacher Test für den Smart Address Agent
"""

import asyncio
import os
from dotenv import load_dotenv

# .env laden (override=True um bereits gesetzte Variablen zu überschreiben)
load_dotenv(override=True)

async def test_simple():
    """Einfacher Test ohne Import-Probleme"""
    
    # Prüfe Credentials
    client_id = os.getenv("SWISSPOST_CLIENT_ID")
    client_secret = os.getenv("SWISSPOST_CLIENT_SECRET")
    
    print("=== CREDENTIALS CHECK ===")
    print(f"CLIENT_ID: {client_id[:10]}..." if client_id else "CLIENT_ID: None")
    print(f"CLIENT_SECRET: {client_secret[:10]}..." if client_secret else "CLIENT_SECRET: None")
    print(f".env Datei vorhanden: {os.path.exists('.env')}")
    
    if not client_id or not client_secret:
        print("❌ FEHLER: Credentials nicht gesetzt!")
        return
    
    print("✅ Credentials OK!")
    
    # Teste Import
    try:
        import sys
        import importlib.util
        spec = importlib.util.spec_from_file_location("smart_address_agent", "smart-address-agent.py")
        smart_address_agent = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(smart_address_agent)
        SmartAddressAgent = smart_address_agent.SmartAddressAgent
        print("✅ Import erfolgreich!")
        
        # Teste Agent-Erstellung
        agent = SmartAddressAgent()
        print("✅ Agent erstellt!")
        
        # Teste eine einfache Adresse
        test_address = {
            'street': 'Bundesplatz 3',
            'city': 'Bern',
            'postcode': '3005'
        }
        
        print("\n=== ADRESS-TEST ===")
        print(f"Teste: {test_address}")
        
        result = await agent.validate_smart(test_address)
        
        print("✅ Test erfolgreich!")
        print(f"Status: {result['status']}")
        print(f"Quality: {result['quality']}")
        print(f"Score: {result['score']}")
        
    except Exception as e:
        print(f"❌ FEHLER: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_simple())
