"""Deadline computation. Pure date arithmetic, no model involved.

All deadlines are computed CONSERVATIVELY: the earliest date on which the
deadline could end. Rules that only extend a deadline (end on a weekend or
holiday, debt enforcement holidays) are deliberately ignored, so the system
can only err towards "more urgent". The exact date is for the human expert.
"""
from __future__ import annotations

import calendar
from datetime import date, timedelta

from . import config
from .schema import Case, Deadline
from .areas import register_objection_open
from .legal_logic import inheritance_start, objection_record_complete


def _easter(year: int) -> date:
    a, b, c = year % 19, year // 100, year % 100
    d, e = b // 4, b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = c // 4, c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month, day = divmod(h + l - 7 * m + 114, 31)
    return date(year, month, day + 1)


def zurich_holidays(year: int) -> set[date]:
    """Public holidays in the Canton of Zurich (to be verified by the legal lead)."""
    e = _easter(year)
    return {
        date(year, 1, 1), date(year, 1, 2),
        e - timedelta(days=2), e + timedelta(days=1),      # Good Friday, Easter Monday
        date(year, 5, 1),
        e + timedelta(days=39), e + timedelta(days=50),    # Ascension, Whit Monday
        date(year, 8, 1), date(year, 12, 25), date(year, 12, 26),
    }


def is_working_day(d: date) -> bool:
    return d.weekday() < 5 and d not in zurich_holidays(d.year)


def working_days_left(today: date, due: date) -> int:
    """Working days after today up to and including the due date.

    0 means the deadline ends today; -1 means it may already have passed.
    """
    if due < today:
        return -1
    n, d = 0, today
    while d < due:
        d += timedelta(days=1)
        n += is_working_day(d)
    return n


def add_months(d: date, months: int) -> date:
    y, m = divmod(d.month - 1 + months, 12)
    y, m = d.year + y, m + 1
    return date(y, m, min(d.day, calendar.monthrange(y, m)[1]))


def compute_deadlines(case: Case, today: date) -> list[Deadline]:
    out: list[Deadline] = []

    def add(key, label, basis, due, done):
        out.append(Deadline(label, basis, due, working_days_left(today, due), bool(done), key))

    received = case.value("document_received_date")
    if case.value("document_type") == "payment_order" and received:
        add("objection", "Objection to the payment order (Rechtsvorschlag)", "Art. 74 SchKG",
            received + timedelta(days=config.OBJECTION_DAYS),
            objection_record_complete(case))

    # Declining an inheritance: three months from the start that fits how the person
    # became an heir (Art. 567 ZGB), and one month for a public inventory (Art. 580).
    start = inheritance_start(case)
    if start:
        declared = case.value("disclaimer_filed") is True
        add("disclaimer", "Disclaimer of the inheritance (Ausschlagung)", "Art. 567 ZGB",
            add_months(start, config.DISCLAIMER_MONTHS), declared)
        add("inventory", "Request for a public inventory", "Art. 580 ZGB",
            add_months(start, 1), declared)

    # Register entries: if no objection was raised and the ten days from service are
    # still running, the objection is still possible (urgent notice, rules.py). A period
    # that has passed is not listed: the result says what remains.
    served = case.value("register_service_date")
    if served and register_objection_open(case):
        add("register_objection", "Objection to the payment order behind the register entry",
            "Art. 74 SchKG", served + timedelta(days=config.OBJECTION_DAYS), False)

    return out
