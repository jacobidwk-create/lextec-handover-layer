"""Command-line chat. Usage: python chat.py [--lang de|en] [--today YYYY-MM-DD]

Needs OPENAI_API_KEY in the environment. --today sets the date used for
deadline computation (useful for demos and tests).
"""
import argparse
from datetime import date

from handover import texts
from handover.answer import classify
from handover.contact import FIELDS
from handover.engine import Session, consent_answer
from handover.llm import OpenAILLM
from handover.schema import Route


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--lang", choices=["de", "en"], default="de")
    p.add_argument("--today", type=date.fromisoformat, default=None)
    p.add_argument("--debug", action="store_true", help="show the rules that fired")
    a = p.parse_args()

    import os
    if not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY is not set. See README, section 'How to run and test'.")

    print(texts.DISCLOSURE[a.lang], "\n")
    print(texts.CONSENT_QUESTION[a.lang])
    consent = input("> ").strip().lower() in ("ja", "j", "yes", "y")
    print("\n" + texts.CONSENT_ACK[consent][a.lang], texts.START_PROMPT[a.lang],
          texts.EXIT_HINT[a.lang])
    session = Session(OpenAILLM(), consent_distress_screening=consent, today=a.today,
                      language=a.lang, answerer=classify, compose=True)

    while not session.closed:
        try:
            user = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if user.lower() in ("exit", "quit", "ende"):
            break
        if not user:
            continue
        # A proposed hand-over waits for a clear yes or no. On yes, ask who the person
        # is and how the team reaches them (first name, surname and e-mail are required);
        # this goes into the briefing only, not to the model. If a required detail is
        # missing, nothing is passed on and the reply says what is needed.
        answer = consent_answer(user) if session.handover == "offered" else None
        if answer is True:
            lang = session.case.language
            print("\n" + texts.CONTACT_NOTE[lang])
            contact = {name: input(texts.CONTACT_FIELD_LABELS[name][lang] + "\n> ").strip()
                       for name in FIELDS}
            reply = session.answer_handover(True, contact=contact, typed=user)
        elif answer is False:
            reply = session.answer_handover(False, typed=user)
        else:
            reply = session.step(user)
        print("\n" + reply.text.replace("**", ""))
        if a.debug:
            for r in reply.decision.reasons:
                print(f"   [{r.rule}] {r.text}")
        if reply.briefing_path:
            print(f"\n(Briefing written to {reply.briefing_path})")


if __name__ == "__main__":
    main()
