"""Legal issues: what the established facts of a case actually raise.

A legal source belongs in a briefing only if the case raises the question the
source is about. "The case is in the area debt collection" is not enough: a
person in distress who mentioned a letter has not raised the question whether
collection fees are owed.

An issue is a named legal question with a test on the established facts
(plain Python, no model). Each issue has one of three states in a case:

  raised      the facts that make the question arise are established
  open        the case is in the issue's area, but a fact needed to tell is
              still missing; the briefing names what is missing
  not raised  the facts show that the question does not arise

Statutes and court decisions are attached to issues (sources/README.md) and
are shown only for raised issues. A thin case therefore gets a briefing that
says what is unknown, without case law.

DRAFT: the list of issues and their tests are to be reviewed by the legal lead.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .schema import Case, Decision, Status
from .legal_logic import objection_record_complete


@dataclass(frozen=True)
class Issue:
    id: str
    area: str
    title: dict            # {"de": ..., "en": ...}
    needs: tuple           # facts that must be established before the test can be applied
    test: Callable         # (case, decision) -> bool, applied once all needed facts are known
    statutes: tuple = ()   # keys in sources/corpus.json
    # Optional: (case) -> names of further facts that are still missing before the test
    # can tell. Used where the needed facts depend on an earlier answer.
    pending: Callable | None = None


_CHARGES = ("interest_charge", "reminder_fee", "collection_costs")


def _charges_claimed(case: Case) -> bool:
    """Late fees: at least one additional charge is established as claimed."""
    return any(case.value(n) not in (None, "none") for n in _CHARGES)


def _charges_pending(case: Case) -> list[str]:
    """Late fees: for a private letter the question arises only once a charge is
    known. While none of the three answers is there, name what is missing."""
    if case.value("document_type") != "reminder" or _charges_claimed(case):
        return []
    return [n for n in _CHARGES if case.fact(n).status is not Status.KNOWN]


def _objection_deadline_passed(case: Case, decision: Decision) -> bool:
    return any(d.key == "objection" and not d.action_done and d.working_days_left < 0
               for d in decision.deadlines)


ISSUES: tuple[Issue, ...] = (
    Issue("collection_fees", "debt_collection",
          {"de": "Zusatzkosten bei verspäteter Zahlung vor einer Betreibung: Verzugszins, "
                 "Mahngebühren, Inkassokosten (Art. 102–106 OR)",
           "en": "Additional charges for late payment before enforcement: default interest, "
                 "reminder fees, collection costs (Art. 102–106 OR)"},
          needs=("document_type",),
          test=lambda c, d: c.value("document_type") == "reminder" and _charges_claimed(c),
          statutes=("or-102", "or-104", "or-105", "or-106", "or-85", "schkg-27", "uwg-8"),
          pending=_charges_pending),
    Issue("payment_order_objection", "debt_collection",
          {"de": "Zahlungsbefehl: Zustellung, Rechtsvorschlag und Frist (Art. 74 SchKG)",
           "en": "Payment order: service, objection and deadline (Art. 74 SchKG)"},
          needs=("document_type",),
          # raised as long as an objection is not confirmed
          test=lambda c, d: (c.value("document_type") == "payment_order"
                             and not objection_record_complete(c)),
          statutes=("schkg-74", "schkg-68", "schkg-64", "schkg-33")),
    Issue("objection_deadline_missed", "debt_collection",
          {"de": "Frist für den Rechtsvorschlag möglicherweise verpasst: "
                 "Wiederherstellung (Art. 33 Abs. 4 SchKG)",
           "en": "Period for the objection possibly missed: restoration "
                 "(Art. 33 para. 4 SchKG)"},
          needs=("document_type", "document_received_date"),
          test=lambda c, d: (c.value("document_type") == "payment_order"
                             and _objection_deadline_passed(c, d)),
          statutes=("schkg-74", "schkg-64", "schkg-33")),
    Issue("advanced_enforcement", "debt_collection",
          {"de": "Fortgeschrittenes Verfahren: Rechtsöffnung oder Pfändung",
           "en": "Advanced proceedings: setting aside the objection, or seizure"},
          needs=("document_type",),
          test=lambda c, d: c.value("document_type") in ("seizure_notice", "court_document"),
          statutes=("schkg-17", "schkg-93")),
    Issue("register_entry", "credit_record",
          {"de": "Eintrag im Betreibungsregister: Nichtbekanntgabe an Dritte (Art. 8a SchKG)",
           "en": "Entry in the debt enforcement register: withholding from third parties "
                 "(Art. 8a SchKG)"},
          needs=("register_entry",),
          test=lambda c, d: c.value("register_entry") in ("enforcement", "old_enforcement"),
          statutes=("schkg-8a", "schkg-74", "schkg-85", "schkg-85a", "schkg-86", "schkg-33",
                    "gebv-12b")),
    Issue("loss_certificate", "credit_record",
          {"de": "Verlustschein: Tilgung und Löschung des Eintrags (Art. 149a SchKG)",
           "en": "Loss certificate: settlement and deletion of the entry (Art. 149a SchKG)"},
          needs=("register_entry",),
          test=lambda c, d: c.value("register_entry") == "loss_certificate",
          statutes=("schkg-149a",)),
    Issue("estate_interference", "inheritance_debt",
          {"de": "Einmischung in die Erbschaft: Verwirkung der Ausschlagung "
                 "(Art. 571 Abs. 2 ZGB)",
           "en": "Interference in the estate: forfeiture of the right to disclaim "
                 "(Art. 571 para. 2 ZGB)"},
          needs=("estate_actions",),
          test=lambda c, d: c.value("estate_actions") in ("took", "unsure"),
          statutes=("zgb-571", "zgb-567", "zgb-566")),
    Issue("disclaimer_period", "inheritance_debt",
          {"de": "Ausschlagung noch nicht erklärt: Frist, Verlängerung, vermutete "
                 "Ausschlagung (Art. 566, 567, 576 ZGB)",
           "en": "Disclaimer not yet declared: period, extension, presumed disclaimer "
                 "(Art. 566, 567, 576 ZGB)"},
          needs=("heir_basis",),
          # raised as long as a disclaimer is not confirmed
          test=lambda c, d: c.value("disclaimer_filed") is not True,
          statutes=("zgb-567", "zgb-566", "zgb-570", "zgb-572", "zgb-575", "zgb-576", "zgb-578",
                    "zgb-580", "zgb-588", "zgb-589", "zgb-593")),
    Issue("disclaimer_effect", "inheritance_debt",
          # Art. 570 governs form and record only; liability towards the deceased's
          # creditors despite a disclaimer is Art. 579.
          {"de": "Ausschlagung erklärt: Form und Protokoll (Art. 570 ZGB), Haftung "
                 "gegenüber Gläubigern trotz Ausschlagung (Art. 579 ZGB)",
           "en": "Disclaimer declared: form and record (Art. 570 ZGB), liability towards "
                 "creditors despite the disclaimer (Art. 579 ZGB)"},
          needs=("disclaimer_filed",),
          test=lambda c, d: c.value("disclaimer_filed") is True,
          statutes=("zgb-570", "zgb-579", "zgb-571", "zgb-566")),
)

ISSUE_BY_ID = {i.id: i for i in ISSUES}


def assess(case: Case, decision: Decision) -> tuple[list[Issue], list[tuple[Issue, list[str]]]]:
    """Return (raised issues, open issues with the names of the facts still missing).
    Issues outside the case's legal areas are ignored."""
    raised, still_open = [], []
    for issue in ISSUES:
        if issue.area not in case.areas:
            continue
        missing = [n for n in issue.needs
                   if case.fact(n).status is not Status.KNOWN]
        if not missing and issue.pending:
            missing = issue.pending(case)
        if missing:
            # A fact that is already known may show that the question cannot arise.
            # Test with what is known; only an issue that is still possible stays open.
            if _excluded(issue, case):
                continue
            still_open.append((issue, missing))
        elif issue.test(case, decision):
            raised.append(issue)
    return raised, still_open


# Known facts that rule an issue out although other needed facts are missing.
_EXCLUDES = {
    "collection_fees": lambda c: (c.value("document_type") not in (None, "reminder")
                                  or all(c.value(n) == "none" for n in _CHARGES)),
    "payment_order_objection": lambda c: (c.value("document_type") not in (None, "payment_order")
                                          or objection_record_complete(c)),
    "objection_deadline_missed": lambda c: (c.value("document_type") not in (None, "payment_order")
                                            or objection_record_complete(c)),
    "disclaimer_period": lambda c: c.value("disclaimer_filed") is True,
}


def _excluded(issue: Issue, case: Case) -> bool:
    check = _EXCLUDES.get(issue.id)
    return bool(check and check(case))
