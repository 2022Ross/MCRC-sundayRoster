# Sunday Roster Bot

WhatsApp bot for managing MCRC Sunday service rosters via Twilio.

## Deployment (Railway — live 24/7)
- **Web URL:** `https://web-production-e05434.up.railway.app`
- **Webhook:** `https://web-production-e05434.up.railway.app/webhook` (set in Twilio Console)
- **GitHub:** `https://github.com/2022Ross/MCRC-sundayRoster.git`
- Railway auto-deploys on every `git push` to master — no manual step needed
- Local server and Serveo tunnel are no longer needed

## Stack
- Python 3.12, FastAPI, SQLAlchemy, PostgreSQL (Railway)
- Twilio WhatsApp sandbox (`+14155238886`)

## Environment variables (set in Railway dashboard)
- `TWILIO_ACCOUNT_SID` — Twilio account SID
- `TWILIO_AUTH_TOKEN` — Twilio auth token
- `TWILIO_WHATSAPP_FROM` — `whatsapp:+14155238886` (sandbox number)
- `MANAGER_PHONE` — `+61435534424` (Ross — receives RSVP notifications)
- `DATABASE_URL` — set automatically by Railway PostgreSQL plugin

## Key files
- `app/main.py` — FastAPI app, webhook endpoint
- `app/commands.py` — all command handlers and RSVP logic
- `app/whatsapp.py` — Twilio messaging (plain + interactive invite)
- `app/models.py` — Member and Shift SQLAlchemy models
- `app/database.py` — DB setup (handles PostgreSQL URL conversion for Railway)

## Commands the bot supports
- `ADD MEMBER <name> <phone>` / `REMOVE MEMBER <name>` / `MEMBERS`
- `ADD <name> <role> <date>` / `REMOVE <name> <role> <date>`
- `ROSTER <date>` — view roster with RSVP status
- `NOTIFY <date>` — send Accept/Reject invite to all rostered members
- `HELP`

## Phone number format
- Stored in DB as `whatsapp:+XXXXXXXXXXXX` (e.g. `whatsapp:+61460446241`)
- When adding members, the bot automatically prefixes with `whatsapp:+`
- Strip `whatsapp:` when displaying to users

## RSVP flow
1. `NOTIFY <date>` sends each rostered member an interactive WhatsApp message with Accept ✓ / Reject ✗ buttons (via Twilio Content API template `mcrc_roster_invite_v1`)
2. Template body: "Hi {{name}}, this is MCRC. You're rostered as *{{role}}* this *{{date}}*. Can you make it?"
3. If the interactive template fails, falls back to plain text asking them to reply ACCEPT or REJECT
4. Member taps button or texts ACCEPT/REJECT → webhook receives it → shift status updates → MANAGER_PHONE is notified
5. Shift statuses: `None` → `pending` → `accepted` / `rejected`

## Twilio Content API template
- Friendly name: `mcrc_roster_invite_v1`
- Auto-created on first NOTIFY if it doesn't exist
- Template SID is cached in memory only — lost on server restart (harmless, re-fetches on next use)

## Sandbox opt-in (IMPORTANT)
Every person who needs to receive or send messages must first text the join code to `+14155238886` on WhatsApp.
- Find the join code: console.twilio.com → Messaging → Try it out → Send a WhatsApp message
- Yves ✓ | Ross (manager) ✓
- Any new member must opt in before NOTIFY will reach them

## Current members
| Name | Phone |
|------|-------|
| Yves | +61460446241 |
| Blessing | +61401346015 |

## Known gotchas
- **Sandbox opt-in** — all recipients must join the sandbox or they won't receive messages
- **Interactive buttons may not work on sandbox** — plain text fallback (ACCEPT/REJECT) always works
- **PostgreSQL URL** — Railway provides `postgres://` but SQLAlchemy needs `postgresql+psycopg2://` — handled in `database.py`
