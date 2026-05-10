from __future__ import annotations

import json
import os
from typing import Optional

from twilio.rest import Client

TEMPLATE_FRIENDLY_NAME = "sunday_roster_shift_reminder_v1"
_template_sid: Optional[str] = None


def _client() -> Client:
    return Client(os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN"))


def send_message(to: str, body: str) -> None:
    _client().messages.create(
        from_=os.getenv("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886"),
        to=to,
        body=body,
    )


def _get_or_create_template() -> str:
    global _template_sid
    if _template_sid:
        return _template_sid

    client = _client()

    for content in client.content.v1.contents.list():
        if content.friendly_name == TEMPLATE_FRIENDLY_NAME:
            _template_sid = content.sid
            return _template_sid

    from twilio.rest.content.v1.content import ContentList

    actions = [
        ContentList.QuickReplyAction({"title": "Accept ✓", "id": "accept"}),
        ContentList.QuickReplyAction({"title": "Reject ✗", "id": "reject"}),
    ]
    quick_reply = ContentList.TwilioQuickReply({
        "body": "Hi {{1}}! You're rostered as *{{2}}* this *{{3}}*. Can you make it?",
        "actions": actions,
    })
    types = ContentList.Types({"twilio/quick-reply": quick_reply})
    request = ContentList.ContentCreateRequest({
        "friendly_name": TEMPLATE_FRIENDLY_NAME,
        "language": "en",
        "types": types,
    })

    content = client.content.v1.contents.create(content_create_request=request)
    _template_sid = content.sid
    return _template_sid


def send_shift_invite(to: str, name: str, role: str, date_str: str) -> None:
    try:
        template_sid = _get_or_create_template()
        _client().messages.create(
            content_sid=template_sid,
            content_variables=json.dumps({"1": name, "2": role, "3": date_str}),
            from_=os.getenv("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886"),
            to=to,
        )
    except Exception:
        # Fallback to plain text if interactive message fails
        send_message(
            to,
            f"Hi {name}! You're rostered as *{role}* this *{date_str}*. "
            f"Can you make it?\n\nReply *ACCEPT* or *REJECT*.",
        )
