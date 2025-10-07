"""
Smart Address Agent MCP Server mit Swisspost Autocomplete

Nutzt Swisspost API für:
- ZIP auto-completion (korrekter Ortsname)
- Street auto-completion (korrekte Schreibweise)
- House number auto-completion (Hausnummer validieren)
"""

import os
import json
import re
import time
from typing import Any, Optional, Dict, List, Tuple
import httpx
from mcp.server import Server
from mcp.types import Tool, TextContent
import mcp.server.stdio
from dotenv import load_dotenv

# .env Datei laden (override=True um bereits gesetzte Variablen zu überschreiben)
load_dotenv(override=True)


# Swisspost API Konfiguration
OAUTH_TOKEN_URL = "https://api.post.ch/OAuth/token"
API_BASE_URL = "https://dcapi.apis.post.ch/address/v1"


class TokenManager:
    """OAuth2 Token Manager"""
    
    def __init__(self, client_id: str, client_secret: str, scope: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.scope = scope
        self.access_token: Optional[str] = None
        self.token_expires_at: float = 0
    
    async def get_token(self) -> str:
        if self.access_token and time.time() < (self.token_expires_at - 30):
            return self.access_token
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                OAUTH_TOKEN_URL,
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "scope": self.scope
                },
                headers={
                    "Content-Type": "application/x-www-form-urlencoded"
                },
                timeout=10.0
            )
            
            if response.status_code == 200:
                data = response.json()
                self.access_token = data["access_token"]
                expires_in = data.get("expires_in", 300)
                self.token_expires_at = time.time() + expires_in
                return self.access_token
            else:
                print(f"OAuth Debug: Status {response.status_code}")
                print(f"OAuth Debug: Response {response.text}")
                raise Exception(f"OAuth Fehler: {response.status_code} - {response.text}")


class AddressAnalyzer:
    """Intelligente Adressanalyse"""
    
    @staticmethod
    def is_swiss_plz(value: str) -> bool:
        """Prüft ob Wert eine Schweizer PLZ ist (4 Ziffern)"""
        return bool(re.match(r'^\d{4}$', str(value).strip()))
    
    @staticmethod
    def normalize_street(street: str) -> Tuple[str, str]:
        """
        Normalisiert Strasse und extrahiert Hausnummer
        Returns: (strassenname, hausnummer)
        """
        if not street:
            return "", ""
        
        street = street.strip()
        
        # Komma entfernen: "64-66, Rue du Grand-Pré" -> "64-66 Rue du Grand-Pré"
        street = re.sub(r',\s*', ' ', street)
        
        # Hausnummer am Anfang: "94 Pfingstweidstrasse" -> "Pfingstweidstrasse", "94"
        match = re.match(r'^(\d+[a-zA-Z]?(?:[/-]\d+[a-zA-Z]?)?)\s+(.+)$', street)
        if match:
            return match.group(2).strip(), match.group(1).strip()
        
        # Hausnummer am Ende mit Trenner: "Hauptstrasse 43"
        match = re.match(r'^(.*?)[\s,\-]+(\d+[a-zA-Z]?(?:[/-]\d+[a-zA-Z]?)?)$', street)
        if match:
            return match.group(1).strip(), match.group(2).strip()
        
        # Hausnummer verklebt: "Hauptstrasse43"
        match = re.match(r'^(.*?)(\d+[a-zA-Z]?(?:[/-]\d+[a-zA-Z]?)?)$', street)
        if match and match.group(1):
            return match.group(1).strip(), match.group(2).strip()
        
        return street, ""
    
    @staticmethod
    def normalize_string(s: str) -> str:
        """Normalisiert String für Vergleiche (lowercase, ohne Diakritika)"""
        import unicodedata
        s = s.lower()
        s = unicodedata.normalize('NFD', s)
        s = ''.join(c for c in s if not unicodedata.combining(c))
        return s
    
    @staticmethod
    def similarity_score(a: str, b: str) -> float:
        """
        Berechnet Ähnlichkeit zwischen zwei Strings (0.0 - 1.0)
        Nutzt character overlap
        """
        a_norm = AddressAnalyzer.normalize_string(a)
        b_norm = AddressAnalyzer.normalize_string(b)
        
        if not a_norm or not b_norm:
            return 0.0
        
        # Character frequency
        def char_freq(s):
            freq = {}
            for c in s.replace(' ', ''):
                freq[c] = freq.get(c, 0) + 1
            return freq
        
        freq_a = char_freq(a_norm)
        freq_b = char_freq(b_norm)
        
        # Overlap
        overlap = 0
        for char, count in freq_a.items():
            overlap += min(count, freq_b.get(char, 0))
        
        # Normalisieren auf längeren String
        max_len = max(len(a_norm.replace(' ', '')), len(b_norm.replace(' ', '')))
        return overlap / max_len if max_len > 0 else 0.0
    
    @staticmethod
    def expand_street_abbreviations(street: str) -> str:
        """
        Erweitert Strassen-Abkürzungen zu vollständigen Namen
        """
        if not street:
            return street
        
        # Abkürzungs-Mapping (längere zuerst, um Überschneidungen zu vermeiden)
        abbreviations = {
            # Deutsche Abkürzungen
            'str.': 'strasse',
            'str ': 'strasse ',
            'str$': 'strasse',
            'wg.': 'weg',
            'wg ': 'weg ',
            'wg$': 'weg',
            'all.': 'allee',
            'all ': 'allee ',
            'all$': 'allee',
            'prom.': 'promenade',
            'prom ': 'promenade ',
            'prom$': 'promenade',
            'g.': 'gasse',
            'g ': 'gasse ',
            'g$': 'gasse',
            
            # Französische Abkürzungen
            'av.': 'avenue',
            'av ': 'avenue ',
            'av$': 'avenue',
            'bd.': 'boulevard',
            'bd ': 'boulevard ',
            'bd$': 'boulevard',
            'ch.': 'chemin',
            'ch ': 'chemin ',
            'ch$': 'chemin',
            'rt.': 'route',
            'rt ': 'route ',
            'rt$': 'route',
            
            # Italienische Abkürzungen
            'c.so': 'corso',
            'cs.': 'corso',
            'cs ': 'corso ',
            'cs$': 'corso',
            'p.za.': 'piazza',
            'p.za': 'piazza',
            'l.go.': 'largo',
            'l.go': 'largo',
            'vic.': 'vicolo',
            'vic ': 'vicolo ',
            'vic$': 'vicolo',
            'pgg.': 'passeggiata',
            'pgg ': 'passeggiata ',
            'pgg$': 'passeggiata',
            'vl.': 'viale',
            'vl ': 'viale ',
            'vl$': 'viale',
            'v.': 'via',
            'v ': 'via ',
            'v$': 'via',
            
            # Hinweis: riskante Ein-Buchstaben-Abkürzungen wie 'r.'/'pl.' werden NICHT ersetzt,
            # da sie legitime Namen (z.B. 'Guiguer') fehlerhaft verändern könnten
        }
        
        # Sortiere nach Länge (längere zuerst)
        sorted_abbrev = sorted(abbreviations.items(), key=lambda x: len(x[0]), reverse=True)
        
        # Abkürzungen ersetzen (nur sichere, punktierte, kleingeschriebene Formen an Wortgrenzen)
        result = street
        for abbrev, full in sorted_abbrev:
            # Nur punktierte Formen sicher ersetzen
            if '.' in abbrev:
                # Wortgrenzen respektieren, kleinschreibung voraussetzen
                safe_pattern = r"\b" + re.escape(abbrev) + r"\b"
                result = re.sub(safe_pattern, full, result)
        
        return result

    @staticmethod
    def capitalize_street_name(street_name: str) -> str:
        """Kapitalisiert den ersten Buchstaben des Straßennamens, falls nötig."""
        if not street_name:
            return street_name
        # Nur kapitalisieren, wenn der erste Buchstabe klein ist
        if street_name[0].islower():
            return street_name[0].upper() + street_name[1:]
        return street_name

    @staticmethod
    def format_corrected_output(street_name: str, house_number: str, city: str, postcode: str, 
                               firstname: str = "", lastname: str = "", company: str = "") -> Dict[str, str]:
        """
        Formatiert die korrigierte Ausgabe. Straßennamen und Ortsnamen werden in der
        von der SwissPost-API gelieferten Schreibweise belassen (keine Title-Case-
        Umwandlung), damit Artikel/Präpositionen wie „de/des/du/der“ korrekt bleiben.
        """
        # Stadt und Strasse: Übernehme Schreibweise unverändert aus API
        city_formatted = city if city else ""
        street_formatted = street_name if street_name else ""
        
        # Hausnummer unverändert
        house_formatted = house_number if house_number else ""
        
        # Vollständige Strasse
        street_full = f"{street_formatted} {house_formatted}".strip()
        
        # Personendaten: Vor-/Nachname in Title-Case; Firmenname unverändert (Casing bleibt wie geliefert)
        firstname_formatted = firstname.title() if firstname else ""
        lastname_formatted = lastname.title() if lastname else ""
        company_formatted = company if company else ""
        
        return {
            "street_name": street_formatted,
            "house_number": house_formatted,
            "city": city_formatted,
            "postcode": postcode,
            "street_full": street_full,
            "firstname": firstname_formatted,
            "lastname": lastname_formatted,
            "company": company_formatted
        }

    @staticmethod
    def normalize_company_legal_forms(company: str) -> str:
        """Normalisiert bekannte Rechtsformen in Firmenname, Rest bleibt unverändert.
        Ersetzt nur die spezifizierten Begriffe fallunabhängig durch kanonische Schreibweise.
        """
        if not company:
            return company or ""

        canonical_forms = [
            "GmbH & Co. KG",
            "AG & Co. KG",
            "S.p.A.",
            "S.r.l.s.",
            "S.r.l.",
            "S.a.s.",
            "S.n.c.",
            "S.a.p.A.",
            "Sàrl",
            "SAGL",
            "SARL",
            "SAS",
            "SNC",
            "KGaA",
            "GmbH",
            "AG",
            "SA",
            "SE",
            "Gen.",
            "Coop",
            "eG",
            "e.V.",
            "Ltd"
        ]

        # Längere Begriffe zuerst ersetzen, um Teil-Überschreibungen zu vermeiden
        canonical_forms.sort(key=len, reverse=True)

        result = company
        for form in canonical_forms:
            pattern = r"(?i)(?<!\w)" + re.escape(form) + r"(?!\w)"
            result = re.sub(pattern, form, result)

        return result


class SmartAddressAgent:
    """Intelligenter Adress-Agent mit Swisspost Autocomplete"""
    
    def __init__(self):
        self.server = Server("smart-address-agent")
        
        # OAuth2 Setup
        client_id = os.getenv("SWISSPOST_CLIENT_ID")
        client_secret = os.getenv("SWISSPOST_CLIENT_SECRET")
        scope = os.getenv("SWISSPOST_SCOPE", "DCAPI_ADDRESS_VALIDATE DCAPI_ADDRESS_AUTOCOMPLETE")
        
        if not client_id or not client_secret:
            print(f"DEBUG: CLIENT_ID = '{client_id}'")
            print(f"DEBUG: CLIENT_SECRET = '{client_secret}'")
            print(f"DEBUG: .env Datei vorhanden: {os.path.exists('.env')}")
            raise ValueError("SWISSPOST_CLIENT_ID und SWISSPOST_CLIENT_SECRET müssen gesetzt sein")
        
        self.token_manager = TokenManager(client_id, client_secret, scope)
        self.analyzer = AddressAnalyzer()
        
        self.setup_tools()
    
    def setup_tools(self):
        """Registriere Tools"""
        
        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            return [
                Tool(
                    name="validate_address_smart",
                    description=(
                        "Intelligenter Adress-Validator mit Swisspost Autocomplete:\n"
                        "1. Analysiert Eingabe und erkennt Fehler (PLZ/Ort vertauscht, etc.)\n"
                        "2. Nutzt ZIP-Autocomplete für korrekten Ortsnamen\n"
                        "3. Nutzt Street-Autocomplete für korrekte Strassenschreibweise\n"
                        "4. Nutzt House-Autocomplete für Hausnummer\n"
                        "5. Validiert finale Adresse und gibt Score zurück"
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "firstname": {
                                "type": "string",
                                "description": "Vorname (optional)"
                            },
                            "lastname": {
                                "type": "string",
                                "description": "Nachname (optional)"
                            },
                            "company": {
                                "type": "string",
                                "description": "Firma (optional)"
                            },
                            "street": {
                                "type": "string",
                                "description": "Strasse mit oder ohne Hausnummer"
                            },
                            "city": {
                                "type": "string",
                                "description": "Ort"
                            },
                            "postcode": {
                                "type": "string",
                                "description": "Postleitzahl"
                            }
                        },
                        "required": ["street", "city", "postcode"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Any) -> list[TextContent]:
            if name == "validate_address_smart":
                result = await self.validate_smart(arguments)
                return [TextContent(
                    type="text",
                    text=json.dumps(result, indent=2, ensure_ascii=False)
                )]
            else:
                raise ValueError(f"Unbekanntes Tool: {name}")
    
    async def validate_smart(self, address: Dict) -> Dict:
        """Intelligente Validierung mit Autocomplete"""
        
        corrections = []
        
        # Schritt 1: Eingabe analysieren
        street_raw = str(address.get('street', ''))
        city_raw = str(address.get('city', '')).strip()
        postcode_raw = str(address.get('postcode', '')).strip()
        
        # Strasse splitten (ohne weitere Korrekturen)
        street_name_raw, house_no_raw = self.analyzer.normalize_street(street_raw)
        # Originale Werte für Korrektur-Logging konservieren
        original_street_name = street_name_raw
        original_house_no = house_no_raw
        original_city = city_raw
        original_postcode = postcode_raw
        
        # Prüfe ob Komma entfernt wurde
        street_normalized = re.sub(r',\s*', ' ', street_raw)
        if street_normalized != street_raw:
            corrections.append({
                'type': 'comma_removed_from_street',
                'message': 'Komma aus Straßenname entfernt',
                'old': street_raw,
                'new': street_normalized
            })
        
        # Prüfe ob Hausnummer am Anfang war und Korrektur hinzufügen
        if house_no_raw and street_raw != f"{street_name_raw} {house_no_raw}".strip():
            # Hausnummer war am Anfang, wurde aber bereits von normalize_street korrigiert
            corrections.append({
                'type': 'house_number_moved_to_end',
                'message': 'Hausnummer vom Anfang der Straße ans Ende verschoben',
                'old': street_raw,
                'new': f"{street_name_raw} {house_no_raw}".strip()
            })
        
        # Straßenname-Kapitalisierung prüfen
        street_name_capitalized = self.analyzer.capitalize_street_name(street_name_raw)
        if street_name_capitalized != street_name_raw:
            corrections.append({
                'type': 'street_name_capitalized',
                'message': 'Straßenname mit Großbuchstaben am Anfang korrigiert',
                'old': street_name_raw,
                'new': street_name_capitalized
            })
            street_name_raw = street_name_capitalized
        
        # Schritt 1a: Erste Validierung OHNE Änderungen (keine Abkürzungen, kein Swap, kein Autocomplete)
        initial_validation = await self.call_validation_api({
            'firstname': address.get('firstname', ''),
            'lastname': address.get('lastname', ''),
            'company': address.get('company', ''),
            'street_name': street_name_raw,
            'house_number': house_no_raw,
            'city': city_raw,
            'postcode': postcode_raw
        })
        initial_quality = initial_validation.get('response', {}).get('quality', 'UNUSABLE')
        if initial_quality in ("DOMICILE_CERTIFIED", "CERTIFIED"):
            # Sofort zurückgeben – Post hat die Adresse bereits ohne Änderungen akzeptiert
            quality = initial_quality
            score = self.quality_to_score(quality)
            firstname_formatted = address.get('firstname', '').title() if address.get('firstname', '') else ""
            lastname_formatted = address.get('lastname', '').title() if address.get('lastname', '') else ""
            # Firmenname: Rechtsformen normalisieren, Rest unverändert belassen
            company_raw_early = address.get('company', '')
            company_normalized_early = self.analyzer.normalize_company_legal_forms(company_raw_early) if company_raw_early else ""
            company_formatted = company_normalized_early
            if company_raw_early and company_normalized_early != company_raw_early:
                corrections.append({
                    'type': 'company_legal_form_normalized',
                    'message': 'Rechtsform in Firmenname normalisiert',
                    'old': company_raw_early,
                    'new': company_normalized_early
                })
            # Straße/Hausnummer aus API erzwingen, falls abweichend
            api_addr = initial_validation.get('response', {}).get('address', {})
            api_house = api_addr.get('geographicLocation', {}).get('house', {})
            api_street_name = api_house.get('street', '')
            api_house_number = api_house.get('houseNumber', '')
            if api_street_name and api_street_name != street_name_raw:
                corrections.append({
                    'type': 'street_from_api_enforced',
                    'message': 'Strasse aus SwissPost API übernommen',
                    'old': street_name_raw,
                    'new': api_street_name
                })
                street_name_raw = api_street_name
            if api_house_number and api_house_number != house_no_raw:
                corrections.append({
                    'type': 'house_number_from_api_enforced',
                    'message': 'Hausnummer aus SwissPost API übernommen',
                    'old': house_no_raw,
                    'new': api_house_number
                })
                house_no_raw = api_house_number
            corrected_formatted = self.analyzer.format_corrected_output(
                street_name_raw, house_no_raw, city_raw, postcode_raw,
                firstname_formatted, lastname_formatted, company_formatted
            )
            return {
                'status': 'success',
                'quality': quality,
                'score': score,
                'corrections': corrections,
                'input': {
                    'street': street_raw,
                    'city': city_raw,
                    'postcode': postcode_raw,
                    'firstname': address.get('firstname', ''),
                    'lastname': address.get('lastname', ''),
                    'company': address.get('company', '')
                },
                'corrected': corrected_formatted,
                'validation': initial_validation.get('response', {}),
                'has_corrections': len(corrections) > 0
            }
        
        # Ab hier: Korrekturpfad, da erste Validierung nicht CERTIFIED/DOMICILE_CERTIFIED
        # PLZ/Ort-Vertauschung erkennen (ab jetzt erlaubt)
        if self.analyzer.is_swiss_plz(city_raw) and not self.analyzer.is_swiss_plz(postcode_raw):
            corrections.append({
                'type': 'swap_plz_city',
                'message': 'PLZ und Ort waren vertauscht',
                'old': {'postcode': original_postcode, 'city': original_city},
                'new': {'postcode': city_raw, 'city': postcode_raw}
            })
            postcode_raw, city_raw = city_raw, postcode_raw
        
        # Schritt 2: ZIP Autocomplete - korrekten Ortsnamen finden
        city_corrected = await self.autocomplete_zip(postcode_raw, city_raw)
        if city_corrected and city_corrected != city_raw:
            corrections.append({
                'type': 'city_corrected',
                'message': f'Ortsname korrigiert via ZIP-Lookup',
                'old': original_city,
                'new': city_corrected
            })
        city_final = city_corrected or city_raw
        
        # Fallback: Erweiterte Stadt-Korrektur für alle PLZ
        if not city_corrected and postcode_raw and city_raw:
            # Versuche erweiterte ZIP-Autocomplete mit verschiedenen Suchstrategien
            city_corrected = await self.enhanced_city_correction(postcode_raw, city_raw)
            if city_corrected and city_corrected != city_raw:
                corrections.append({
                'type': 'city_corrected',
                'message': f'Ortsname korrigiert via erweiterte ZIP-Suche',
                'old': original_city,
                'new': city_corrected
            })
                city_final = city_corrected
        
        # Schritt 3: Abkürzungen erweitern
        street_expanded = self.analyzer.expand_street_abbreviations(street_name_raw)
        if street_expanded != street_name_raw:
            corrections.append({
                'type': 'street_abbreviation_expanded',
                'message': f'Strassen-Abkürzung erweitert',
                'old': original_street_name,
                'new': street_expanded
            })
            street_name_raw = street_expanded
        
        # Schritt 4: Street Autocomplete - korrekte Schreibweise
        if postcode_raw and street_name_raw:
            street_corrected = await self.autocomplete_street(postcode_raw, street_name_raw)
            if street_corrected and street_corrected != street_name_raw:
                corrections.append({
                    'type': 'street_corrected',
                    'message': f'Strassenname korrigiert via Street-Lookup',
                    'old': original_street_name,
                    'new': street_corrected
                })
                street_name_raw = street_corrected
        
        # Schritt 5: House Autocomplete - Hausnummer validieren
        if postcode_raw and street_name_raw and house_no_raw:
            house_validated = await self.autocomplete_house(
                postcode_raw, street_name_raw, house_no_raw
            )
            if house_validated and house_validated != house_no_raw:
                corrections.append({
                    'type': 'house_number_corrected',
                    'message': f'Hausnummer korrigiert via House-Lookup',
                    'old': original_house_no,
                    'new': house_validated
                })
                house_no_raw = house_validated
        
        # Schritt 6: Finale Validierung
        validation_result = await self.call_validation_api({
            'firstname': address.get('firstname', ''),
            'lastname': address.get('lastname', ''),
            'company': address.get('company', ''),
            'street_name': street_name_raw,
            'house_number': house_no_raw,
            'city': city_final,
            'postcode': postcode_raw
        })
        
        quality = validation_result.get('response', {}).get('quality', 'UNUSABLE')
        
        # Straße/Hausnummer aus finaler API-Antwort erzwingen, falls abweichend
        final_addr = validation_result.get('response', {}).get('address', {})
        final_house = final_addr.get('geographicLocation', {}).get('house', {})
        final_street_name = final_house.get('street', '')
        final_house_number = final_house.get('houseNumber', '')
        if final_street_name and final_street_name != street_name_raw:
            corrections.append({
                'type': 'street_from_api_enforced',
                'message': 'Strasse aus SwissPost API übernommen',
                'old': street_name_raw,
                'new': final_street_name
            })
            street_name_raw = final_street_name
        if final_house_number and final_house_number != house_no_raw:
            corrections.append({
                'type': 'house_number_from_api_enforced',
                'message': 'Hausnummer aus SwissPost API übernommen',
                'old': house_no_raw,
                'new': final_house_number
            })
            house_no_raw = final_house_number

        # Bei USABLE: Zusatzlogik gemäß Anforderung (Street → Revalidate → City → Revalidate)
        if quality == 'USABLE':
            # 1) Street-Korrektur per Streets-API versuchen
            try:
                street_suggestion = await self.autocomplete_street(postcode_raw, street_name_raw)
            except Exception:
                street_suggestion = None

            if street_suggestion and street_suggestion != street_name_raw:
                corrections.append({
                    'type': 'street_corrected_after_usable',
                    'message': 'Strassenname via Street-Lookup nach USABLE verbessert',
                    'old': original_street_name,
                    'new': street_suggestion
                })
                street_name_raw = street_suggestion

            # Re-Validierung nach Street-Korrektur
            re_validation = await self.call_validation_api({
                'firstname': address.get('firstname', ''),
                'lastname': address.get('lastname', ''),
                'company': address.get('company', ''),
                'street_name': street_name_raw,
                'house_number': house_no_raw,
                'city': city_final,
                'postcode': postcode_raw
            })
            re_quality = re_validation.get('response', {}).get('quality', 'UNUSABLE')

            if re_quality in ('DOMICILE_CERTIFIED', 'CERTIFIED'):
                validation_result = re_validation
                quality = re_quality
            else:
                # 2) City-Korrektur: Ortsnamen aus ZIPs bestimmen und besten per Buchstaben-Überschneidung wählen
                city_choice = None
                try:
                    token = await self.token_manager.get_token()
                    async with httpx.AsyncClient() as client:
                        resp = await client.get(
                            f"{API_BASE_URL}/zips",
                            headers={"Authorization": f"Bearer {token}"},
                            params={"zipCity": postcode_raw, "type": "DOMICILE"},
                            timeout=10.0
                        )
                        if resp.status_code == 200:
                            zips = resp.json().get('zips', [])
                            candidates: List[str] = []
                            for entry in zips:
                                for cand in [entry.get('city18', ''), entry.get('city27', '')]:
                                    if cand:
                                        candidates.append(cand)
                            if candidates:
                                city_choice = self._pick_best_city_by_overlap(city_final, candidates)
                except Exception:
                    city_choice = None

                if city_choice and city_choice != city_final:
                    corrections.append({
                        'type': 'city_corrected_after_usable',
                        'message': 'Ort via ZIP-Lookup nach USABLE verbessert (Buchstaben-Überschneidung)',
                        'old': original_city,
                        'new': city_choice
                    })
                    city_final = city_choice

                # Zweite Re-Validierung nach City-Korrektur
                re_validation_2 = await self.call_validation_api({
                    'firstname': address.get('firstname', ''),
                    'lastname': address.get('lastname', ''),
                    'company': address.get('company', ''),
                    'street_name': street_name_raw,
                    'house_number': house_no_raw,
                    'city': city_final,
                    'postcode': postcode_raw
                })
                validation_result = re_validation_2
                quality = re_validation_2.get('response', {}).get('quality', quality)
        
        # Personendaten formatieren und Korrekturen hinzufügen
        firstname_raw = address.get('firstname', '')
        lastname_raw = address.get('lastname', '')
        company_raw = address.get('company', '')
        
        firstname_formatted = firstname_raw.title() if firstname_raw else ""
        lastname_formatted = lastname_raw.title() if lastname_raw else ""
        # Firmenname: Rechtsformen normalisieren, sonst unverändert lassen
        company_normalized = self.analyzer.normalize_company_legal_forms(company_raw) if company_raw else ""
        company_formatted = company_normalized
        
        # Personendaten-Korrekturen hinzufügen
        if firstname_formatted != firstname_raw and firstname_raw:
            corrections.append({
                'type': 'firstname_formatted',
                'message': 'Vorname formatiert',
                'old': firstname_raw,
                'new': firstname_formatted
            })
        
        if lastname_formatted != lastname_raw and lastname_raw:
            corrections.append({
                'type': 'lastname_formatted',
                'message': 'Nachname formatiert',
                'old': lastname_raw,
                'new': lastname_formatted
            })
        
        # Firmenname-Korrektur nur, wenn Rechtsform normalisiert wurde
        if company_raw and company_normalized != company_raw:
            corrections.append({
                'type': 'company_legal_form_normalized',
                'message': 'Rechtsform in Firmenname normalisiert',
                'old': company_raw,
                'new': company_normalized
            })
        
        # Korrigierte Ausgabe formatieren
        corrected_formatted = self.analyzer.format_corrected_output(
            street_name_raw, house_no_raw, city_final, postcode_raw,
            firstname_formatted, lastname_formatted, company_formatted
        )
        
        # Score berechnen (nach möglicher Re-Validierung)
        score = self.quality_to_score(quality)

        return {
            'status': 'success' if score >= 50 else 'failed',
            'quality': quality,
            'score': score,
            'corrections': corrections,
            'input': {
                'street': street_raw,
                'city': city_raw,
                'postcode': postcode_raw,
                'firstname': firstname_raw,
                'lastname': lastname_raw,
                'company': company_raw
            },
            'corrected': corrected_formatted,
            'validation': validation_result.get('response', {}),
            'has_corrections': len(corrections) > 0
        }
    
    async def enhanced_city_correction(self, zip_code: str, city_input: str) -> Optional[str]:
        """
        Erweiterte Stadt-Korrektur mit verschiedenen Suchstrategien
        """
        try:
            token = await self.token_manager.get_token()
            
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
                    return None
                
                data = response.json()
                zips = data.get('zips', [])
                
                if not zips:
                    return None
                
                # Verschiedene Suchstrategien
                city_lower = city_input.lower()
                
                # 1. Exakter Match (case-insensitive)
                for zip_entry in zips:
                    for candidate in [zip_entry.get('city18', ''), zip_entry.get('city27', '')]:
                        if candidate and candidate.lower() == city_lower:
                            return candidate
                
                # 2. "Startet mit" Match
                for zip_entry in zips:
                    for candidate in [zip_entry.get('city18', ''), zip_entry.get('city27', '')]:
                        if candidate and candidate.lower().startswith(city_lower):
                            return candidate
                
                # 3. "Enthält" Match
                for zip_entry in zips:
                    for candidate in [zip_entry.get('city18', ''), zip_entry.get('city27', '')]:
                        if candidate and city_lower in candidate.lower():
                            return candidate
                
                # 4. Ähnlichkeits-Score (niedrigere Schwelle)
                best_match = None
                best_score = 0.0
                
                for zip_entry in zips:
                    for candidate in [zip_entry.get('city18', ''), zip_entry.get('city27', '')]:
                        if candidate:
                            score = self.analyzer.similarity_score(city_input, candidate)
                            if score > best_score and score > 0.2:  # Niedrigere Schwelle
                                best_score = score
                                best_match = candidate
                
                return best_match
        
        except Exception as e:
            print(f"Enhanced city correction Fehler: {e}")
            return None
    
    async def autocomplete_zip(self, zip_code: str, city_input: str) -> Optional[str]:
        """
        Sucht korrekten Ortsnamen via ZIP-Autocomplete
        Wenn mehrere Orte: wähle den mit bester Übereinstimmung
        """
        try:
            token = await self.token_manager.get_token()
            
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
                    return None
                
                data = response.json()
                zips = data.get('zips', [])
                
                if not zips:
                    return None
                
                if len(zips) == 1:
                    # Nur ein Ort gefunden
                    return zips[0].get('city18') or zips[0].get('city27')
                
                # Mehrere Orte: besten Match finden
                best_match = None
                best_score = 0.0
                
                for zip_entry in zips:
                    city18 = zip_entry.get('city18', '')
                    city27 = zip_entry.get('city27', '')
                    
                    # Prüfe beide Varianten
                    for candidate in [city18, city27]:
                        if candidate:
                            # Prüfe zuerst auf exakten Match
                            if candidate.lower() == city_input.lower():
                                return candidate
                            
                            # Prüfe auf "startet mit" Match
                            if candidate.lower().startswith(city_input.lower()):
                                return candidate
                            
                            # Prüfe auf Ähnlichkeit
                            score = self.analyzer.similarity_score(city_input, candidate)
                            if score > best_score:
                                best_score = score
                                best_match = candidate
                
                # Wenn kein exakter oder "startet mit" Match gefunden, 
                # aber ein ähnlicher Match mit Score > 0.3
                if best_match and best_score > 0.3:
                    return best_match
                
                return best_match
        
        except Exception as e:
            print(f"ZIP Autocomplete Fehler: {e}")
            return None
    
    async def autocomplete_street(self, zip_code: str, street_input: str) -> Optional[str]:
        """Sucht korrekte Strassenschreibweise via Street-Autocomplete"""
        try:
            token = await self.token_manager.get_token()
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{API_BASE_URL}/streets",
                    headers={"Authorization": f"Bearer {token}"},
                    params={
                        "zip": zip_code,
                        "name": street_input
                    },
                    timeout=10.0
                )
                
                if response.status_code != 200:
                    return None
                
                data = response.json()
                print(f"DEBUG: Street API response: {data}")
                
                streets = data.get('streets', [])
                
                if not streets:
                    print(f"DEBUG: No streets found for {street_input} in {zip_code}")
                    return None
                
                # Prüfe ob streets eine Liste ist
                if not isinstance(streets, list):
                    print(f"DEBUG: Streets is not a list: {type(streets)} - {streets}")
                    return None
                
                # Prüfe ob der erste Eintrag ein Dictionary oder String ist
                if isinstance(streets[0], dict):
                    # Dictionary Format: {'name': 'Talstrasse'}
                    street_name = streets[0].get('name', '')
                elif isinstance(streets[0], str):
                    # String Format: 'Talstrasse'
                    street_name = streets[0]
                else:
                    print(f"DEBUG: Unexpected street entry format: {type(streets[0])} - {streets[0]}")
                    return None
                
                print(f"DEBUG: Found street name: {street_name}")
                return street_name
        
        except Exception as e:
            print(f"Street Autocomplete Fehler: {e}")
            return None
    
    async def autocomplete_house(self, zip_code: str, street_name: str, house_no: str) -> Optional[str]:
        """Validiert Hausnummer via House-Autocomplete"""
        try:
            token = await self.token_manager.get_token()
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{API_BASE_URL}/houses",
                    headers={"Authorization": f"Bearer {token}"},
                    params={
                        "zip": zip_code,
                        "streetname": street_name,
                        "number": house_no
                    },
                    timeout=10.0
                )
                
                if response.status_code != 200:
                    return None
                
                data = response.json()
                print(f"DEBUG: House API response: {data}")
                
                houses = data.get('houses', [])
                
                if not houses:
                    print(f"DEBUG: No houses found for {house_no} in {street_name}, {zip_code}")
                    return None
                
                # Prüfe ob houses eine Liste ist
                if not isinstance(houses, list):
                    print(f"DEBUG: Houses is not a list: {type(houses)} - {houses}")
                    return None
                
                # Prüfe ob der erste Eintrag ein Dictionary oder String ist
                if isinstance(houses[0], dict):
                    # Dictionary Format: {'number': '4'}
                    house_number = houses[0].get('number', '')
                elif isinstance(houses[0], str):
                    # String Format: '4'
                    house_number = houses[0]
                else:
                    print(f"DEBUG: Unexpected house entry format: {type(houses[0])} - {houses[0]}")
                    return None
                
                print(f"DEBUG: Found house number: {house_number}")
                return house_number
        
        except Exception as e:
            print(f"House Autocomplete Fehler: {e}")
            return None
    
    def _pick_best_city_by_overlap(self, original_city: str, candidates: List[str]) -> Optional[str]:
        """Wählt den besten Ortsnamen anhand Buchstaben-Überschneidung (Character-Overlap)."""
        if not candidates:
            return None
        best: Tuple[Optional[str], float] = (None, 0.0)
        for cand in candidates:
            score = self.analyzer.similarity_score(original_city, cand)
            if score > best[1]:
                best = (cand, score)
        return best[0]
    
    async def call_validation_api(self, data: Dict) -> Dict:
        """Finale Validierung mit Swisspost API"""
        try:
            token = await self.token_manager.get_token()
            
            request_body = {
                "addressee": {},
                "geographicLocation": {
                    "house": {
                        "street": data.get('street_name', ''),
                        "houseNumber": data.get('house_number', '')
                    },
                    "zip": {
                        "zip": str(data.get('postcode', '')),
                        "city": data.get('city', '')
                    }
                },
                "fullValidation": True
            }
            
            if data.get('firstname'):
                request_body['addressee']['firstName'] = data['firstname']
            if data.get('lastname'):
                request_body['addressee']['lastName'] = data['lastname']
            if data.get('company'):
                request_body['addressee']['companyName'] = data['company']
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{API_BASE_URL}/addresses/validation",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json"
                    },
                    json=request_body,
                    timeout=15.0
                )
                
                if response.status_code == 200:
                    return {
                        'status': 'success',
                        'response': response.json()
                    }
                else:
                    return {
                        'status': 'error',
                        'http_status': response.status_code,
                        'message': response.text
                    }
        
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }
    
    @staticmethod
    def quality_to_score(quality: str) -> int:
        """Konvertiert Quality zu Score"""
        quality_map = {
            'DOMICILE_CERTIFIED': 100,
            'CERTIFIED': 100,
            'VERIFIED': 90,
            'USABLE': 50,
            'COMPROMISED': 60,
            'UNUSABLE': 0
        }
        return quality_map.get(quality.upper(), 0)
    
    async def run(self):
        """Server starten"""
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )


async def main():
    agent = SmartAddressAgent()
    await agent.run()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())