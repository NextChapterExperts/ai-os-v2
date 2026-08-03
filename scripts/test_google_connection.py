#!/usr/bin/env python3
"""Google-Verbindung testen — OAuth + Kalender, Gmail, Drive (interaktiv)."""
from __future__ import annotations

import datetime
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from core.google import auth
from core.google.scopes import GOOGLE_SCOPES

SCOPES = [
    GOOGLE_SCOPES["calendar.readonly"],
    GOOGLE_SCOPES["gmail.readonly"],
    GOOGLE_SCOPES["drive"],
    GOOGLE_SCOPES["spreadsheets"],
    GOOGLE_SCOPES["tasks"],
]


def main() -> int:
    print("=" * 60)
    print(" Google OAuth — AI-OS V2 Verbindungstest ".center(60, "="))
    print("=" * 60)
    print(f"Secrets: {auth.SECRETS_DIR}")

    try:
        creds = auth.load_credentials(SCOPES, "token.json", interactive=True)
    except FileNotFoundError as exc:
        print(f"\n[FEHLER] {exc}")
        return 1
    except Exception as exc:
        print(f"\n[FEHLER] Autorisierung fehlgeschlagen: {exc}")
        return 1

    print("[ERFOLG] OAuth-Token gültig.")
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError

    try:
        print("\n--- Kalender (nächste 5 Termine) ---")
        cal = build("calendar", "v3", credentials=creds)
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        events = (
            cal.events()
            .list(calendarId="primary", timeMin=now, maxResults=5, singleEvents=True, orderBy="startTime")
            .execute()
            .get("items", [])
        )
        for ev in events:
            start = ev["start"].get("dateTime", ev["start"].get("date"))
            print(f"- [{start}] {ev.get('summary', '(Kein Titel)')}")

        print("\n--- Gmail (5 neueste) ---")
        gmail = build("gmail", "v1", credentials=creds)
        msgs = gmail.users().messages().list(userId="me", maxResults=5).execute().get("messages", [])
        for ref in msgs or []:
            msg = gmail.users().messages().get(userId="me", id=ref["id"], format="metadata").execute()
            print(f"- {msg.get('snippet', '')[:80]}…")

        print("\n--- Drive (5 neueste Dateien) ---")
        drive = build("drive", "v3", credentials=creds)
        files = drive.files().list(pageSize=5, fields="files(id,name)").execute().get("files", [])
        for f in files or []:
            print(f"- {f['name']} ({f['id']})")

    except HttpError as exc:
        print(f"\n[FEHLER] Google API: {exc}")
        return 1

    print("\n" + "=" * 60)
    print(" Test erfolgreich ".center(60, "="))
    return 0


if __name__ == "__main__":
    sys.exit(main())
