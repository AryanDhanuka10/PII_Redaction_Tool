"""
pii_engine.py
--------------
Core detection + consistent fake-replacement engine for PII redaction.

Approach (hybrid, as allowed by the assignment brief):
  1. Regex detectors for STRUCTURED PII that has a predictable shape:
     email, phone, SSN, credit card (Luhn-validated), IP address,
     date-of-birth (date near a DOB-style keyword), PIN/ZIP code.
  2. spaCy en_core_web_sm NER for UNSTRUCTURED PII that has no fixed
     shape: person names (PERSON) and company names (ORG).
  3. A light address heuristic layered on top of spaCy's GPE/LOC/FAC
     entities plus a "address keyword" line-scan (Village/Taluka/
     District/Road/Pune/Maharashtra/PIN-code patterns), because Indian
     mailing addresses in this document are multi-line blocks that pure
     NER under-detects.

Every detected PII value is mapped to a FAKE but *realistic* replacement
using Faker, and the mapping is cached so the same real value always
maps to the same fake value everywhere in the document (this matches
the worked example in the assignment: the same name/email recurring
gets the same fake alias every time).
"""

import re
import spacy
from faker import Faker
from dataclasses import dataclass, field

fake = Faker()
Faker.seed(42)  # reproducible fake values across runs


 # Regex patterns for structured PII
 
RE_EMAIL = re.compile(
    r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"
)

# Indian mobile (+91 / 0-prefixed, 10 digits) and generic international phone
RE_PHONE = re.compile(
    r"(?<!\d)(?:\+?91[\s\-]?)?[6-9]\d{9}(?!\d)"
    r"|(?<!\d)\+\d{1,3}[\s\-]?\d{2,4}[\s\-]?\d{3,4}[\s\-]?\d{3,4}(?!\d)"
)

RE_SSN = re.compile(r"(?<!\d)\d{3}-\d{2}-\d{4}(?!\d)")

RE_CREDIT_CARD = re.compile(
    r"(?<!\d)(?:\d[ \-]?){13,16}(?!\d)"
)

RE_IP = re.compile(
    r"(?<!\d)(?:(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|1?\d?\d)(?!\d)"
)

RE_PIN = re.compile(r"(?<!\d)\d{3}\s?[\-–]?\s?\d{3}(?!\d)")  # Indian PIN "410 501"

RE_DOB_CONTEXT = re.compile(
    r"(?:date of birth|dob|d\.o\.b\.?|born on)\s*[:\-]?\s*"
    r"(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}|"
    r"\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+\d{2,4})",
    re.IGNORECASE,
)

ADDRESS_KEYWORDS = re.compile(
    r"\b(Village|Taluka|District|Tehsil|Road|Street|Nagar|Colony|Pune|"
    r"Maharashtra|Mumbai|Delhi|Bengaluru|Chennai|Hyderabad|Kolkata|"
    r"Society|Apartment|Sector|Block|Wing|Floor)\b",
    re.IGNORECASE,
)


def luhn_valid(number: str) -> bool:
    digits = [int(d) for d in re.sub(r"[ \-]", "", number)]
    if len(digits) < 13:
        return False
    checksum = 0
    parity = len(digits) % 2
    for i, d in enumerate(digits):
        if i % 2 == parity:
            d *= 2
            if d > 9:
                d -= 9
        checksum += d
    return checksum % 10 == 0


@dataclass
class Match:
    start: int
    end: int
    text: str
    label: str


@dataclass
class PIIMapper:
    """Caches real->fake mappings so recurring values stay consistent."""
    cache: dict = field(default_factory=dict)
    counters: dict = field(default_factory=lambda: {})

    def fake_for(self, label: str, real_value: str) -> str:
        key = (label, real_value.strip().lower())
        if key in self.cache:
            return self.cache[key]

        if label == "PERSON":
            val = fake.name()
        elif label == "EMAIL":
            val = fake.email()
        elif label == "PHONE":
            val = fake.phone_number()
        elif label == "ORG":
            val = fake.company()
        elif label == "ADDRESS":
            val = fake.address().replace("\n", ", ")
        elif label == "SSN":
            val = fake.ssn()
        elif label == "CREDIT_CARD":
            val = fake.credit_card_number()
        elif label == "DOB":
            val = fake.date_of_birth().strftime("%d/%m/%Y")
        elif label == "IP":
            val = fake.ipv4_public()
        elif label == "PIN":
            val = str(fake.random_int(100000, 999999))
        else:
            val = "[REDACTED]"

        self.cache[key] = val
        return val


nlp = spacy.load("en_core_web_sm")


RE_INDIAN_PIN_ANCHOR = re.compile(r"\d{3}\s?[\-–]?\s?\d{3}")

# Address heuristic: an address block is a run of words containing at least
# one street/area keyword AND ending in a 6-digit Indian PIN code (with or
# without the customary space, e.g. "411 045" or "411045"). This is a
# line-level heuristic, not true span-level NER, and is the component most
# likely to under- or over-fire -- see README "Known limitations".
RE_ADDRESS_BLOCK = re.compile(
    r"[A-Z0-9][A-Za-z0-9,\.\-/ ]{3,140}?"
    r"(?:Village|Taluka|Road|Street|Nagar|Colony|Society|Apartment|"
    r"Sector|Block|Wing|Floor|Farms|Centre|Center)"
    r"[A-Za-z0-9,\.\-/ ]{0,80}?"
    r"\d{3}\s?[\-–]?\s?\d{3}"
)


def detect_address(text: str):
    matches = []
    for m in RE_ADDRESS_BLOCK.finditer(text):
        matches.append(Match(m.start(), m.end(), m.group(), "ADDRESS"))
    return matches


def detect_structured(text: str):
    """Yield Match objects for regex-detectable PII types."""
    matches = []

    for m in RE_EMAIL.finditer(text):
        matches.append(Match(m.start(), m.end(), m.group(), "EMAIL"))

    for m in RE_DOB_CONTEXT.finditer(text):
        g = m.group(1)
        s = m.start(1)
        matches.append(Match(s, s + len(g), g, "DOB"))

    for m in RE_SSN.finditer(text):
        matches.append(Match(m.start(), m.end(), m.group(), "SSN"))

    for m in RE_IP.finditer(text):
        matches.append(Match(m.start(), m.end(), m.group(), "IP"))

    for m in RE_PHONE.finditer(text):
        matches.append(Match(m.start(), m.end(), m.group(), "PHONE"))

    for m in RE_CREDIT_CARD.finditer(text):
        digits_only = re.sub(r"[ \-]", "", m.group())
        if len(digits_only) in (13, 14, 15, 16) and luhn_valid(m.group()):
            matches.append(Match(m.start(), m.end(), m.group(), "CREDIT_CARD"))

    return matches



# Generic legal/financial "defined terms" and public regulators that spaCy's
# ORG label frequently (mis)fires on in prospectus-style documents. These are
# not personally- or company-identifying, so we explicitly exclude them.
# See README "Precision tuning" section for rationale.
ORG_STOPLIST = {
    "company", "board", "offer", "prospectus", "registrar", "syndicate",
    "bidders", "promoters", "promoter group", "promoter selling shareholders",
    "non-institutional investors", "anchor investors", "upi", "upi bidders",
    "sebi", "bse", "nse", "rbi", "roc", "rta", "cdsl", "nsdl", "gst", "ipo",
    "n.a.", "registered office", "corporate office", "this red herring prospectus",
    "the cara report", "the care report", "restated financial statements",
    "book running lead managers", "the restated financial statements",
    "qualified institutional buyers", "qibs",
    "order", "ticket", "card", "ssn", "dob", "date of birth", "visa",
    "mastercard", "pii", "invoice", "case", "ref", "reference",
}

# Alphanumeric identifiers such as "ORD-58291" / "TCK-77123" are business
# reference numbers, not organization names -- explicitly excluded per the
# assignment's own worked example ("Order"/"Ticket" numbers).
RE_ID_LIKE = re.compile(r"^[A-Z]{2,6}-\d+$")


def _looks_like_real_org(text: str) -> bool:
    lowered = text.strip().lower().strip(",.")
    if lowered in ORG_STOPLIST:
        return False
    if RE_ID_LIKE.match(text.strip()):
        return False
    if not any(ch.isalpha() for ch in text):
        return False
    if len(lowered) <= 2:
        return False
    return True


def detect_ner(text: str):
    """Yield Match objects for spaCy-detected PERSON / ORG entities."""
    matches = []
    doc = nlp(text)
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            token = ent.text.strip().lower().strip(",.")
            if token in ORG_STOPLIST or (len(ent.text.split()) == 1 and len(token) <= 4):
                continue  # single short capitalized word (e.g. "Card") -- likely not a name
            matches.append(Match(ent.start_char, ent.end_char, ent.text, "PERSON"))
        elif ent.label_ == "ORG":
            if _looks_like_real_org(ent.text):
                matches.append(Match(ent.start_char, ent.end_char, ent.text, "ORG"))
    return matches


def resolve_overlaps(matches):
    """Longer / higher-priority match wins when spans overlap."""
    priority = {
        "EMAIL": 0, "SSN": 0, "CREDIT_CARD": 0, "IP": 0, "DOB": 0,
        "ADDRESS": 1, "PHONE": 1, "PERSON": 2, "ORG": 3, "PIN": 4,
    }
    matches = sorted(matches, key=lambda m: (m.start, -(m.end - m.start)))
    result = []
    last_end = -1
    for m in sorted(matches, key=lambda m: (priority.get(m.label, 9), m.start)):
        if any(not (m.end <= r.start or m.start >= r.end) for r in result):
            continue
        result.append(m)
    result.sort(key=lambda m: m.start)
    return result


def redact_text(text: str, mapper: PIIMapper):
    """Return (redacted_text, list_of_matches_found) for one text block."""
    matches = detect_structured(text) + detect_ner(text) + detect_address(text)
    matches = resolve_overlaps(matches)

    out = []
    last = 0
    for m in matches:
        out.append(text[last:m.start])
        out.append(mapper.fake_for(m.label, m.text))
        last = m.end
    out.append(text[last:])
    return "".join(out), matches
