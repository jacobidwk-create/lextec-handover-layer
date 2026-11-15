"""Builds sources/corpus.json from Fedlex, the official publication platform
of Swiss federal law. Usage: python tools/fetch_sources.py

For each statute the script asks the Fedlex open-data endpoint for the latest
consolidated German version, downloads it, and copies the listed articles
word for word. Nothing in the corpus is typed by hand or written by a model.
"""
import html
import json
import re
import ssl
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

SPARQL = "https://fedlex.data.admin.ch/sparqlendpoint"
OUT = Path(__file__).resolve().parent.parent / "sources" / "corpus.json"

# statute -> (abbreviation, Fedlex identifier, {article: [areas]})
LAWS = {
    "schkg": ("SchKG", "eli/cc/11/529_488_529", {
        "8a": ["credit_record", "debt_collection"],
        "17": ["debt_collection"],
        "27": ["debt_collection"],
        "31": ["debt_collection"],
        "33": ["debt_collection", "credit_record"],
        "38": ["credit_record"],
        "63": ["debt_collection"],
        "64": ["debt_collection"],
        "68": ["debt_collection"],
        "69": ["debt_collection"],
        "22": ["credit_record"],
        "73": ["credit_record"],
        "74": ["debt_collection", "credit_record"],
        "79": ["credit_record"],
        "80": ["credit_record"],
        "82": ["debt_collection"],
        "85": ["credit_record"],
        "85a": ["credit_record"],
        "86": ["credit_record"],
        "93": ["debt_collection"],
        "149": ["inheritance_debt"],
        "149a": ["credit_record"],
    }),
    # Fee ordinance to the SchKG: the flat fees for a register extract and for the
    # request not to disclose an enforcement to third parties.
    "gebv": ("GebV SchKG", "eli/cc/1996/2937_2937_2937", {
        "12a": ["credit_record"],
        "12b": ["credit_record"],
    }),
    "or": ("OR", "eli/cc/27/317_321_377", {
        "1": ["debt_collection"],
        "75": ["debt_collection"],
        "85": ["debt_collection"],
        "102": ["debt_collection"],
        "104": ["debt_collection"],
        "105": ["debt_collection"],
        "106": ["debt_collection"],
        "127": ["debt_collection"],
        "128": ["debt_collection"],
        "135": ["debt_collection"],
        "160": ["debt_collection"],
        "161": ["debt_collection"],
        "163": ["debt_collection"],
    }),
    "zgb": ("ZGB", "eli/cc/24/233_245_233", {
        "8": ["debt_collection"],
        "306": ["inheritance_debt"],
        "560": ["inheritance_debt"],
        "566": ["inheritance_debt"],
        "567": ["inheritance_debt"],
        "571": ["inheritance_debt"],
        "572": ["inheritance_debt"],
        "573": ["inheritance_debt"],
        "574": ["inheritance_debt"],
        "575": ["inheritance_debt"],
        "578": ["inheritance_debt"],
        "589": ["inheritance_debt"],
        "593": ["inheritance_debt"],
        "568": ["inheritance_debt"],
        "569": ["inheritance_debt"],
        "570": ["inheritance_debt"],
        "576": ["inheritance_debt"],
        "579": ["inheritance_debt"],
        "580": ["inheritance_debt"],
        "587": ["inheritance_debt"],
        "588": ["inheritance_debt"],
    }),
    "uwg": ("UWG", "eli/cc/1988/223_223_223", {
        "8": ["debt_collection"],
    }),
    "kvg": ("KVG", "eli/cc/1995/1328_1328_1328", {
        "64a": ["debt_collection"],
    }),
    "elg": ("ELG", "eli/cc/2007/804", {
        "11a": ["inheritance_debt"],
    }),
}

QUERY = """PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
SELECT ?date ?url WHERE {
  ?cons jolux:isMemberOf <https://fedlex.data.admin.ch/%s> ;
        jolux:dateApplicability ?date ;
        jolux:isRealizedBy ?expr .
  ?expr jolux:language <http://publications.europa.eu/resource/authority/language/DEU> ;
        jolux:isEmbodiedBy ?manif .
  ?manif jolux:isExemplifiedBy ?url .
  FILTER(CONTAINS(STR(?url), "html"))
  FILTER(?date <= "%s"^^<http://www.w3.org/2001/XMLSchema#date>)
} ORDER BY DESC(?date) LIMIT 1"""


def _ssl_context() -> ssl.SSLContext:
    """Use the certifi certificate bundle if present (needed on some macOS Pythons)."""
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        return ssl.create_default_context()


def get(url: str, data: bytes | None = None, accept: str = "*/*") -> str:
    req = urllib.request.Request(url, data=data, headers={
        "Accept": accept, "User-Agent": "legal-intake-prototype"})
    with urllib.request.urlopen(req, timeout=90, context=_ssl_context()) as r:
        return r.read().decode("utf-8")


def latest_version(eli: str) -> tuple[str, str]:
    q = QUERY % (eli, date.today().isoformat())
    body = urllib.parse.urlencode({"query": q}).encode()
    res = json.loads(get(SPARQL, body, "application/sparql-results+json"))
    b = res["results"]["bindings"][0]
    return b["date"]["value"], b["url"]["value"]


def article_text(page: str, art: str) -> str:
    art_id = "art_" + re.sub(r"(\d+)([a-z]+)", r"\1_\2", art)
    m = re.search(rf'<article id="{art_id}">(.*?)</article>', page, re.S)
    if not m:
        raise ValueError(f"article {art} not found")
    block = m.group(1)
    block = re.sub(r'<div class="footnotes">.*?</div>', "", block, flags=re.S)
    block = re.sub(r'<sup><a href="#fn-.*?</a></sup>', "", block, flags=re.S)  # footnote marks
    block = re.sub(r"<h6.*?</h6>", "", block, flags=re.S)                      # heading
    block = re.sub(r"<sup>(\d+)</sup>", r"\1 ", block)                         # paragraph numbers
    block = re.sub(r"</(p|dd|dt|div)>", "\n", block)
    text = html.unescape(re.sub(r"<[^>]+>", "", block)).replace("\xa0", " ")
    lines = [re.sub(r"[ \t]+", " ", l).strip() for l in text.splitlines()]
    return "\n".join(l for l in lines if l)


def main() -> None:
    corpus = {}
    for key, (abbr, eli, articles) in LAWS.items():
        version, url = latest_version(eli)
        page = get(url)
        for art, areas in articles.items():
            art_id = "art_" + re.sub(r"(\d+)([a-z]+)", r"\1_\2", art)
            corpus[f"{key}-{art}"] = {
                "citation": f"Art. {art} {abbr}",
                "url": f"https://www.fedlex.admin.ch/{eli}/de#{art_id}",
                "version_in_force_since": version,
                "retrieved": date.today().isoformat(),
                "language": "de",
                "areas": areas,
                "text": article_text(page, art),
            }
            print(f"ok  Art. {art} {abbr} (version {version})")
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(corpus, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {len(corpus)} articles to {OUT}")


if __name__ == "__main__":
    main()
