"""Web interface. Usage:

    python server.py            # live: uses the model API (needs OPENAI_API_KEY)
    python server.py --demo     # demo: example cases with recorded model answers, no key

Then open http://127.0.0.1:8000 in a browser.

Uses only the Python standard library. The server listens on this computer
only (127.0.0.1) and keeps conversations in memory; they are gone when it stops.
"""
from __future__ import annotations

import argparse
import json
import os
import secrets
import threading
from collections import OrderedDict
from datetime import date
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from handover import demo, texts
from handover.answer import classify_structured
from handover.engine import Session
from handover.view import reply_view

WEB = Path(__file__).resolve().parent / "web"
TYPES = {".html": "text/html; charset=utf-8", ".css": "text/css; charset=utf-8",
         ".js": "text/javascript; charset=utf-8", ".svg": "image/svg+xml"}
MAX_BODY = 20_000          # bytes
MAX_MESSAGE = 4_000        # characters
MAX_CONTACT = 200          # characters per contact detail (name, e-mail, phone)
MAX_SESSIONS = 200


class App:
    def __init__(self, demo_mode: bool, today: date | None):
        self.demo = demo_mode
        self.today = demo.DEMO_TODAY if demo_mode else today
        if demo_mode:
            self.llm = demo.ReplayLLM()
        else:
            from handover.llm import OpenAILLM
            self.llm = OpenAILLM()
        self.sessions: OrderedDict[str, dict] = OrderedDict()
        self.lock = threading.Lock()

    # ---- data for the start page ------------------------------------------------
    def config(self, lang: str) -> dict:
        p = texts.DISCLOSURE_PARTS[lang]
        return {
            "demo": self.demo,
            "today": (self.today or date.today()).strftime("%d.%m.%Y"),
            "disclosure": {**p, "topics": [{"title": t, "text": s} for t, s in p["topics"]]},
            "consent_label": texts.CONSENT_LABEL[lang],
            "examples": [{"id": s["id"], "title": s["title"][lang],
                          "summary": s["summary"][lang], "text": s["messages"][lang][0]}
                         for s in demo.SCENARIOS],
        }

    # ---- conversations ------------------------------------------------------------
    def start(self, lang: str, consent: bool, scenario_id: str | None) -> dict:
        sc = demo.scenario(scenario_id) if scenario_id else None
        if self.demo:
            if sc is None:
                raise ValueError("In demo mode a conversation starts from an example.")
            consent = False          # the recordings were made without the screening
        session = Session(self.llm, consent_distress_screening=consent, today=self.today,
                          language=lang, answerer=classify_structured, compose=True)
        sid = secrets.token_urlsafe(18)
        with self.lock:
            self.sessions[sid] = {"session": session, "lock": threading.Lock(),
                                  "prepared": demo.pool(sc["messages"][lang]) if (sc and self.demo) else {}}
            while len(self.sessions) > MAX_SESSIONS:
                self.sessions.popitem(last=False)
        return {
            "id": sid,
            "welcome": texts.DISCLOSURE_PARTS[lang]["welcome"],
            "start_prompt": texts.START_PROMPT[lang],
            "consent": consent,
            "consent_ack": texts.CONSENT_ACK[consent][lang],
            # Demo: the typed messages in order, and the prepared answers for the lists.
            "script": ([m for m in sc["messages"][lang] if isinstance(m, str)]
                       if (sc and self.demo) else []),
        }

    @staticmethod
    def _view(entry: dict, reply) -> dict:
        """The reply for the page. In demo mode the prepared answer of the example is
        marked on each question; the person can tap it or any other answer."""
        view = reply_view(entry["session"], reply)
        for q in view["data"].get("questions") or []:
            value = demo.prepared(entry["prepared"], q)
            if value is not None:
                q["prepared"] = value
        return view

    def _entry(self, sid: str) -> dict:
        with self.lock:
            entry = self.sessions.get(sid)
        if entry is None:
            raise KeyError("unknown conversation")
        return entry

    def message(self, sid: str, text: str) -> dict:
        entry = self._entry(sid)
        with entry["lock"]:
            s: Session = entry["session"]
            return self._view(entry, s.step(text))

    def answers(self, sid: str, answers: dict) -> dict:
        """Answers chosen from the lists of the open questions. No model call."""
        entry = self._entry(sid)
        with entry["lock"]:
            s: Session = entry["session"]
            return self._view(entry, s.answer_form(answers))

    def revise(self, sid: str, name: str) -> dict:
        """The person wants to change a list answer. No model call."""
        entry = self._entry(sid)
        with entry["lock"]:
            s: Session = entry["session"]
            return self._view(entry, s.revise(name))

    def human(self, sid: str) -> dict:
        entry = self._entry(sid)
        with entry["lock"]:
            s: Session = entry["session"]
            return self._view(entry, s.request_human())

    def recover(self, sid: str, retry: bool) -> dict:
        entry = self._entry(sid)
        with entry["lock"]:
            s: Session = entry["session"]
            return self._view(entry, s.recover(retry=retry))

    def handover(self, sid: str, accept: bool, contact: dict) -> dict:
        """The user's answer (button) to the proposed hand-over."""
        entry = self._entry(sid)
        with entry["lock"]:
            s: Session = entry["session"]
            return self._view(entry, s.answer_handover(accept, contact=contact))


class Handler(BaseHTTPRequestHandler):
    app: App
    server_version = "HandoverPrototype"

    def log_message(self, fmt, *args):      # request lines only, never message contents
        print(f"{self.command} {urlparse(self.path).path} -> {args[1] if len(args) > 1 else ''}")

    def _send(self, status: int, body: bytes, ctype: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, status: int, data: dict) -> None:
        self._send(status, json.dumps(data, ensure_ascii=False).encode("utf-8"),
                   "application/json; charset=utf-8")

    def do_GET(self) -> None:
        url = urlparse(self.path)
        if url.path == "/api/config":
            lang = parse_qs(url.query).get("lang", ["de"])[0]
            return self._json(200, self.app.config(lang if lang in ("de", "en") else "de"))
        name = "index.html" if url.path == "/" else url.path.removeprefix("/static/")
        allowed = {p.name for p in WEB.iterdir() if p.suffix in TYPES}
        if name in allowed and (url.path == "/" or url.path.startswith("/static/")):
            path = WEB / name
            return self._send(200, path.read_bytes(), TYPES[path.suffix])
        self._json(404, {"error": "not found"})

    def do_POST(self) -> None:
        url = urlparse(self.path)
        try:
            length = int(self.headers.get("Content-Length") or 0)
            if length > MAX_BODY:
                return self._json(413, {"error": "too large"})
            body = json.loads(self.rfile.read(length) or b"{}")
            if not isinstance(body, dict):
                raise ValueError("JSON object expected")
            lang = body.get("lang") if body.get("lang") in ("de", "en") else "de"
            if url.path == "/api/session":
                return self._json(200, self.app.start(lang, body.get("consent") is True,
                                                      body.get("scenario")))
            if url.path == "/api/message":
                text = str(body.get("text") or "").strip()
                if not text or len(text) > MAX_MESSAGE:
                    return self._json(400, {"error": "empty or too long"})
                return self._json(200, self.app.message(str(body.get("id")), text))
            if url.path == "/api/answers":
                chosen = body.get("answers")
                if (not isinstance(chosen, dict) or not chosen or len(chosen) > 10
                        or not all(isinstance(k, str) and isinstance(v, str)
                                   for k, v in chosen.items())):
                    return self._json(400, {"error": "answers must name a listed answer "
                                                     "per question"})
                return self._json(200, self.app.answers(str(body.get("id")), chosen))
            if url.path == "/api/revise":
                if not isinstance(body.get("name"), str):
                    return self._json(400, {"error": "name of the answer expected"})
                return self._json(200, self.app.revise(str(body.get("id")), body["name"]))
            if url.path == "/api/human":
                return self._json(200, self.app.human(str(body.get("id"))))
            if url.path == "/api/recover":
                if not isinstance(body.get("retry"), bool):
                    return self._json(400, {"error": "retry must be true or false"})
                return self._json(200, self.app.recover(str(body.get("id")), body["retry"]))
            if url.path == "/api/handover":
                if not isinstance(body.get("accept"), bool):
                    return self._json(400, {"error": "accept must be true or false"})
                # First name, surname, e-mail, phone: text only. The engine checks
                # them (handover/contact.py); they never reach a model.
                raw = body.get("contact")
                contact = {k: v[:MAX_CONTACT] for k, v in (raw if isinstance(raw, dict) else {}).items()
                           if isinstance(k, str) and isinstance(v, str)}
                return self._json(200, self.app.handover(str(body.get("id")),
                                                         body["accept"], contact))
            return self._json(404, {"error": "not found"})
        except KeyError:
            self._json(404, {"error": "unknown conversation"})
        except (ValueError, json.JSONDecodeError) as e:
            self._json(400, {"error": str(e)})
        except RuntimeError as e:               # conversation already ended
            self._json(409, {"error": str(e)})
        except Exception as e:                  # never leak details to the page
            print(f"error: {type(e).__name__}: {e}")
            self._json(500, {"error": "internal error"})


def main() -> None:
    p = argparse.ArgumentParser(description="Web interface of the hand-over prototype")
    p.add_argument("--port", type=int, default=8000)
    p.add_argument("--demo", action="store_true",
                   help="example cases with recorded model answers; no API key needed")
    p.add_argument("--today", type=date.fromisoformat, default=None,
                   help="date used for deadlines in live mode (YYYY-MM-DD)")
    a = p.parse_args()

    if not a.demo and not os.environ.get("OPENAI_API_KEY"):
        import handover.config  # noqa: F401  (reads the .env file)
        if not os.environ.get("OPENAI_API_KEY"):
            raise SystemExit("OPENAI_API_KEY is not set. Put it into the .env file, or start "
                             "the demo without a key: python server.py --demo")
    if a.demo and not demo.RECORDINGS.exists():
        raise SystemExit("demo/recordings.json is missing. Create it with: "
                         "python tools/record_demo.py")

    Handler.app = App(a.demo, a.today)
    httpd = ThreadingHTTPServer(("127.0.0.1", a.port), Handler)
    print(f"{'Demo' if a.demo else 'Live'} mode. Open http://127.0.0.1:{a.port}  "
          "(stop with Ctrl+C)")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")


if __name__ == "__main__":
    main()
