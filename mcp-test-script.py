"""
Test-Skript für den Smart Address Agent MCP Server

Testet verschiedene Adress-Szenarien ohne Claude Desktop
"""

import asyncio
import json
import sys
import os
from dotenv import load_dotenv

# .env Datei laden
load_dotenv(override=True)

# Server-Code importieren (anpassen an deinen Pfad)
sys.path.insert(0, os.path.dirname(__file__))


async def test_address(agent, test_case):
    """Testet eine einzelne Adresse"""
    print(f"\n{'='*80}")
    print(f"TEST: {test_case['name']}")
    print(f"{'='*80}")
    print(f"Input:")
    print(f"  Strasse: {test_case['input']['street']}")
    print(f"  Ort:     {test_case['input']['city']}")
    print(f"  PLZ:     {test_case['input']['postcode']}")
    
    try:
        result = await agent.validate_smart(test_case['input'])
        
        print(f"\nErgebnis:")
        print(f"  Status:  {result['status']}")
        print(f"  Quality: {result['quality']}")
        print(f"  Score:   {result['score']}")
        
        if result.get('corrections'):
            print(f"\nKorrekturen:")
            for corr in result['corrections']:
                print(f"  - {corr['message']}")
                if corr['type'] == 'swap_plz_city':
                    print(f"    Alt: PLZ={corr['old']['postcode']}, Ort={corr['old']['city']}")
                    print(f"    Neu: PLZ={corr['new']['postcode']}, Ort={corr['new']['city']}")
                else:
                    print(f"    Alt: {corr.get('old', 'N/A')}")
                    print(f"    Neu: {corr.get('new', 'N/A')}")
        
        print(f"\nKorrigierte Adresse:")
        print(f"  {result['corrected']['street_name']} {result['corrected']['house_number']}")
        print(f"  {result['corrected']['postcode']} {result['corrected']['city']}")
        
        print(f"\n{'='*80}")
        
    except Exception as e:
        print(f"\nFEHLER: {str(e)}")
        import traceback
        traceback.print_exc()


async def main():
    """Haupttestfunktion"""
    
    # Prüfe ob Credentials gesetzt sind
    if not os.getenv("SWISSPOST_CLIENT_ID") or not os.getenv("SWISSPOST_CLIENT_SECRET"):
        print("FEHLER: SWISSPOST_CLIENT_ID und SWISSPOST_CLIENT_SECRET müssen gesetzt sein!")
        print("\nSetze sie mit:")
        print("  export SWISSPOST_CLIENT_ID=deine_client_id")
        print("  export SWISSPOST_CLIENT_SECRET=dein_secret")
        sys.exit(1)
    
    # Agent importieren
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("smart_address_agent", "smart-address-agent.py")
        smart_address_agent = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(smart_address_agent)
        SmartAddressAgent = smart_address_agent.SmartAddressAgent
    except Exception as e:
        print(f"FEHLER: Kann 'smart-address-agent.py' nicht importieren: {e}")
        print("Stelle sicher, dass smart-address-agent.py im gleichen Verzeichnis ist.")
        sys.exit(1)
    
    print("Initialisiere Smart Address Agent...")
    agent = SmartAddressAgent()
    
    # Test-Fälle
    test_cases = [
        {
            'name': 'PLZ und Ort vertauscht',
            'input': {
                'street': 'Musterstrasse 123',
                'city': '8001',
                'postcode': 'Musterstadt'
            }
        },
        {
            'name': 'Hausnummer am Anfang',
            'input': {
                'street': '123 Musterstrasse',
                'city': 'Musterstadt',
                'postcode': '8001'
            }
        },
        {
            'name': 'Abkürzung in Strassenname',
            'input': {
                'street': 'Hauptstr. 43',
                'city': 'Beispielstadt',
                'postcode': '8002'
            }
        },
        {
            'name': 'Verklebte Hausnummer',
            'input': {
                'street': 'Bahnhofstrasse123',
                'city': 'Teststadt',
                'postcode': '8003'
            }
        },
        {
            'name': 'Korrekte Adresse (sollte durchgehen)',
            'input': {
                'street': 'Bundesplatz 3',
                'city': 'Bern',
                'postcode': '3005'
            }
        }
    ]
    
    # Alle Tests durchlaufen
    for test_case in test_cases:
        await test_address(agent, test_case)
        await asyncio.sleep(0.5)  # Kurze Pause zwischen Tests
    
    print("\n" + "="*80)
    print("ALLE TESTS ABGESCHLOSSEN")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(main())
