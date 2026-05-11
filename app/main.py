import os
from typing import Optional

from fastapi import Depends, FastAPI, Form, Response
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session
from twilio.twiml.messaging_response import MessagingResponse

from .commands import handle_command, handle_rsvp, prepare_invites
from .database import Base, engine, get_db
from .whatsapp import send_message, send_shift_invite

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Sunday Roster Bot")


@app.get("/", response_class=PlainTextResponse)
def health():
    return "Sunday Roster Bot is running."


@app.post("/webhook")
async def webhook(
    From: str = Form(...),
    Body: str = Form(...),
    ButtonPayload: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    twiml = MessagingResponse()

    # Accept / Reject — button tap or plain text reply
    body_upper = Body.strip().upper()
    if ButtonPayload in ("accept", "reject"):
        pass  # handled below
    elif body_upper.startswith("ACCEPT"):
        ButtonPayload = "accept"
    elif body_upper.startswith("REJECT"):
        ButtonPayload = "reject"

    if ButtonPayload in ("accept", "reject"):
        reply, manager_msg = handle_rsvp(From, ButtonPayload == "accept", db)
        if manager_msg:
            manager_phone = os.getenv("MANAGER_PHONE")
            if manager_phone:
                mp = manager_phone if manager_phone.startswith("whatsapp:") else f"whatsapp:{manager_phone}"
                try:
                    send_message(mp, manager_msg)
                except Exception as e:
                    reply += f"\n[Manager alert failed: {e}]"
        twiml.message(reply)
        return Response(content=str(twiml), media_type="application/xml")

    # NOTIFY command — send interactive shift invites
    parts = Body.strip().split()
    verb = parts[0].upper() if parts else ""

    if verb == "NOTIFY":
        summary, invites = prepare_invites(parts[1:], db)
        for phone, name, role, date_str, _shift in invites:
            try:
                send_shift_invite(phone, name, role, date_str)
            except Exception as e:
                summary += f"\nFailed to reach {phone.replace('whatsapp:', '')}: {e}"
        twiml.message(summary)

    else:
        twiml.message(handle_command(Body.strip(), db))

    return Response(content=str(twiml), media_type="application/xml")
