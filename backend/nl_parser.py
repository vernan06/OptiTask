import re
from datetime import datetime, timedelta

_WEEKDAYS = {
    "monday": 0, "mon": 0,
    "tuesday": 1, "tue": 1, "tues": 1,
    "wednesday": 2, "wed": 2,
    "thursday": 3, "thu": 3, "thur": 3, "thurs": 3,
    "friday": 4, "fri": 4,
    "saturday": 5, "sat": 5,
    "sunday": 6, "sun": 6,
}

_CATEGORIES = ["work", "study", "personal", "home", "finance", "health", "general"]

def _today_iso() -> str:
    return datetime.now().date().isoformat()

def _now_time() -> str:
    """Returns current time as HH:MM"""
    return datetime.now().strftime("%H:%M")

def _parse_date(text: str) -> str:
    t = text.lower()

    today = datetime.now().date()

    # Check for "yesterday" - this should be rejected
    if "yesterday" in t:
        return "__PAST__"

    if "today" in t:
        return today.isoformat()

    if any(x in t for x in ["tomorrow", "tmr", "tmrw", "tommow"]):
        return (today + timedelta(days=1)).isoformat()

    m = re.search(r"\bin\s+(\d+)\s+days?\b", t)
    if m:
        days = int(m.group(1))
        if days < 0:
            return "__PAST__"
        return (today + timedelta(days=days)).isoformat()

    # next week [day] - means the same day in the FOLLOWING week (7+ days ahead)
    for name, num in _WEEKDAYS.items():
        if re.search(rf"\bnext\s+week\s+{re.escape(name)}\b", t):
            cur = today.weekday()
            # Calculate days to that weekday in the NEXT week
            ahead = (num - cur) % 7
            if ahead == 0:
                ahead = 7
            ahead += 7  # Add a full week
            return (today + timedelta(days=ahead)).isoformat()

    # next monday / monday - means THIS coming occurrence
    for name, num in _WEEKDAYS.items():
        if re.search(rf"\bnext\s+{re.escape(name)}\b", t) or re.search(rf"\b{re.escape(name)}\b", t):
            cur = today.weekday()
            ahead = (num - cur) % 7
            if ahead == 0:
                ahead = 7
            return (today + timedelta(days=ahead)).isoformat()

    return today.isoformat()

def validate_date_time(deadline: str, start_time: str) -> dict:
    """
    Validates that the deadline and start_time are not in the past.
    Returns {"valid": True} or {"valid": False, "error": "message"}
    """
    if deadline == "__PAST__":
        return {"valid": False, "error": "Cannot schedule tasks for past dates (like yesterday)"}

    today_iso = _today_iso()
    now_time = _now_time()

    # Check if deadline is in the past
    if deadline and deadline < today_iso:
        return {"valid": False, "error": f"Cannot schedule tasks for past date ({deadline}). Today is {today_iso}"}

    # If deadline is today and a start_time is provided, check if it's in the past
    if deadline == today_iso and start_time:
        if start_time < now_time:
            return {"valid": False, "error": f"Cannot schedule tasks for past time ({start_time}). Current time is {now_time}"}

    return {"valid": True}

def _parse_time(text: str) -> str:
    """
    Supports:
      - 2pm, 2 pm, 2:30pm
      - 14:00
      - 9am
    Returns "HH:MM" or "" if not found
    """
    t = text.lower()

    # 14:00 / 9:05
    m = re.search(r"\b([01]?\d|2[0-3]):([0-5]\d)\b", t)
    if m:
        hh = int(m.group(1))
        mm = int(m.group(2))
        return f"{hh:02d}:{mm:02d}"

    # 2pm / 2:30pm / 12am
    m = re.search(r"\b(\d{1,2})(?::(\d{2}))?\s*(am|pm)\b", t)
    if m:
        hh = int(m.group(1))
        mm = int(m.group(2) or 0)
        ap = m.group(3)
        if ap == "pm" and hh != 12:
            hh += 12
        if ap == "am" and hh == 12:
            hh = 0
        if 0 <= hh <= 23 and 0 <= mm <= 59:
            return f"{hh:02d}:{mm:02d}"

    return ""

def _parse_duration_mins(text: str) -> int | None:
    """
    Supports:
      - 90m
      - 1h
      - 2h30m
      - 1h 15m
    """
    t = text.lower()

    # 2h30m / 2h 30m / 2h
    m = re.search(r"\b(\d+)\s*h(?:\s*(\d+)\s*m)?\b", t)
    if m:
        h = int(m.group(1))
        mm = int(m.group(2) or 0)
        return h * 60 + mm

    m = re.search(r"\b(\d+)\s*m\b", t)
    if m:
        return int(m.group(1))

    return None

def _strip_tokens(text: str, tokens: list[str]) -> str:
    t = text
    for tok in tokens:
        t = re.sub(tok, " ", t, flags=re.IGNORECASE)
    return " ".join(t.split()).strip()

def parse_command(text: str) -> dict:
    """
    Returns a dict:
      name, category, priority, deadline, start_time, duration, status, valid, error
    """
    raw = (text or "").strip()
    t = raw.lower()

    out = {
        "name": "",
        "category": "general",
        "priority": 3,
        "deadline": _today_iso(),
        "start_time": "",
        "duration": 30,
        "status": 0,
        "valid": False,
        "error": None,
    }

    # Priority: P1..P5
    pm = re.search(r"\bp([1-5])\b", t)
    if pm:
        out["priority"] = int(pm.group(1))

    # Duration
    d = _parse_duration_mins(t)
    if d is not None and d > 0:
        out["duration"] = d

    # Date
    out["deadline"] = _parse_date(t)

    # Time
    st = _parse_time(t)
    if st:
        out["start_time"] = st

    # Check for past date EARLY and reject
    validation = validate_date_time(out["deadline"], out["start_time"])
    if not validation["valid"]:
        out["valid"] = False
        out["error"] = validation["error"]
        return out

    # Category
    for c in _CATEGORIES:
        if re.search(rf"\b{re.escape(c)}\b", t):
            out["category"] = c
            break

    # Strip recognized tokens to get name
    strip_patterns = [
        r"\bp[1-5]\b",
        r"\b\d+\s*h(?:\s*\d+\s*m)?\b",
        r"\b\d+\s*m\b",
        r"\b(today|tomorrow|tmr|tmrw|tommow|yesterday)\b",  # Added yesterday and tommow typo
        r"\bin\s+\d+\s+days?\b",
        r"\bnext\s+(monday|mon|tuesday|tue|tues|wednesday|wed|thursday|thu|thur|thurs|friday|fri|saturday|sat|sunday|sun)\b",
        r"\b(monday|mon|tuesday|tue|tues|wednesday|wed|thursday|thu|thur|thurs|friday|fri|saturday|sat|sunday|sun)\b",
        r"\b([01]?\d|2[0-3]):([0-5]\d)\b",
        r"\b(\d{1,2})(?::(\d{2}))?\s*(am|pm)\b",
        r"\bfor\b",  # Strip "for" as in "set a meeting for yesterday"
        r"\bat\b",   # Strip "at" as in "at 2 pm"
    ] + [rf"\b{re.escape(c)}\b" for c in _CATEGORIES]

    name = _strip_tokens(raw, strip_patterns)

    out["name"] = name
    out["valid"] = len(name) > 0

    return out