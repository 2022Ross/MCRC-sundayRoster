# Sunday Roster Bot

Manage your Sunday service roster via WhatsApp. Text commands to a Twilio number to add members, assign shifts, view the roster, and send reminders.

---

## Prerequisites

- Python 3.8+
- A free [Twilio account](https://www.twilio.com/try-twilio)
- [ngrok](https://ngrok.com/download) (free, for local development)

---

## Setup

### 1. Clone & install

```bash
cd sunday-roster
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env` with your Twilio credentials:

```
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
```

Find your `ACCOUNT_SID` and `AUTH_TOKEN` on the [Twilio Console](https://console.twilio.com/) dashboard.

The `TWILIO_WHATSAPP_FROM` number above is Twilio's shared WhatsApp sandbox number — use it as-is for testing.

### 3. Start the server

```bash
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

### 4. Expose it with ngrok

In a second terminal:

```bash
ngrok http 8000
```

Copy the `https://` URL it gives you (e.g. `https://abc123.ngrok.io`).

### 5. Connect Twilio WhatsApp Sandbox

1. Go to [Twilio Console → Messaging → Try it out → Send a WhatsApp message](https://console.twilio.com/us1/develop/sms/try-it-out/whatsapp-learn)
2. Follow the instructions to join the sandbox (send the join code from your WhatsApp)
3. Under **Sandbox Settings**, set the webhook URL to:
   ```
   https://abc123.ngrok.io/webhook
   ```
   Method: `HTTP POST`
4. Save.

You're live. Text the sandbox number from WhatsApp.

---

## Commands

### Team management

| Command | Example |
|---|---|
| `ADD MEMBER <name> <phone>` | `ADD MEMBER John +27821234567` |
| `REMOVE MEMBER <name>` | `REMOVE MEMBER John` |
| `MEMBERS` | Lists all members and numbers |

Phone numbers must include the country code (e.g. `+27` for South Africa).

### Shift management

| Command | Example |
|---|---|
| `ADD <name> <role> <date>` | `ADD John Ushers 2026-05-11` |
| `REMOVE <name> <role> <date>` | `REMOVE John Ushers 2026-05-11` |
| `ROSTER <date>` | `ROSTER sunday` |
| `NOTIFY <date>` | `NOTIFY 2026-05-11` |

**NOTIFY** sends a personal WhatsApp reminder to every member rostered on that date (only works if they have a phone number on file).

### Date formats

- `2026-05-11` (ISO — recommended)
- `11 May` or `11 May 2026`
- `11/05/2026`
- `sunday` / `next sunday` (computes the upcoming Sunday)

### HELP

Text `HELP` at any time to get the command list back.

---

## Example session

```
You:  ADD MEMBER Sarah +27831234567
Bot:  Added Sarah (+27831234567).

You:  ADD MEMBER Mike +27841234567
Bot:  Added Mike (+27841234567).

You:  ADD Sarah Worship 2026-05-11
Bot:  Added Sarah to Worship on 11 May 2026.

You:  ADD Mike Sound 2026-05-11
Bot:  Added Mike to Sound on 11 May 2026.

You:  ROSTER 2026-05-11
Bot:  *Roster — Monday, 11 May 2026*
      _Sound_
        • Mike
      _Worship_
        • Sarah

You:  NOTIFY 2026-05-11
Bot:  Sending reminders to 2 member(s) for 11 May 2026.
      (Sarah & Mike each receive a personal WhatsApp reminder)
```

---

## Going to production

When you're ready to move beyond the sandbox:

1. Apply for a [WhatsApp Business API number](https://www.twilio.com/whatsapp/request-access) via Twilio.
2. Replace `TWILIO_WHATSAPP_FROM` in `.env` with your approved number.
3. Deploy the app to any host that can run Python (Railway, Render, Fly.io — all have free tiers).
4. Update the Twilio webhook URL to your production URL.
