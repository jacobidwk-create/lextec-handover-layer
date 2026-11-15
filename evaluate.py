"""Runs the scenario test set. Usage:

    python evaluate.py --set dev            # development scenarios
    python evaluate.py --set heldout        # held-out scenarios (run once, at the end)
    python evaluate.py --set dev --baseline # same scenarios, model decides the route alone

Each scenario is run several times (default 3) and the WORST run counts.
A simulated user answers follow-up questions strictly from the scenario's
hidden facts. Needs OPENAI_API_KEY.
"""
from __future__ import annotations

import argparse
import json
import tempfile
from datetime import date
from pathlib import Path

from handover import config
from handover.answer import classify
from handover.engine import Session
from handover.llm import LLM
from handover.schema import Route

MAX_STEPS = config.MAX_ROUNDS + 6  # evaluation budget, not a user-question limit

USER_SIM = """You play a layperson who contacted a legal intake chat in Switzerland. \
Answer the system's questions in {lang}, briefly and in everyday language. Use ONLY the \
facts below. If a question is not covered by the facts, say that you do not know. Never \
add facts.

Facts you know:
{facts}

Return JSON: {{"reply": "..."}}"""

BASELINE = """You are a legal intake assistant for the Canton of Zurich. Covered topics: \
disputed debts and collection fees, inheriting debts, debt enforcement register entries. Decide for the conversation so far:
- "ASK": information is missing; put your follow-up questions in "message".
- "REFER": the matter must go to a human legal professional.
- "PROCEED": you have enough information to give a general legal classification.
Today's date: {today}.
Return JSON: {{"route": "ASK" | "REFER" | "PROCEED", "message": "..."}}"""


def load(set_name: str) -> list[dict]:
    files = sorted(Path("scenarios").rglob("*.json"))
    scenarios = [json.loads(f.read_text(encoding="utf-8")) for f in files]
    return [s for s in scenarios if s.get("set") == set_name]


def sim_reply(llm: LLM, sc: dict, convo: list[tuple[str, str]]) -> str:
    lang = "German" if sc["language"] == "de" else "English"
    system = USER_SIM.format(lang=lang, facts=sc["hidden_facts"])
    text = "\n".join(f"{r.upper()}: {t}" for r, t in convo)
    return str(llm.complete_json(system, text).get("reply", ""))


def run_system(llm: LLM, sc: dict) -> dict:
    s = Session(llm, consent_distress_screening=sc.get("consent_distress_screening", False),
                today=date.fromisoformat(sc["today"]), language=sc["language"],
                answerer=classify)
    asked: set[str] = set()
    msg, reply = sc["opening_message"], None
    for _ in range(MAX_STEPS):
        reply = s.step(msg)
        asked |= set(reply.decision.questions)
        if reply.route is not Route.ASK:
            break
        msg = sim_reply(llm, sc, s.case.messages)
    rules = [r.rule for r in reply.decision.reasons]
    return {"route": reply.route.value, "asked": asked, "rules": rules,
            "deadline_flagged": "R4-deadline-close" in rules}


def run_baseline(llm: LLM, sc: dict) -> dict:
    convo = [("user", sc["opening_message"])]
    route = "ASK"
    for _ in range(MAX_STEPS):
        text = "\n".join(f"{r.upper()}: {t}" for r, t in convo)
        out = llm.complete_json(BASELINE.format(today=sc["today"]), text)
        route = out.get("route") if out.get("route") in ("ASK", "REFER", "PROCEED") else "ASK"
        if route != "ASK":
            break
        convo.append(("assistant", str(out.get("message", ""))))
        convo.append(("user", sim_reply(llm, sc, convo)))
    return {"route": route, "asked": set(), "rules": [], "deadline_flagged": None}


def score(sc: dict, runs: list[dict]) -> dict:
    gold = sc["gold"]
    must_ask = set(gold.get("must_ask", []))
    return {
        "id": sc["id"], "gold": gold["route"], "got": [r["route"] for r in runs],
        "route_ok": all(r["route"] == gold["route"] for r in runs),
        "missed_escalation": gold["route"] == "REFER"
                             and any(r["route"] == "PROCEED" for r in runs),
        "over_escalation": gold["route"] == "PROCEED"
                           and any(r["route"] == "REFER" for r in runs),
        "deadline_ok": (None if not gold.get("deadline_flagged")
                        or runs[0]["deadline_flagged"] is None
                        else all(r["deadline_flagged"] for r in runs)),
        "asked_ok": (None if not must_ask else all(must_ask <= r["asked"] for r in runs)),
    }


def evaluate(llm: LLM, scenarios: list[dict], runs: int = 3, baseline: bool = False):
    runner = run_baseline if baseline else run_system
    return [score(sc, [runner(llm, sc) for _ in range(runs)]) for sc in scenarios]


def report(rows: list[dict]) -> str:
    def rate(key):
        vals = [r[key] for r in rows if r[key] is not None]
        return f"{sum(vals)}/{len(vals)}" if vals else "n/a"
    lines = [f"{'id':8}{'gold':9}{'runs':28}{'ok'}"]
    for r in rows:
        lines.append(f"{r['id']:8}{r['gold']:9}{','.join(r['got']):28}"
                     f"{'ok' if r['route_ok'] else 'WRONG'}"
                     f"{'  MISSED ESCALATION' if r['missed_escalation'] else ''}")
    lines += ["", f"scenarios:               {len(rows)}",
              f"route correct (all runs): {rate('route_ok')}",
              f"missed escalations:       {rate('missed_escalation')}",
              f"over-escalations:         {rate('over_escalation')}",
              f"deadlines flagged:        {rate('deadline_ok')}",
              f"required questions asked: {rate('asked_ok')}"]
    return "\n".join(lines)


def main() -> None:
    from handover.llm import OpenAILLM
    p = argparse.ArgumentParser()
    p.add_argument("--set", default="dev")
    p.add_argument("--runs", type=int, default=3)
    p.add_argument("--baseline", action="store_true")
    a = p.parse_args()
    config.OUTBOX_DIR = tempfile.mkdtemp(prefix="eval_outbox_")
    scenarios = load(a.set)
    if not scenarios:
        raise SystemExit(f"No scenarios with \"set\": \"{a.set}\" found in scenarios/")
    print(report(evaluate(OpenAILLM(), scenarios, a.runs, a.baseline)))


if __name__ == "__main__":
    main()
