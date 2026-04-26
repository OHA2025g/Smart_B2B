"""
RFQ and quote validity windows (presentation / procurement demo).

- RFQ validUntil defaults to createdAt + 7 days if not stored.
- Quote quoteValidUntil defaults to createdAt + 5 days if not stored.
- isExpired is computed: not accepted/closed (RFQ) or not accepted/rejected (quote).
"""
from __future__ import annotations

import datetime
from typing import Any

RFQ_VALID_DAYS = 7
QUOTE_VALID_DAYS = 5


def _as_utc_dt(value: Any) -> datetime.datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime.datetime):
        return value.replace(tzinfo=None) if value.tzinfo else value
    if isinstance(value, str):
        try:
            s = value.replace("Z", "+00:00")
            dt = datetime.datetime.fromisoformat(s)
            return dt.replace(tzinfo=None) if dt.tzinfo else dt
        except ValueError:
            return None
    return None


def compute_rfq_valid_until(created_at: Any, stored: Any = None) -> datetime.datetime | None:
    if stored:
        dt = _as_utc_dt(stored)
        if dt:
            return dt
    c = _as_utc_dt(created_at)
    if not c:
        return None
    return c + datetime.timedelta(days=RFQ_VALID_DAYS)


def compute_quote_valid_until(created_at: Any, stored: Any = None) -> datetime.datetime | None:
    if stored:
        dt = _as_utc_dt(stored)
        if dt:
            return dt
    c = _as_utc_dt(created_at)
    if not c:
        return None
    return c + datetime.timedelta(days=QUOTE_VALID_DAYS)


def rfq_is_expired(now: datetime.datetime, valid_until: datetime.datetime | None, status: str | None) -> bool:
    if not valid_until or status in ("accepted", "closed", "rejected"):
        return False
    return now > valid_until


def quote_is_expired(now: datetime.datetime, valid_until: datetime.datetime | None, status: str | None) -> bool:
    if not valid_until or status in ("accepted", "rejected"):
        return False
    return now > valid_until


def enrich_rfq_dict(doc: dict | None, now: datetime.datetime | None = None) -> dict | None:
    """Mutates serialized or raw rfq dict in place with validUntil, isExpired (ISO dates preserved by caller)."""
    if doc is None:
        return None
    now = now or datetime.datetime.utcnow()
    created = doc.get("createdAt")
    vu = compute_rfq_valid_until(created, doc.get("validUntil"))
    status = doc.get("status")
    expired = rfq_is_expired(now, vu, status)
    if vu:
        doc["validUntil"] = vu.isoformat() if hasattr(vu, "isoformat") else vu
    doc["isExpired"] = expired
    return doc


def enrich_quote_dict(doc: dict | None, now: datetime.datetime | None = None) -> dict | None:
    if doc is None:
        return None
    now = now or datetime.datetime.utcnow()
    created = doc.get("createdAt")
    qvu = compute_quote_valid_until(created, doc.get("quoteValidUntil"))
    status = doc.get("status")
    expired = quote_is_expired(now, qvu, status)
    if qvu:
        doc["quoteValidUntil"] = qvu.isoformat() if hasattr(qvu, "isoformat") else qvu
    doc["isQuoteExpired"] = expired
    # delivery_days: average across line items for API convenience
    items = doc.get("items") or []
    if items:
        days = [it.get("deliveryDays") for it in items if it.get("deliveryDays") is not None]
        doc["deliveryDays"] = round(sum(days) / len(days), 1) if days else None
    else:
        doc["deliveryDays"] = None
    return doc
