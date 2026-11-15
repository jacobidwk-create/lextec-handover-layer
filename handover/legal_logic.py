"""Deterministic legal branch selection, not a merits or validity decision.

Every unresolved/exceptional branch is referred. Dates remain conservative
screening dates; see full_report.md 3.5a and sources/legal_logic_review.md.
"""
from datetime import timedelta
from .schema import Case, Reason


def objection_record_complete(c: Case) -> bool:
    served = c.value('document_received_date')
    filed = c.value('objection_date')
    return (c.value('document_type') == 'payment_order'
            and c.value('objection_filed') is True
            and c.value('service_disputed') is False
            and served is not None and filed is not None
            and served <= filed <= served + timedelta(days=10)
            and c.value('objection_recipient') in ('server', 'office')
            and (c.value('objection_recipient') != 'server' or filed == served)
            and c.value('objection_scope') == 'full')


def inheritance_start(c: Case):
    """The day the three months for disclaiming start (areas.inheritance_start)."""
    from .areas import inheritance_start as start
    return start(c)


def legal_referrals(c: Case):
    """Return (reasons, urgent). Referral is a scope policy, not an adverse finding."""
    reasons, urgent = [], False

    def refer(detail, *, time_sensitive=False):
        nonlocal urgent
        reasons.append(Reason('R13-legal-review', detail))
        urgent |= time_sensitive

    if c.value('jurisdiction') in ('other', 'international'):
        refer('Jurisdiction or applicable law requires review beyond the Zurich domestic scope.')
    if c.value('case_complexity') is True:
        refer('Multiple proceedings, representation or capacity requires individual review.')
    if c.value('other_official_deadline') is True:
        refer('An additional official deadline requires immediate review.', time_sensitive=True)
    if 'debt_collection' in c.areas:
        if c.value('earlier_official_document') is True:
            refer('Earlier official proceedings cannot be excluded by the latest private letter.', time_sensitive=True)
        if c.value('service_disputed') is True:
            refer('Service and the start of the objection period require review.', time_sensitive=True)
        if c.value('objection_filed') is True:
            served, filed = c.value('document_received_date'), c.value('objection_date')
            if (c.value('objection_recipient') in ('creditor', 'other')
                    or c.value('objection_scope') == 'partial'
                    or served and filed and (filed < served or filed > served + timedelta(days=10))
                    or c.value('objection_recipient') == 'server' and served and filed and filed != served):
                refer('Timing, recipient or scope of the reported objection needs review; no validity is assumed.', time_sensitive=True)
    # Declining an inheritance: the rules of the four gates are in rules.py.
    # Register entries: the rules of the flow are in rules.py.
    return reasons, urgent


def legal_context(c, today):
    """Bound the answer to the branch supported by the collected facts."""
    from .deadlines import add_months
    out = ["Only general information. No finding that any claim, objection, disclaimer or non-disclosure request is legally valid."]
    # Late fees are not drafted by the model: their result comes from late_fees.py.
    # Inheritance and late fees are not drafted by the model: fixed results.
    # Register entries are not drafted by the model either (register.py).
    return out
