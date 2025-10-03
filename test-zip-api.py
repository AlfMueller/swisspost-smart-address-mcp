#!/usr/bin/env python3
"""
Test Swisspost ZIP API direkt
"""

import os
import asyncio
import httpx
from dotenv import load_dotenv

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
        
        print(f"DEBUG: Client ID: {client_id[:8] if client_id else 'None'}...")
        print(f"DEBUG: Scope: {scope}")
        
        if not client_id or not client_secret:
            print("❌ Credentials nicht gefunden")
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
            
            print(f"DEBUG: OAuth Response Status: {response.status_code}")
            print(f"DEBUG: OAuth Response: {response.text}")
            
            if response.status_code == 200:
                data = response.json()
                return data["access_token"]
            else:
                print(f"❌ OAuth Fehler: {response.status_code} - {response.text}")
                return None
    except Exception as e:
        print(f"❌ Token Fehler: {e}")
        return None

async def test_zip_lookup(zip_code: str):
    """Teste ZIP Lookup"""
    try:
        token = await get_swisspost_token()
        if not token:
            print("❌ Kein Token verfügbar")
            return
        
        print(f"✅ Token erhalten: {token[:20]}...")
        
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
            
            print(f"DEBUG: ZIP API Response Status: {response.status_code}")
            print(f"DEBUG: ZIP API Response: {response.text}")
            
            if response.status_code == 200:
                data = response.json()
                zips = data.get('zips', [])
                
                print(f"✅ ZIP {zip_code}: {len(zips)} Städte gefunden")
                
                for i, zip_entry in enumerate(zips):
                    city18 = zip_entry.get('city18', '')
                    city27 = zip_entry.get('city27', '')
                    print(f"   {i+1}. city18: '{city18}', city27: '{city27}'")
            else:
                print(f"❌ ZIP API Fehler: {response.status_code} - {response.text}")
                
    except Exception as e:
        print(f"❌ ZIP Lookup Fehler: {e}")

async def main():
    """Hauptfunktion"""
    print("🧪 Teste Swisspost ZIP API...")
    print("=" * 50)
    
    # Test verschiedene PLZ
    test_zips = ["4586", "8001", "3000", "4000"]
    
    for zip_code in test_zips:
        print(f"\n📮 Teste PLZ: {zip_code}")
        await test_zip_lookup(zip_code)
    
    print("\n" + "=" * 50)
    print("🏁 Test abgeschlossen")

if __name__ == "__main__":
    asyncio.run(main())
