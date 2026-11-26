"""Build calendar.ics (a subscribable iCalendar feed) from data/sessions.json.

Every session with a "start" (ISO datetime) or a Persian "date" becomes a
2-hour event. Run: python3 scripts/build_calendar.py -> writes calendar.ics.

The generated file follows RFC 5545 closely enough to be consumed by Google
Calendar, Apple Calendar, and similar clients:
  * all datetimes are emitted in UTC (``...Z``),
  * long lines are folded at 75 octets,
  * TEXT values are escaped,
  * each event has a stable UID so edits update instead of duplicating.
"""
import hashlib
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Repository root (this file lives in <root>/scripts/).
ROOT = Path(__file__).resolve().parent.parent

# Default length of a class session.
DURATION = timedelta(hours=2)

# Iran uses a fixed UTC+3:30 offset (no DST since 2022), so a static timezone
# is sufficient and avoids depending on the system tz database.
TEHRAN = timezone(timedelta(hours=3, minutes=30))

# First Jalali year of the course; used to infer the year when a session's
# "date" string does not include one.
COURSE_START_YEAR = 1405

# Persian month names mapped to their Jalali month number (1 = فروردین).
FA_MONTHS = {
    "فروردین": 1, "اردیبهشت": 2, "خرداد": 3,
    "تیر": 4, "مرداد": 5, "شهریور": 6,
    "مهر": 7, "آبان": 8, "آذر": 9,
    "دی": 10, "بهمن": 11, "اسفند": 12,
}


def fa_to_latin(text):
    """Convert Persian and Arabic-Indic digits in ``text`` to ASCII digits.

    Only digits are translated; letters and punctuation are left untouched so
    the result can be matched with regular expressions using ``\\d``.
    """
    trans = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
    return text.translate(trans)


def jalali_to_gregorian(jy, jm, jd):
    """Convert a Jalali (Solar Hijri) date to a Gregorian ``(year, month, day)``.

    Uses the widely used 33-year cycle arithmetic (the same approach as the
    common ``jdate``/``jalali_to_gregorian`` snippets). ``jy`` is the Jalali
    year, ``jm`` the month (1..12), and ``jd`` the day of month.
    """
    # Shift to an internal year count starting near the Gregorian epoch.
    jy += 1595

    # Day count from the epoch: whole 33-year cycles plus leap days.
    days = -355668 + (365 * jy) + ((jy // 33) * 8) + (((jy % 33) + 3) // 4) + jd

    # First 6 Jalali months have 31 days, the next 5 have 30 (Esfand has 29/30).
    days += (jm - 1) * 31 if jm < 7 else ((jm - 7) * 30) + 186

    # Convert the day count to a Gregorian year/month/day.
    gy = 400 * (days // 146097)  # 400-year Gregorian cycles
    days %= 146097
    if days > 36524:  # 100-year cycles (with the century non-leap correction)
        days -= 1
        gy += 100 * (days // 36524)
        days %= 36524
        if days >= 365:
            days += 1
    gy += 4 * (days // 1461)  # 4-year cycles
    days %= 1461
    if days > 365:  # remaining years inside the 4-year cycle
        gy += (days - 1) // 365
        days = (days - 1) % 365
    gd = days + 1

    # Month lengths for the resolved Gregorian year, accounting for leap years.
    is_leap = (gy % 4 == 0 and gy % 100 != 0) or (gy % 400 == 0)
    sal_a = [0, 31, 29 if is_leap else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    gm = 0
    while gm < 13 and gd > sal_a[gm]:
        gd -= sal_a[gm]
        gm += 1
    return gy, gm, gd


def parse_start(session):
    """Return the session start as an aware ``datetime`` in Tehran time.

    Resolution order:
      1. An explicit ``start`` field (ISO 8601). Naive values are assumed to be
         Tehran local time.
      2. A Persian ``date`` string such as ``"۲۳ مهر ساعت ۱۸:۰۰"``, optionally
         combined with a ``year`` field.

    Returns ``None`` when the session has neither a usable ``start`` nor a
    non-empty ``date``. Raises ``ValueError`` when a ``date`` is present but
    cannot be parsed (month, day, or hour missing).
    """
    # Preferred path: a machine-readable ISO datetime.
    if session.get("start"):
        dt = datetime.fromisoformat(session["start"])
        return dt if dt.tzinfo else dt.replace(tzinfo=TEHRAN)

    raw_date = (session.get("date") or "").strip()
    if not raw_date:
        return None

    # Normalize digits so the regexes below only need to handle ASCII digits.
    norm = fa_to_latin(raw_date)

    # Find which Persian month name appears in the string.
    month_name, month_num = next(
        ((m, n) for m, n in FA_MONTHS.items() if m in norm), (None, None)
    )
    if not month_num:
        raise ValueError(f"Could not find Persian month in date: {raw_date!r}")

    # Day is the number immediately before the month name (e.g. "۲۳ مهر").
    day_match = re.search(rf"(\d{{1,2}})\s*{month_name}", norm)
    if not day_match:
        raise ValueError(f"Could not parse day from date: {raw_date!r}")
    day = int(day_match.group(1))

    # Time is written as "ساعت ۱۸" or "ساعت ۱۸:۳۰".
    time_match = re.search(r"ساعت\s*(\d{1,2})(?::(\d{2}))?", norm)
    if not time_match:
        raise ValueError(f"Could not parse hour from date: {raw_date!r}")
    hour = int(time_match.group(1))
    minute = int(time_match.group(2) or 0)

    # Course started in Mehr 1405; months 1..6 roll over into 1406.
    year = session.get("year") or (COURSE_START_YEAR if month_num >= 7 else COURSE_START_YEAR + 1)
    gy, gm, gd = jalali_to_gregorian(year, month_num, day)
    return datetime(gy, gm, gd, hour, minute, tzinfo=TEHRAN)


def esc(text):
    """Escape a value for use in an iCalendar TEXT property.

    Backslash must be escaped first so the escapes added afterwards are not
    double-escaped.
    """
    # RFC 5545 §3.3.11: escape backslash, ; , and newlines in TEXT values.
    return text.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")


def fold(line):
    """Fold a logical iCalendar line into physical lines of at most 75 octets.

    Per RFC 5545 §3.1, continuation lines begin with a single space. Folding
    happens per character (not per byte) so multi-byte Persian letters are
    never split in the middle of a code point.
    """
    # RFC 5545 §3.1: lines max 75 octets; continuation lines start with a space.
    # Split on characters, not bytes, so Persian (multi-byte) letters never break.
    out, cur = [], ""
    for ch in line:
        # Continuation lines lose one octet to the leading space, so they may
        # hold at most 74 octets of content.
        if len((cur + ch).encode()) > (75 if not out else 74):
            out.append(cur)
            cur = ""
        cur += ch
    out.append(cur)
    return "\r\n ".join(out)


def utc(dt):
    """Format ``dt`` as an iCalendar UTC timestamp (``YYYYMMDDTHHMMSSZ``)."""
    return dt.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def build(sessions, now):
    """Build and return the complete iCalendar document as a string.

    ``sessions`` is the parsed contents of ``data/sessions.json`` and ``now``
    is the generation timestamp used for each event's ``DTSTAMP``. Sessions
    without a parsable start time are skipped. The result uses CRLF line
    endings and ends with a trailing CRLF, as required by RFC 5545.
    """
    # Calendar-level properties: metadata plus hints for clients that support
    # periodic refresh (REFRESH-INTERVAL / X-PUBLISHED-TTL).
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//data-course//sessions//FA",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:دورهٔ مهندسی داده و هوش مصنوعی",
        "X-WR-TIMEZONE:Asia/Tehran",
        "REFRESH-INTERVAL;VALUE=DURATION:PT1H",
        "X-PUBLISHED-TTL:PT1H",
    ]
    for s in sessions:
        start = parse_start(s)
        if not start:
            continue

        # Build the optional description lines shown in calendar clients.
        details = []
        if s.get("speaker"):
            details.append("مدرس: " + s["speaker"])
        if s.get("join"):
            details.append("ورود به کلاس: " + s["join"])

        # UID must stay the same across builds so a changed time updates the
        # event instead of creating a duplicate. Keyed on "type" (e.g. جلسه ۱۱).
        uid = hashlib.sha1(s["type"].encode()).hexdigest()[:16] + "@data-course"
        lines += [
            "BEGIN:VEVENT",
            "UID:" + uid,
            "DTSTAMP:" + utc(now),
            "DTSTART:" + utc(start),
            "DTEND:" + utc(start + DURATION),
            "SUMMARY:" + esc(s["type"] + ": " + s["title"]),
        ]
        if details:
            lines.append("DESCRIPTION:" + esc("\n".join(details)))

        # Reuse the join link as both the location and the event URL.
        if s.get("join"):
            lines += ["LOCATION:" + esc(s["join"]), "URL:" + s["join"]]

        # A display alarm 30 minutes before the event start.
        lines += [
            "BEGIN:VALARM",
            "TRIGGER:-PT30M",
            "ACTION:DISPLAY",
            "DESCRIPTION:" + esc(s["type"] + ": " + s["title"]),
            "END:VALARM",
            "END:VEVENT",
        ]
    lines.append("END:VCALENDAR")

    # Fold every logical line and join with CRLF; terminate with a final CRLF.
    return "\r\n".join(fold(l) for l in lines) + "\r\n"


if __name__ == "__main__":
    sessions = json.loads((ROOT / "data/sessions.json").read_text(encoding="utf-8"))
    ics = build(sessions, datetime.now(timezone.utc))

    # Count sessions that should produce an event, for the self-check below.
    expected = sum(1 for s in sessions if s.get("start") or (s.get("date") or "").strip())

    # self-check: every physical line fits in 75 octets and events are balanced
    assert all(len(l.encode()) <= 75 for l in ics.split("\r\n")), "line too long"
    assert ics.count("BEGIN:VEVENT") == ics.count("END:VEVENT") == expected
    assert ics.count("BEGIN:VALARM") == ics.count("END:VALARM") == expected

    # Write with newline="" so Python does not translate the CRLF line endings.
    (ROOT / "calendar.ics").write_text(ics, encoding="utf-8", newline="")
    print(f"calendar.ics: {ics.count('BEGIN:VEVENT')} event(s)")
