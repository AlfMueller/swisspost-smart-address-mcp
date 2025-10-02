#!/usr/bin/env python3
"""
Test Swisspost API Credentials
"""

import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

# Get credentials
client_id = os.getenv('SWISSPOST_CLIENT_ID')
client_secret = os.getenv('SWISSPOST_CLIENT_SECRET')

# Check credentials
if not client_id or client_id == 'your_actual_client_id_here':
    print('❌ SWISSPOST_CLIENT_ID nicht konfiguriert')
    sys.exit(1)

if not client_secret or client_secret == 'your_actual_client_secret_here':
    print('❌ SWISSPOST_CLIENT_SECRET nicht konfiguriert')
    sys.exit(1)

print('✅ Credentials gefunden')
print(f'   Client ID: {client_id[:8]}...')
print(f'   Client Secret: {client_secret[:8]}...')
