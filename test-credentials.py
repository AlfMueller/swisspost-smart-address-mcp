#!/usr/bin/env python3
"""
Kurzer Credential-Check für SwissPost OAuth, damit start-mcp-server-and-proxy.bat
einen einfachen Vorabtest ausführen kann.

Exit-Code 0 bei Erfolg, !=0 bei Fehler.
"""
import os
import sys
import asyncio
import json
from typing import Optional

import httpx
from dotenv import load_dotenv

OAUTH_TOKEN_URL = "https://api.post.ch/OAuth/token"


def get_env(name: str) -> Optional[str]:
    value = os.getenv(name)
    if value is not None and isinstance(value, str):
        value = value.strip()
    return value or None


async def fetch_token(client_id: str, client_secret: str, scope: str) -> str:
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(
            OAUTH_TOKEN_URL,
            data={
                "grant_type": "client_credentials",
                "client_id": client_id,
                "client_secret": client_secret,
                "scope": scope,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        token = data.get("access_token")
        if not token:
            raise RuntimeError("Kein access_token in OAuth-Antwort")
        return token


async def main() -> int:
    load_dotenv(override=True)

    client_id = get_env("SWISSPOST_CLIENT_ID")
    client_secret = get_env("SWISSPOST_CLIENT_SECRET")
    scope = get_env("SWISSPOST_SCOPE")

    missing = [name for name, val in (
        ("SWISSPOST_CLIENT_ID", client_id),
        ("SWISSPOST_CLIENT_SECRET", client_secret),
        ("SWISSPOST_SCOPE", scope),
    ) if not val]

    if missing:
        print(json.dumps({
            "status": "error",
            "message": "Fehlende Umgebungsvariablen",
            "missing": missing,
        }, ensure_ascii=False))
        return 2

    try:
        token = await fetch_token(client_id, client_secret, scope)  # noqa: F841
        print(json.dumps({
            "status": "ok",
            "message": "Credentials gültig",
        }, ensure_ascii=False))
        return 0
    except Exception as e:
        print(json.dumps({
            "status": "error",
            "message": f"OAuth fehlgeschlagen: {e}",
        }, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))


