from __future__ import annotations

import re
from datetime import date, timedelta
from dateutil import parser as dateparser
from sqlalchemy.orm import Session

from .models import Member, Shift

STATUS_EMOJI = {"accepted": "✓", "rejected": "✗", "pending": "?"}


def parse_date(text: str) -> date:
    text = text.strip()
    lower = text.lower()

    if lower in ("sunday", "next sunday"):
        today = date.today()
        days_ahead = (6 - today.weekday()) % 7
        if days_ahead == 0 or lower == "next sunday":
            days_ahead += 7
        return today + timedelta(days=days_ahead)

    if lower == "this sunday":
        today = date.today()
        days_ahead = (6 - today.weekday()) % 7
        if days_ahead == 0:
            days_ahead = 7
        return today + timedelta(days=days_ahead)

    if re.match(r"^\d{4}-\d{2}-\d{2}$", text):
        return date.fromisoformat(text)

    return dateparser.parse(text, dayfirst=True).date()


def handle_command(text: str, db: Session) -> str:
    parts = text.strip().split()
    if not parts:
        return help_text()

    verb = parts[0].upper()

    if verb == "HELP":
        return help_text()

    if verb == "ADD":
        if len(parts) >= 2 and parts[1].upper() == "MEMBER":
            return add_member(parts[2:], db)
        return add_shift(parts[1:], db)

    if verb == "REMOVE":
        if len(parts) >= 2 and parts[1].upper() == "MEMBER":
            return remove_member(parts[2:], db)
        return remove_shift(parts[1:], db)

    if verb == "ROSTER":
        return get_roster(parts[1:], db)

    if verb == "MEMBERS":
        return list_members(db)

    if verb == "NOTIFY":
        return "Use NOTIFY <date> — e.g. NOTIFY sunday"

    return f"Unknown command '{verb}'. Type HELP."


def prepare_invites(parts: list, db: Session) -> tuple[str, list[tuple]]:
    """Returns (summary, [(phone, name, role, date_str, shift), ...]) for NOTIFY."""
    if not parts:
        return "Usage: NOTIFY <date>  e.g. NOTIFY sunday", []
    try:
        roster_date = parse_date(" ".join(parts))
    except Exception:
        return "Couldn't parse that date. Try YYYY-MM-DD or 'sunday'.", []

    shifts = (
        db.query(Shift)
        .join(Member)
        .filter(Shift.date == roster_date)
        .order_by(Shift.role, Member.name)
        .all()
    )
    if not shifts:
        return f"No roster found for {roster_date.strftime('%d %b %Y')}.", []

    invites = []
    no_number = []
    date_str = roster_date.strftime("%A, %d %b %Y")

    for shift in shifts:
        m = shift.member
        if m.phone:
            shift.status = "pending"
            invites.append((m.phone, m.name, shift.role, date_str, shift))
        else:
            no_number.append(m.name)

    db.commit()

    summary = f"Sending invites to {len(invites)} member(s) for {roster_date.strftime('%d %b %Y')}."
    if no_number:
        summary += f"\nNo number on file for: {', '.join(no_number)}"
    if not invites:
        summary = "No members with phone numbers found for that date."
    return summary, invites


def handle_rsvp(phone: str, accepted: bool, db: Session) -> tuple[str, str | None]:
    """
    Process an Accept/Reject button tap.
    Returns (reply_to_member, manager_notification_or_None).
    """
    member = db.query(Member).filter(Member.phone == phone).first()
    if not member:
        return "Couldn't find your details. Please contact the roster manager.", None

    shift = (
        db.query(Shift)
        .filter(Shift.member_id == member.id, Shift.status == "pending")
        .order_by(Shift.date)
        .first()
    )
    if not shift:
        return "No pending shift found — it may already be confirmed.", None

    shift.status = "accepted" if accepted else "rejected"
    db.commit()

    date_str = shift.date.strftime("%A, %d %b %Y")
    if accepted:
        reply = f"Great, confirmed! See you on {date_str} for {shift.role}. ✓"
        manager_msg = f"{member.name} accepted {shift.role} on {date_str} ✓"
    else:
        reply = f"Understood, you've declined {shift.role} on {date_str}. ✗\nThe roster manager has been notified."
        manager_msg = f"{member.name} declined {shift.role} on {date_str} ✗"

    return reply, manager_msg


def add_member(parts: list, db: Session) -> str:
    if not parts:
        return "Usage: ADD MEMBER <name> [<phone>]\nExample: ADD MEMBER John +27821234567"
    name = parts[0].title()
    phone = parts[1] if len(parts) > 1 else None
    if phone:
        phone = phone.lstrip("+")
        phone = f"whatsapp:+{phone}" if not phone.startswith("whatsapp:") else phone

    existing = db.query(Member).filter(Member.name == name).first()
    if existing:
        if phone:
            existing.phone = phone
            db.commit()
            return f"Updated {name}'s number to {phone.replace('whatsapp:', '')}."
        return f"{name} is already a member."

    db.add(Member(name=name, phone=phone))
    db.commit()
    line = f"Added {name}"
    if phone:
        line += f" ({phone.replace('whatsapp:', '')})"
    return line + "."


def remove_member(parts: list, db: Session) -> str:
    if not parts:
        return "Usage: REMOVE MEMBER <name>"
    name = parts[0].title()
    member = db.query(Member).filter(Member.name == name).first()
    if not member:
        return f"No member named {name}."
    db.delete(member)
    db.commit()
    return f"Removed {name} and all their shifts."


def add_shift(parts: list, db: Session) -> str:
    if len(parts) < 3:
        return "Usage: ADD <name> <role> <date>\nExample: ADD John Ushers sunday"
    name = parts[0].title()
    role = parts[1].title()
    try:
        shift_date = parse_date(" ".join(parts[2:]))
    except Exception:
        return f"Couldn't parse date '{' '.join(parts[2:])}'. Try YYYY-MM-DD or 'sunday'."

    member = db.query(Member).filter(Member.name == name).first()
    if not member:
        return f"No member named {name}. Add them first:\nADD MEMBER {name} <phone>"

    exists = db.query(Shift).filter(
        Shift.member_id == member.id,
        Shift.role == role,
        Shift.date == shift_date,
    ).first()
    if exists:
        return f"{name} is already on {role} for {shift_date.strftime('%d %b %Y')}."

    db.add(Shift(member_id=member.id, role=role, date=shift_date))
    db.commit()
    return f"Added {name} to {role} on {shift_date.strftime('%d %b %Y')}."


def remove_shift(parts: list, db: Session) -> str:
    if len(parts) < 3:
        return "Usage: REMOVE <name> <role> <date>"
    name = parts[0].title()
    role = parts[1].title()
    try:
        shift_date = parse_date(" ".join(parts[2:]))
    except Exception:
        return "Couldn't parse date. Try YYYY-MM-DD."

    member = db.query(Member).filter(Member.name == name).first()
    if not member:
        return f"No member named {name}."

    shift = db.query(Shift).filter(
        Shift.member_id == member.id,
        Shift.role == role,
        Shift.date == shift_date,
    ).first()
    if not shift:
        return f"No shift: {name} / {role} / {shift_date.strftime('%d %b %Y')}."

    db.delete(shift)
    db.commit()
    return f"Removed {name} from {role} on {shift_date.strftime('%d %b %Y')}."


def get_roster(parts: list, db: Session) -> str:
    if not parts:
        return "Usage: ROSTER <date>  e.g. ROSTER sunday"
    try:
        roster_date = parse_date(" ".join(parts))
    except Exception:
        return "Couldn't parse that date. Try YYYY-MM-DD or 'sunday'."

    shifts = (
        db.query(Shift)
        .join(Member)
        .filter(Shift.date == roster_date)
        .order_by(Shift.role, Member.name)
        .all()
    )
    if not shifts:
        return f"No roster for {roster_date.strftime('%d %b %Y')}."

    lines = [f"*Roster — {roster_date.strftime('%A, %d %b %Y')}*"]
    current_role = None
    for shift in shifts:
        if shift.role != current_role:
            current_role = shift.role
            lines.append(f"\n_{current_role}_")
        emoji = STATUS_EMOJI.get(shift.status, " ") if shift.status else " "
        lines.append(f"  {emoji} {shift.member.name}")
    return "\n".join(lines)


def list_members(db: Session) -> str:
    members = db.query(Member).order_by(Member.name).all()
    if not members:
        return "No members yet.\nAdd one: ADD MEMBER <name> <phone>"
    lines = ["*Team Members*"]
    for m in members:
        phone = m.phone.replace("whatsapp:", "") if m.phone else "no number"
        lines.append(f"  • {m.name} ({phone})")
    return "\n".join(lines)


def help_text() -> str:
    return (
        "*Sunday Roster Bot*\n\n"
        "*Team*\n"
        "  ADD MEMBER <name> <phone>\n"
        "  REMOVE MEMBER <name>\n"
        "  MEMBERS\n\n"
        "*Shifts*\n"
        "  ADD <name> <role> <date>\n"
        "  REMOVE <name> <role> <date>\n"
        "  ROSTER <date>\n"
        "  NOTIFY <date>\n\n"
        "*Dates*: 2026-05-11 | 11 May | sunday"
    )
