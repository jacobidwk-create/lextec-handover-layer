"""Builds sources/case_law.json from the selection made by the legal team.
Usage: python tools/verify_case_law.py

The legal team selects decisions and pastes the relevant passage into
sources/case_law_selection.json. This script downloads each decision from
its public address (a web page or a PDF file) and accepts an entry only if
the pasted passage appears word for word in the decision. A passage that
was mistyped, shortened or taken from another decision is rejected and
reported.
"""
import html
import io
import json
import re
import ssl
import sys
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SELECTION = ROOT / "sources" / "case_law_selection.json"
OUT = ROOT / "sources" / "case_law.json"
REQUIRED = ("id", "citation", "url", "passage", "areas", "selected_by")


def _ssl_context() -> ssl.SSLContext:
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        return ssl.create_default_context()


def normalise(text: str) -> str:
    """The form in which passage and decision are compared: lower case, without
    white space and hyphens. The words and their order must still be identical.
    White space and hyphens are ignored because they depend on the layout, not
    on the wording: a PDF splits words at the end of a line ("Verwal-
    tungshandlung"), and a web page puts spaces around links ("( Art. 82 )")."""
    return re.sub(r"[\s\-\xad\xa0\u2010\u2011]+", "", text).lower()


def page_text(raw: str) -> str:
    raw = re.sub(r"<(script|style).*?</\1>", " ", raw, flags=re.S | re.I)
    return html.unescape(re.sub(r"<[^>]+>", " ", raw))


def pdf_text(data: bytes) -> str:
    """Text of a PDF file, page after page. A scanned PDF without a text layer
    yields no text; such an entry is rejected."""
    from pypdf import PdfReader
    reader = PdfReader(io.BytesIO(data))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def document_text(data) -> str:
    """Plain text of a downloaded decision, whether web page or PDF."""
    if isinstance(data, str):
        return page_text(data)
    if data[:5] == b"%PDF-":
        return pdf_text(data)
    return page_text(data.decode("utf-8", errors="replace"))


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "legal-intake-prototype"})
    with urllib.request.urlopen(req, timeout=90, context=_ssl_context()) as r:
        return r.read()


def verify_entry(entry: dict, fetcher=fetch) -> tuple[bool, str]:
    missing = [k for k in REQUIRED if not entry.get(k)]
    if missing:
        return False, "missing fields: " + ", ".join(missing)
    if len(entry["passage"].strip()) < 40:
        return False, "passage shorter than 40 characters"
    try:
        text = document_text(fetcher(entry["url"]))
    except Exception as e:
        return False, f"download or reading failed ({type(e).__name__})"
    if not text.strip():
        return False, "no text could be read from the document"
    if normalise(entry["passage"]) not in normalise(text):
        return False, "passage not found word for word in the decision"
    return True, "ok"


def main() -> int:
    selection = json.loads(SELECTION.read_text(encoding="utf-8"))
    corpus, failed = {}, 0
    for e in selection:
        ok, msg = verify_entry(e)
        print(f"{'ok ' if ok else 'REJECTED'}  {e.get('citation', e.get('id', '?'))}: {msg}")
        if not ok:
            failed += 1
            continue
        corpus[e["id"]] = {
            "type": "decision",
            "citation": e["citation"] + (f" E. {e['consideration']}" if e.get("consideration") else ""),
            "url": e["url"],
            "areas": e["areas"],
            "issues": e.get("issues", []),
            # The question the passage answers, and the condition on the established
            # facts under which it is printed in a briefing (handover/relevance.py).
            "question": e.get("question", {}),
            "when": e.get("when", "always"),
            "rules": e.get("rules", []),
            "facts": e.get("facts", {}),
            "use": e.get("use", ["briefing"]),
            "holding": e.get("holding", ""),
            "text": e["passage"].strip(),
            "selected_by": e["selected_by"],
            "verified_against_source": date.today().isoformat(),
        }
    OUT.write_text(json.dumps(corpus, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {len(corpus)} verified decision passage(s) to {OUT}; {failed} rejected")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
