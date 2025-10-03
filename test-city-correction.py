#!/usr/bin/env python3
"""
Test City Correction für Swisspost MCP Server
"""

import requests
import json

def test_city_correction():
    """Teste City Correction mit verschiedenen Fällen"""
    
    test_cases = [
        {
            "name": "Kyburg 4586 - sollte korrigiert werden",
            "data": {
                "street": "Talstr. 4",
                "city": "4586",  # PLZ und Stadt vertauscht
                "postcode": "Kyburg"
            }
        },
        {
            "name": "Kyburg 4586 - korrekte Reihenfolge",
            "data": {
                "street": "Talstr. 4", 
                "city": "Kyburg",
                "postcode": "4586"
            }
        },
        {
            "name": "Zürich 8001 - korrekte Adresse",
            "data": {
                "street": "Bahnhofstrasse 1",
                "city": "Zürich",
                "postcode": "8001"
            }
        }
    ]
    
    base_url = "http://localhost:3000"
    
    print("🧪 Teste City Correction...")
    print("=" * 50)
    
    for test_case in test_cases:
        print(f"\n📋 Test: {test_case['name']}")
        print(f"   Eingabe: {test_case['data']}")
        
        try:
            response = requests.post(
                f"{base_url}/validate",
                json=test_case['data'],
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('success'):
                    data = result.get('data', {})
                    corrected = data.get('corrected', {})
                    corrections = data.get('corrections', [])
                    city_correction = data.get('city_correction', {})
                    
                    print(f"   ✅ Status: {data.get('status', 'unknown')}")
                    print(f"   📊 Score: {data.get('score', 'unknown')}")
                    print(f"   🏙️  Stadt: {corrected.get('city', 'unknown')}")
                    print(f"   📮 PLZ: {corrected.get('postcode', 'unknown')}")
                    print(f"   🛣️  Strasse: {corrected.get('street_full', 'unknown')}")
                    
                    if corrections:
                        print(f"   🔧 Korrekturen: {len(corrections)}")
                        for correction in corrections:
                            print(f"      - {correction.get('message', 'Unknown correction')}")
                    
                    if city_correction:
                        print(f"   🏙️  Stadt-Korrektur:")
                        print(f"      Original: {city_correction.get('original', 'unknown')}")
                        print(f"      Korrigiert: {city_correction.get('corrected', 'unknown')}")
                        print(f"      Auto-korrigiert: {city_correction.get('auto_corrected', False)}")
                else:
                    print(f"   ❌ Fehler: {result.get('error', 'Unknown error')}")
            else:
                print(f"   ❌ HTTP Fehler: {response.status_code}")
                print(f"   Response: {response.text}")
                
        except requests.exceptions.ConnectionError:
            print(f"   ❌ Verbindungsfehler: Server läuft nicht auf {base_url}")
            break
        except Exception as e:
            print(f"   ❌ Fehler: {e}")
    
    print("\n" + "=" * 50)
    print("🏁 Test abgeschlossen")

if __name__ == "__main__":
    test_city_correction()
