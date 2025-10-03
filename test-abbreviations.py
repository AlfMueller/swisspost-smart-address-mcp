#!/usr/bin/env python3
"""
Test für Abkürzungs-Erweiterung und Formatierung
"""

import asyncio
import os
from dotenv import load_dotenv

# .env laden
load_dotenv(override=True)

async def test_abbreviations():
    """Test der Abkürzungs-Erweiterung"""
    
    # Prüfe Credentials
    if not os.getenv("SWISSPOST_CLIENT_ID") or not os.getenv("SWISSPOST_CLIENT_SECRET"):
        print("❌ FEHLER: Credentials nicht gesetzt!")
        return
    
    try:
        # Importiere den Agent
        import sys
        import importlib.util
        spec = importlib.util.spec_from_file_location("smart_address_agent", "smart-address-agent.py")
        smart_address_agent = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(smart_address_agent)
        SmartAddressAgent = smart_address_agent.SmartAddressAgent
        
        agent = SmartAddressAgent()
        
        # Test-Fälle für Abkürzungen
        test_cases = [
            {
                'name': 'Deutsche Abkürzungen',
                'input': {
                    'street': 'bachstr 15',
                    'city': 'ostermundigen',
                    'postcode': '3072'
                }
            },
            {
                'name': 'Französische Abkürzungen',
                'input': {
                    'street': 'r. de la paix 42',
                    'city': 'genève',
                    'postcode': '1200'
                }
            },
            {
                'name': 'Italienische Abkürzungen',
                'input': {
                    'street': 'v. roma 10',
                    'city': 'lugano',
                    'postcode': '6900'
                }
            },
            {
                'name': 'Gemischte Abkürzungen',
                'input': {
                    'street': 'hauptstr. 123',
                    'city': 'zürich',
                    'postcode': '8001'
                }
            }
        ]
        
        print("🧪 Teste Abkürzungs-Erweiterung und Formatierung...")
        print("=" * 80)
        
        for test_case in test_cases:
            print(f"\n📋 TEST: {test_case['name']}")
            print(f"Input: {test_case['input']}")
            print("-" * 40)
            
            try:
                result = await agent.validate_smart(test_case['input'])
                
                print(f"✅ Status: {result['status']}")
                print(f"📊 Score: {result['score']}")
                print(f"🏷️  Quality: {result['quality']}")
                
                if result.get('corrections'):
                    print(f"\n🔧 Korrekturen ({len(result['corrections'])}):")
                    for corr in result['corrections']:
                        print(f"  • {corr['message']}")
                        print(f"    Alt: {corr.get('old', 'N/A')}")
                        print(f"    Neu: {corr.get('new', 'N/A')}")
                
                print(f"\n📝 Korrigierte Ausgabe:")
                corrected = result['corrected']
                print(f"  Strasse: '{corrected['street_name']}'")
                print(f"  Hausnummer: '{corrected['house_number']}'")
                print(f"  Stadt: '{corrected['city']}'")
                print(f"  PLZ: '{corrected['postcode']}'")
                print(f"  Vollständig: '{corrected['street_full']}'")
                
            except Exception as e:
                print(f"❌ Fehler: {e}")
            
            print("=" * 80)
            await asyncio.sleep(1)  # Pause zwischen Tests
        
        print("\n🏁 Alle Tests abgeschlossen!")
        
    except Exception as e:
        print(f"❌ Import-Fehler: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_abbreviations())
