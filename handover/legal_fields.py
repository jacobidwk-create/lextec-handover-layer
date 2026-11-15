"""Legal fields: one text file per field in the folder legal_fields/.

A legal field is an area of law the system covers (late fees, inherited debts, ...).
Each file holds, in plain text that the legal lead can edit without touching code:

  the head      id, titles, when a case belongs to the field, what the field covers
                and what it does not, the statute articles the model may cite, and
                how the field is handled (answer, or always hand over after questions)
  the body      the legal flow of the field in prose: the "playbook". The model that
                writes the replies receives it as its instructions.

Adding a field is adding a file (full_report.md section 3.12). Structured questions with
answer lists (areas.py), deadlines (deadlines.py) and a fixed result (as late_fees.py
for late fees) are optional additions for a field; without them the model leads the
conversation from the playbook, and every legal statement still has to be pinned to
one of the listed articles.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

FIELDS_DIR = Path(__file__).resolve().parent.parent / "legal_fields"
HANDLING = ("answer", "refer_after_questions")
_REQUIRED = ("id", "title_de", "title_en", "handling", "description", "covers",
             "not_covered", "statutes")


@dataclass(frozen=True)
class LegalField:
    id: str
    title: dict                 # {"de": ..., "en": ...}
    description: str            # shown to the extraction model: when a case belongs here
    covers: str
    not_covered: str
    statutes: tuple             # keys of sources/corpus.json the model may cite
    handling: str               # "answer" | "refer_after_questions"
    playbook: str               # the legal flow, as instructions for the model
    author: str = ""
    file: str = ""


def parse(text: str, name: str = "") -> LegalField:
    """Read one field file: a head of "key: value" lines between two lines of three
    dashes, then the playbook."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError(f"{name}: the file must start with a line of three dashes")
    try:
        end = next(i for i, line in enumerate(lines[1:], 1) if line.strip() == "---")
    except StopIteration:
        raise ValueError(f"{name}: the head is not closed by a line of three dashes") from None
    head = {}
    for line in lines[1:end]:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            raise ValueError(f"{name}: head line without a colon: {line!r}")
        key, value = line.split(":", 1)
        head[key.strip()] = value.strip()
    missing = [k for k in _REQUIRED if not head.get(k)]
    if missing:
        raise ValueError(f"{name}: missing in the head: {', '.join(missing)}")
    if head["handling"] not in HANDLING:
        raise ValueError(f"{name}: handling must be one of {HANDLING}")
    playbook = "\n".join(lines[end + 1:]).strip()
    if not playbook:
        raise ValueError(f"{name}: the playbook (the text after the head) is empty")
    return LegalField(
        id=head["id"], title={"de": head["title_de"], "en": head["title_en"]},
        description=head["description"], covers=head["covers"],
        not_covered=head["not_covered"],
        statutes=tuple(s.strip() for s in head["statutes"].split(",") if s.strip()),
        handling=head["handling"], playbook=playbook, author=head.get("author", ""),
        file=name)


def load(folder: Path = FIELDS_DIR) -> dict[str, LegalField]:
    """All fields of the folder, in the order of their file names."""
    out: dict[str, LegalField] = {}
    for path in sorted(folder.glob("*.md")):
        field = parse(path.read_text(encoding="utf-8"), path.name)
        if field.id in out:
            raise ValueError(f"{path.name}: the id {field.id!r} is used twice")
        out[field.id] = field
    return out


REGISTRY = load()


def playbooks(areas) -> str:
    """The playbooks of the given fields, for a model prompt."""
    return "\n\n".join(f"## Field: {REGISTRY[a].title['en']} ({a})\n"
                       f"Covers: {REGISTRY[a].covers}\n"
                       f"Not covered: {REGISTRY[a].not_covered}\n\n{REGISTRY[a].playbook}"
                       for a in sorted(areas) if a in REGISTRY)


def statute_keys(areas) -> list[str]:
    """Keys of the articles the model may cite for the given fields."""
    seen, out = set(), []
    for a in sorted(areas):
        for key in (REGISTRY[a].statutes if a in REGISTRY else ()):
            if key not in seen:
                seen.add(key)
                out.append(key)
    return out
