"""Thresholds and settings. Values marked LEGAL are set by the legal lead."""
import os
from pathlib import Path


def _load_env_file() -> None:
    """Read KEY=value lines from the .env file in the project folder, if present.
    Variables already set in the shell take precedence."""
    path = Path(__file__).resolve().parent.parent / ".env"
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        value = value.strip().strip('"').strip("'")
        if value:
            os.environ.setdefault(key.strip(), value)


_load_env_file()

# LEGAL: a deadline with this many working days left (or fewer, or already
# passed) is referred immediately. Chosen so that a weekend in between still
# leaves the pro bono staff time to act.
DEADLINE_CLOSE_WORKING_DAYS = 4

# LEGAL (statutory periods, to be verified against Fedlex)
OBJECTION_DAYS = 10        # Art. 74 SchKG
DISCLAIMER_MONTHS = 3      # Art. 567 ZGB
REGISTER_WAIT_MONTHS = 3   # Art. 8a para. 3 lit. d SchKG: request for non-disclosure

# LEGAL (decided by the legal lead on 2026-11-13): in the area of late fees, the only
# letter that marks a case as urgent is one from the debt enforcement office
# (Betreibungsamt). A letter from a court is referred without the urgent mark.
URGENT_DOCUMENTS = ("payment_order", "seizure_notice")
# LEGAL (decided by the legal lead on 2026-11-13): a payment order gets the urgent
# notice and the conversation continues with the questions about the charges; it is
# handed over only if the objection period may already have passed. Other documents
# from the debt enforcement office are handed over at once.
CONTINUE_AFTER_URGENT_NOTICE = ("payment_order",)

# LEGAL (decided by the legal lead on 2026-11-13): hand-over proposals that are made
# alongside the answer. The person is told what applies and what to do, the hand-over is
# proposed once, and after a "no" the conversation continues and it is not proposed again.
#   R14-not-covered       a topic the stored sources do not cover
#   R4-disclaimer-passed  the period for disclaiming an inheritance may have passed and
#                         the deceased was not manifestly insolvent (apply for an extension)
#   R5-estate-actions     the heir dealt with the estate in a way that can be interference
# Register entries (flow of 2026-11-14; these two were set by the AI assistant in the
# same way and are to be confirmed by the legal lead):
#   R5-register-court         what remains for the entry goes through a court or the
#                             supervisory authority (no objection raised, or the creditor
#                             went to court)
#   R5-private-credit-agency  the entry is held by a private credit agency, which the
#                             stored sources do not cover
SOFT_RULES = ("R14-not-covered", "R4-disclaimer-passed", "R5-estate-actions",
              "R5-register-court", "R5-private-credit-agency")
# LEGAL (proposed by the AI assistant, not yet confirmed): from this many working days
# before the earliest end of the disclaimer period, the reply carries an urgent notice.
# The conversation continues (decision of the legal lead on 2026-11-13).
DISCLAIMER_NOTICE_WORKING_DAYS = 10

# LEGAL (proposed, not yet confirmed): claims above this amount are referred.
CLAIM_AMOUNT_REFER_CHF = 5000

# SERVICE POLICY (decided by the legal lead on 2026-11-15): priority class of a
# handed-over case (handover/priority.py). A case in which only these rules fired, with
# no urgent mark and no open deadline, is class 3 "no deadline known": the person wants
# a human (R1), the matter is outside the three legal fields (R3, R14), or the
# conversation brought no result (R7, R8, R9). Every other rule, and any rule not
# listed here, makes the case class 2 at least.
PRIORITY_NO_DEADLINE_RULES = ("R1", "R3", "R7", "R8", "R9", "R14")

# Conversation limits (see full_report.md section 3.1)
MAX_QUESTIONS_PER_ROUND = 3
MAX_ASKS_PER_FIELD = 2
MAX_ROUNDS = 24

# Model access
LLM_MODEL = os.environ.get("LLM_MODEL", "gpt-6-luna")
LLM_BASE_URL = os.environ.get("LLM_BASE_URL") or None   # set for a local model server
LLM_TIMEOUT_SECONDS = float(os.environ.get("LLM_TIMEOUT_SECONDS") or 60)

# Briefing delivery
OUTBOX_DIR = os.environ.get("OUTBOX_DIR", "outbox")
# Language of the briefing for the legal team ("de" or "en").
BRIEFING_LANGUAGE = os.environ.get("BRIEFING_LANGUAGE", "de")
