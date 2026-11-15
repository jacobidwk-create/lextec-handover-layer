"""Records the model answers for the demo scenarios.
Usage: python tools/record_demo.py      (needs OPENAI_API_KEY)

Runs every scenario of handover/demo.py in German and English against the
real model and stores the answers in demo/recordings.json. Run it again
whenever a prompt, a question text or a scenario was changed.
"""
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from handover import config, demo                      # noqa: E402
from handover.answer import classify_structured        # noqa: E402
from handover.engine import Session                    # noqa: E402
from handover.llm import OpenAILLM                     # noqa: E402


def main() -> int:
    config.OUTBOX_DIR = tempfile.mkdtemp(prefix="demo_outbox_")
    store: dict = {}
    llm = demo.RecordingLLM(OpenAILLM(), store)
    problems = 0
    for sc in demo.SCENARIOS:
        for lang in ("de", "en"):
            s = Session(llm, consent_distress_screening=False, today=demo.DEMO_TODAY,
                        language=lang, answerer=classify_structured, compose=True)
            reply = demo.run(s, sc["messages"][lang])
            rules = [r.rule for r in reply.decision.reasons]
            if s.handover == "offered":
                # The yes to the hand-over lets the model write the short description
                # for the advisor; record that answer too.
                s.answer_handover(True, contact=demo.DEMO_CONTACT)
            ok = (reply.route.value == sc["expect"]
                  and ("expect_rule" not in sc or sc["expect_rule"] in rules)
                  and reply.decision.urgent == sc.get("expect_urgent", reply.decision.urgent))
            problems += not ok
            print(f"{'ok ' if ok else 'UNEXPECTED'}  {sc['id']:14} {lang}  "
                  f"{reply.route.value:8} {', '.join(rules)}")
    demo.RECORDINGS.parent.mkdir(exist_ok=True)
    demo.RECORDINGS.write_text(json.dumps(store, ensure_ascii=False, indent=1),
                               encoding="utf-8")
    print(f"wrote {len(store)} recorded answers to {demo.RECORDINGS}")
    if problems:
        print("At least one scenario did not end as expected. Check before using the demo.")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
