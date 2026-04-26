"""
Layered contact-sharing detection for RFQ chat (phones, obfuscated emails, off-platform phrases).

Scoring policy:
  score >= 90  -> blocked
  score 70-89  -> confirm_required
  score 45-69 -> warn
  score < 45  -> clean
Thread context can block split contact attempts (no confirm path for digit-split bursts when rules fire).
"""
from __future__ import annotations

import re
import unicodedata
from typing import Any

_ZW_RE = re.compile(r"[\u200b-\u200d\ufeff\u2060\u00ad]")
_FW_AT = "\uff20"
_FW_DOT = "\uff0e"
_TRANSLATE_FW = str.maketrans({_FW_AT: "@", _FW_DOT: ".", "\u3002": ".", "\uff61": "."})

_WORD_DIGITS = {
    "zero": "0",
    "one": "1",
    "two": "2",
    "three": "3",
    "four": "4",
    "five": "5",
    "six": "6",
    "seven": "7",
    "eight": "8",
    "nine": "9",
}
_WORD_DIGIT_RE = re.compile(r"\b(" + "|".join(_WORD_DIGITS) + r")\b", re.I)

_GSTIN_RE = re.compile(
    r"\b\d{2}[A-Z]{5}\d{4}[A-Z][A-Z0-9][Z][A-Z0-9]\b",
    re.I,
)

_EMAIL_LIKE_RE = re.compile(
    r"[a-z0-9][a-z0-9._+-]{0,48}@[a-z0-9][a-z0-9.-]{0,40}\.[a-z]{2,12}",
    re.I,
)

_CONTACT_PHRASES = (
    "call me",
    "whatsapp",
    "whats app",
    "watsapp",
    "contact me",
    "mail me",
    "email me",
    "reach me",
    "ping me",
    "my number",
    "my contact",
    "my mobile",
    "my cell",
    "share number",
    "send number",
    "gimme a call",
    "give me a call",
    "ring me",
    "text me on",
    "message me on",
    "my telegram",
    "my instagram",
    "on telegram",
    "on instagram",
    "on signal",
    "on snap",
    "personal number",
    "personal email",
    "work email",
    "outside platform",
    "off the platform",
    "talk outside",
    "reach me at",
    "text me",
    "dm me",
    "inbox me",
    "drop a mail",
    "contact me outside",
    "off platform",
    "not on platform",
    "direct line",
    "face time",
    "google meet",
    "teams meeting",
    "ms teams",
    "webex",
    "skype me",
    "viber",
    "line id",
    "we chat",
    "zoom link",
    "meeting link",
    "my handle",
    "gmail is",
    "gmail com",
    "outlook com",
    "proton me",
    "yandex",
)

# Public URLs or deep links that usually mean moving conversation off B2B chat.
_OFFPLATFORM_LINK_SUBSTRS = (
    "t.me/",
    "t.me@",
    "wa.me/",
    "wa.link",
    "api.whatsapp",
    "telegram.me",
    "telegram.dog",
    "instagram.com",
    "instagr.am",
    "ig.me/",
    "linktr.ee",
    "lnk.bio",
    "bio.link",
    "m.me/",  # messenger
    "messenger.com",
    "signal.me",
    "snapchat.com",
    "twitter.com",
    "x.com/",
    "bsky.app",
    "linkedin.com/in",
    "fb.com/",
    "facebook.com/",
    "threads.net",
    "meet.google",
    "zoom.us",
    "us02web.zoom",
    "teams.microsoft",
    "web.whatsapp",
)

_DOMAIN_HINTS = ("gm.", "gml.", "gmail", "yahoo", "yhoo", "outlook", "hotmail")


def normalize_message(text: str) -> dict[str, str]:
    if text is None:
        text = ""
    raw = text
    t = unicodedata.normalize("NFKC", raw)
    buf = []
    for ch in t:
        if ch.isdigit() and not ("0" <= ch <= "9"):
            try:
                buf.append(str(unicodedata.digit(ch)))
            except (TypeError, ValueError):
                buf.append(ch)
        else:
            buf.append(ch)
    t = "".join(buf)
    t = t.translate(_TRANSLATE_FW)
    t = _ZW_RE.sub("", t)
    t = t.casefold()
    collapsed = re.sub(r"[\s\u00a0]+", " ", t).strip()
    joined = re.sub(r"[^a-z0-9@.+-]", "", collapsed)
    return {
        "raw": raw,
        "normalized": t,
        "collapsed": collapsed,
        "joined": joined,
    }


def _words_to_digit_spaced(collapsed: str) -> str:
    def repl(m: re.Match) -> str:
        return _WORD_DIGITS[m.group(1).lower()]

    return _WORD_DIGIT_RE.sub(repl, collapsed)


def _apply_at_dot_words(s: str) -> str:
    s = re.sub(r"\bdot\b", ".", s, flags=re.I)
    s = re.sub(r"\bat\b", "@", s, flags=re.I)
    s = re.sub(r"\s*\.\s*", ".", s)
    s = re.sub(r"\s*@\s*", "@", s)
    return s


def _strip_gstin_regions(s: str) -> str:
    return _GSTIN_RE.sub(" ", s)


def _digit_only(s: str) -> str:
    return re.sub(r"\D", "", s)


def _indian_mobile_10(d10: str) -> bool:
    return len(d10) == 10 and d10.isdigit() and d10[0] in "6789"


def _has_valid_mobile_window(digits: str) -> bool:
    n = len(digits)
    for length in (13, 12, 11, 10):
        for i in range(0, max(0, n - length + 1)):
            chunk = digits[i : i + length]
            if length == 10 and _indian_mobile_10(chunk):
                return True
            if length == 12 and chunk.startswith("91") and _indian_mobile_10(chunk[2:]):
                return True
            if length == 11 and chunk.startswith("0") and _indian_mobile_10(chunk[1:]):
                return True
    return False


def _message_to_digit_stream(text: str) -> str:
    """Digits only, same normalisation as single-message phone scan (for thread concatenation)."""
    if not (text or "").strip():
        return ""
    pack = normalize_message(text)
    collapsed = pack["collapsed"]
    wd = _words_to_digit_spaced(collapsed)
    d = _digit_only(_strip_gstin_regions(wd))
    if d:
        return d
    return _digit_only(_strip_gstin_regions(collapsed))


def _build_same_user_concatenated_digits(same_sender_recent: list[str], new_text: str, *, max_msgs: int = 36) -> str:
    """
    Join digit streams from recent same-user lines + the new line (chronological).
    Used to catch phone numbers split across many short messages.
    """
    if not same_sender_recent and not (new_text or "").strip():
        return ""
    body = (same_sender_recent or []) + [new_text or ""]
    if len(body) > max_msgs:
        body = body[-max_msgs:]
    return "".join(_message_to_digit_stream(m) for m in body if m is not None)


def _max_validated_indian_phone_in_digit_stream(stream: str) -> tuple[int, list[str], list[str], list[str]]:
    """Return 90 with reasons if a valid IN mobile appears as a substring; else 0. Duplicates one branch of _score_phones."""
    if not stream:
        return 0, [], [], []
    n = len(stream)
    seen: set[str] = set()
    for length in (13, 12, 11, 10):
        for i in range(0, n - length + 1):
            chunk = stream[i : i + length]
            if chunk in seen:
                continue
            ok = (
                (length == 10 and _indian_mobile_10(chunk))
                or (length == 12 and chunk.startswith("91") and _indian_mobile_10(chunk[2:]))
                or (length == 11 and chunk.startswith("0") and _indian_mobile_10(chunk[1:]))
            )
            if not ok:
                continue
            seen.add(chunk)
            return (
                90,
                ["phone_validated", "phone_split_or_concat_thread"],
                ["PHONE"],
                [chunk[:12] + "…" if len(chunk) > 12 else chunk],
            )
    return 0, [], [], []


def _score_phones(collapsed: str, joined: str) -> tuple[int, list[str], list[str], list[str]]:
    reasons: list[str] = []
    types: list[str] = []
    spans: list[str] = []
    score = 0

    wd = _words_to_digit_spaced(collapsed)
    streams = [
        _digit_only(_strip_gstin_regions(wd)),
        _digit_only(_strip_gstin_regions(collapsed)),
        _digit_only(_strip_gstin_regions(joined)),
    ]
    seen: set[str] = set()
    validated = False
    for stream in streams:
        if not stream:
            continue
        n = len(stream)
        for length in range(13, 9, -1):
            for i in range(0, n - length + 1):
                chunk = stream[i : i + length]
                if chunk in seen:
                    continue
                ok = False
                if length == 10 and _indian_mobile_10(chunk):
                    ok = True
                elif length == 12 and chunk.startswith("91") and _indian_mobile_10(chunk[2:]):
                    ok = True
                elif length == 11 and chunk.startswith("0") and _indian_mobile_10(chunk[1:]):
                    ok = True
                if ok:
                    seen.add(chunk)
                    validated = True
                    score = max(score, 90)
                    reasons.append("phone_validated")
                    types.append("PHONE")
                    spans.append(chunk[:12] + "…" if len(chunk) > 12 else chunk)

    if not validated:
        for stream in streams:
            if len(stream) >= 10 and not _has_valid_mobile_window(stream):
                if stream.startswith("27") and len(stream) <= 15:
                    continue
                oscore = 70 if len(stream) >= 12 else 50
                score = max(score, oscore)
                reasons.append("phone_obfuscated_digits" + (":long" if oscore == 70 else ""))
                types.append("PHONE")
                spans.append(stream[:16])
                break

    return score, reasons, types, spans


def _score_emails(collapsed: str) -> tuple[int, list[str], list[str], list[str]]:
    reasons: list[str] = []
    types: list[str] = []
    spans: list[str] = []
    score = 0
    atdot = _apply_at_dot_words(collapsed)
    for m in _EMAIL_LIKE_RE.finditer(atdot):
        email = m.group(0)
        dom = email.split("@", 1)[-1].lower()
        for hint in _DOMAIN_HINTS:
            if dom.startswith(hint):
                reasons.append(f"email_domain:{hint}")
                break
        score = max(score, 90)
        reasons.append("email_pattern")
        types.append("EMAIL")
        spans.append(email[:96])

    if score == 0 and "@" in atdot and re.search(r"@\s*[a-z0-9.-]{2,}\.", atdot):
        score = max(score, 70)
        reasons.append("at_dot_structure")
        types.append("EMAIL")

    return score, reasons, types, spans


def _score_phrases(collapsed: str) -> tuple[int, list[str], list[str]]:
    """Any off-platform phrase alone should reach at least warn tier (>=45)."""
    reasons: list[str] = []
    types: list[str] = []
    score = 0
    low = collapsed.lower()
    hits = 0
    for p in _CONTACT_PHRASES:
        if p in low:
            hits += 1
            reasons.append(f"phrase:{p}")
            types.append("CONTACT_PHRASE")
    if hits:
        score = 48 + max(0, hits - 1) * 15
    # Messaging / off-platform channels: must be able to block alone.
    _hard_channels = (
        "whatsapp",
        "whats app",
        "watsapp",
        "api.whatsapp",
        "web.whatsapp",
        "web.telegram",
        "telegram",
        "t.me/",
        "t.me@",
        "wa.me",
        "wa.link",
        "signal app",
        "snapchat",
        "snap chat",
        "instagram",
        " insta@",
        " insta id",
        " insta is",
        "face time",
        "facetime",
        " meet.google",
        "zoom.us",
        "us02web.zoom",
        "teams.microsoft",
    )
    if any(h in low for h in _hard_channels):
        score = max(score, 92)
    return score, reasons, types


def _score_offplatform_links_and_protocols(collapsed: str) -> tuple[int, list[str], list[str]]:
    score = 0
    reasons: list[str] = []
    types: list[str] = []
    low = collapsed.lower()
    for s in _OFFPLATFORM_LINK_SUBSTRS:
        if s in low:
            score = max(score, 92)
            reasons.append(f"offplatform_url:{s[:28]}")
            types.append("OFFPLATFORM_LINK")
            return score, reasons, types
    if re.search(r"\bmailto:\s*[^\s@]+@", collapsed, re.I):
        score = max(score, 90)
        reasons.append("mailto_link")
        types.append("EMAIL")
    if re.search(r"(?<![a-z])tel:\s*\+?[\d\s-]{4,16}\b", collapsed, re.I):
        score = max(score, 90)
        reasons.append("tel_link")
        types.append("PHONE")
    if re.search(r"@[a-z0-9_]{3,20}\.t\.me\b", low):
        score = max(score, 90)
        reasons.append("telegram_username_link")
        types.append("TELEGRAM_HANDLE")
    return score, reasons, types


def _business_safe_context(collapsed: str) -> bool:
    keys = ("gstin", "gst ", "hsn", "invoice amount", "quantity", "units", "delivery in", "order quantity")
    cl = collapsed.lower()
    return any(k in cl for k in keys)


def analyze_contact(
    text: str,
    *,
    prior_thread_flags: int = 0,
    same_sender_recent: list[str] | None = None,
) -> dict[str, Any]:
    pack = normalize_message(text or "")
    collapsed = pack["collapsed"]
    joined = pack["joined"]

    reasons: list[str] = []
    detected_types: list[str] = []
    detected_spans: list[str] = []
    score = 0

    if prior_thread_flags == 1:
        score += 12
        reasons.append("prior_flags:1")
    elif prior_thread_flags >= 2:
        bonus = min(40, (prior_thread_flags - 1) * 20)
        score += bonus
        reasons.append(f"prior_flags:{prior_thread_flags}")

    if same_sender_recent is not None:
        thread_d = _build_same_user_concatenated_digits(same_sender_recent, text or "")
        thread_ts = 0
        if len(thread_d) >= 10:
            tts, tr, tt, tsp = _max_validated_indian_phone_in_digit_stream(thread_d)
            thread_ts = tts
            if tts:
                score = max(score, tts)
                reasons.extend(tr)
                detected_types.extend(tt)
                detected_spans.extend(tsp)
        if not thread_ts and len((same_sender_recent or []) + [text or ""]) >= 2:
            line_parts = (same_sender_recent or []) + [text or ""]
            take = line_parts[-6:]
            run = 0
            for piece in reversed(take):
                col2 = re.sub(r"[\s-]+", "", normalize_message(piece or "")["collapsed"])
                if 1 <= len(col2) <= 6 and col2.isdigit():
                    run += 1
                else:
                    break
            tlen = len(thread_d)
            if (run >= 3 and 9 <= tlen <= 24) or (run >= 2 and 10 <= tlen <= 24):
                score = max(score, 90)
                reasons.append("phone_digit_split_burst_suspect")
                detected_types.append("PHONE")

    ps, pr, pt, pspans = _score_phones(collapsed, joined)
    score = max(score, ps)
    reasons.extend(pr)
    detected_types.extend(pt)
    detected_spans.extend(pspans)

    es, er, et, espans = _score_emails(collapsed)
    score = max(score, es)
    reasons.extend(er)
    detected_types.extend(et)
    detected_spans.extend(espans)

    if es == 0 and re.search(r"\bdot\b", collapsed, re.I) and re.search(r"\b(com|net|org|in|co)\b", collapsed, re.I):
        score = max(score, 55)
        reasons.append("obfuscated_domain_words")
        detected_types.append("EMAIL")

    phs, phr, pht = _score_phrases(collapsed)
    score += phs
    reasons.extend(phr)
    detected_types.extend(pht)

    ols, olr, olt = _score_offplatform_links_and_protocols(collapsed)
    score = max(score, ols)
    reasons.extend(olr)
    detected_types.extend(olt)

    if _business_safe_context(collapsed) and score < 90:
        score = max(0, score - 35)
        reasons.append("business_context_discount")

    score = int(min(200, max(0, score)))

    if score >= 90:
        status = "blocked"
    elif score >= 70:
        status = "confirm_required"
    elif score >= 45:
        status = "warn"
    else:
        status = "clean"

    display_message = (text or "").strip()
    normalized_preview = collapsed[:200]

    if status == "blocked":
        display_message = "[Message hidden due to contact-sharing attempt]"

    return {
        "status": status,
        "score": score,
        "reasons": reasons,
        "detected_types": list(dict.fromkeys(detected_types)),
        "detected_spans": detected_spans[:24],
        "normalized_preview": normalized_preview,
        "display_message": display_message,
    }


def redact_contact_content(text: str, findings: dict[str, Any]) -> str:
    if findings.get("status") == "blocked":
        return "[Message hidden due to contact-sharing attempt]"
    out = text or ""
    out = _EMAIL_LIKE_RE.sub("[contact hidden]", out)
    out = re.sub(r"\b\+?\d[\d\s.-]{8,14}\d\b", "[contact hidden]", out)
    return out
