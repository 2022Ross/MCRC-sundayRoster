# Sunday Roster Bot

WhatsApp bot for managing MCRC Sunday service rosters via Twilio.

## Stack
- Python 3.8, FastAPI, SQLAlchemy, SQLite (`roster.db`)
- Twilio WhatsApp sandbox (`+14155238886`)
- Serveo for tunneling (not ngrok)

## How to start

**Terminal 1 — server:**
```bash
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

**Terminal 2 — Serveo tunnel:**
```bash
ssh -R 80:localhost:8000 serveo.net
```
The URL changes on every reconnect. Update the Twilio webhook each time:
- console.twilio.com → Messaging → Try it out → Send a WhatsApp message → Sandbox Settings
- Set webhook to `https://<new-serveo-url>/webhook`

## Environment variables (`.env`)
- `TWILIO_ACCOUNT_SID` — Twilio account SID
- `TWILIO_AUTH_TOKEN` — Twilio auth token
- `TWILIO_WHATSAPP_FROM` — `whatsapp:+14155238886` (sandbox number)
- `MANAGER_PHONE` — receives RSVP notifications (`+61435534424` — Ross's number)
- `DATABASE_URL` — defaults to `sqlite:///./roster.db`

## Key files
- `app/main.py` — FastAPI app, webhook endpoint
- `app/commands.py` — all command handlers and RSVP logic
- `app/whatsapp.py` — Twilio messaging (plain + interactive invite)
- `app/models.py` — Member and Shift SQLAlchemy models
- `app/database.py` — DB setup

## Commands the bot supports
- `ADD MEMBER <name> <phone>` / `REMOVE MEMBER <name>` / `MEMBERS`
- `ADD <name> <role> <date>` / `REMOVE <name> <role> <date>`
- `ROSTER <date>` — view roster with RSVP status
- `NOTIFY <date>` — send Accept/Reject invite to all rostered members
- `HELP`

## Phone number format
- Stored in DB as `whatsapp:+XXXXXXXXXXXX` (e.g. `whatsapp:+61401346015`)
- When adding members, the bot automatically prefixes with `whatsapp:+`
- Strip `whatsapp:` when displaying to users

## RSVP flow
1. `NOTIFY <date>` sends each rostered member an interactive WhatsApp message with Accept ✓ / Reject ✗ buttons (via Twilio Content API template `sunday_roster_shift_reminder_v1`)
2. If the interactive template fails, falls back to plain text asking them to reply ACCEPT or REJECT
3. Member taps button or texts ACCEPT/REJECT → webhook receives it → shift status updates → MANAGER_PHONE is notified
4. Shift statuses: `None` → `pending` → `accepted` / `rejected`

## Twilio Content API template
- Friendly name: `sunday_roster_shift_reminder_v1`
- Auto-created on first NOTIFY if it doesn't exist
- Template SID is cached in memory only — lost on server restart (harmless, just re-fetches on next use)

## Known gotchas
- **Serveo URL changes every reconnect** — always update Twilio webhook after restarting Serveo
- **Sandbox opt-in** — members must text the Twilio join code to `+14155238886` before they can receive messages
- **Interactive buttons may not work on sandbox** — plain text fallback (ACCEPT/REJECT) always works
- **`.env.example` is missing `MANAGER_PHONE`** — needs to be added

## Current members (as of 2026-05-11)
| Name | Phone |
|------|-------|
| Houlder | +61401346015 |

## Sending messages directly via script
```python
import os
os.chdir("/Users/ross/Documents/VS/sunday-roster")
from dotenv import load_dotenv
load_dotenv("/Users/ross/Documents/VS/sunday-roster/.env")
from app.whatsapp import send_message, send_shift_invite

# Plain message
send_message("whatsapp:+61401346015", "Your message here")

# Interactive invite with Accept/Reject buttons
send_shift_invite("whatsapp:+61401346015", "Houlder", "Host at PFPC", "Sunday, 11 May 2026")
```
