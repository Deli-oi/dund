"""Entity resolver: map post text to candidate market entities.

Match types: cashtag, bare_ticker, company_name, github_repo.
"""
from __future__ import annotations

import csv
import re
from dataclasses import dataclass, field
from pathlib import Path

GITHUB_RE = re.compile(
    r"github\.com/([A-Za-z0-9](?:[A-Za-z0-9-]{0,38}))/([A-Za-z0-9._-]+)", re.I)
URL_RE = re.compile(r"https?://\S+|www\.\S+|github\.com/\S+", re.I)
CASHTAG_RE = re.compile(r"(?<![\w$])\$([A-Z]{1,5})(?![A-Za-z0-9])")
BARE_RE = re.compile(r"(?<![\w$.\-/])([A-Z]{2,5})(?![\w$])")

FINANCE_WORDS = {
    "stock", "stocks", "share", "shares", "calls", "puts", "call", "put",
    "earnings", "buy", "buying", "sell", "bullish", "bearish", "dividend",
    "dividends", "ticker", "price", "market", "options", "strike", "short",
    "long", "etf", "invest", "investing", "portfolio", "premarket", "ipo",
    "eps", "nasdaq", "nyse", "yolo", "shorting", "squeeze", "valuation", "rally",
}
MATH_WORDS = {
    "matrix", "kernel", "gradient", "loss", "tensor", "vector", "dimension",
    "dimensions", "lemma", "theorem", "equation", "latex", "sigma", "softmax",
    "attention", "embedding", "weights", "epsilon", "logits", "norm",
}
# Tickers that are ordinary English words / ubiquitous acronyms: never match bare.
COMMON_WORDS = {
    "A", "I", "IT", "ALL", "ARE", "ON", "BE", "SO", "AN", "AS", "AT", "BY",
    "DO", "GO", "HE", "IF", "IN", "IS", "ME", "MY", "NO", "OF", "OR", "TO",
    "UP", "US", "WE", "CAN", "FOR", "NOW", "OUT", "ONE", "NEW", "OLD", "BIG",
    "HAS", "WAS", "ANY", "HAD", "HOT", "NEXT", "LOVE", "WELL", "REAL", "VERY",
    "TRUE", "OPEN", "GOOD", "BEST", "FAST", "CASH", "FREE", "LIFE", "PLAY",
    "SAVE", "SEE", "TOO", "TWO", "WHO", "WHY", "YOU", "YOUR", "AM", "PM",
    "CEO", "CFO", "USA", "API", "GPU", "CPU", "LLM", "AI", "ML", "RL", "GDP",
    "FED", "SEC", "IPO", "ETF", "EPS", "DD", "YOLO", "IMO", "EDIT", "TLDR",
    "NYSE", "FAQ", "PDF", "URL", "SQL", "CNN", "RNN", "GAN", "NLP", "OK",
    "ELI", "LOL", "WTF", "FYI", "TIL", "PSA", "AMA", "NEWS", "HOLD", "KEY",
    "LOW", "HIGH", "PEAK", "RUN", "SET", "NET", "TOP", "FUN", "EAT", "RIDE",
    "SHE", "HER", "HIS", "OUR", "THE", "AND", "BUT", "NOT", "ITS",
}
NAME_STOP = {
    "inc", "incorporated", "corp", "corporation", "co", "company", "ltd",
    "limited", "plc", "llc", "lp", "holdings", "holding", "group", "the",
    "sa", "nv", "ag", "se", "de", "cl", "class", "common", "stock", "ord",
    "adr", "trust", "fund", "etf", "new", "intl", "international",
}
# single-word company names too generic to match on their own
SINGLE_NAME_BLOCK = {
    "target", "square", "block", "gap", "visa", "snap", "match", "uber", "meta",
    "ford", "best", "first", "united", "general", "american", "national", "global",
    "energy", "capital", "financial", "bank", "health", "systems", "technologies",
    "technology", "partners", "resources", "industries", "services", "software",
    "networks", "communications", "pharma", "therapeutics", "biosciences",
    "acquisition", "ventures", "digital", "data", "cloud", "power", "water",
}


@dataclass(frozen=True)
class Candidate:
    entity_type: str          # "stock" | "repo"
    id: str                   # ticker or "owner/repo"
    confidence: float
    match_type: str           # cashtag | bare_ticker | company_name | github_repo
    name: str = ""
    cik: str = ""
    evidence: str = ""


def normalize_name(s: str) -> str:
    s = s.lower().replace("&", " and ")
    s = re.sub(r"[^a-z0-9 ]+", " ", s)
    return " ".join(t for t in s.split() if t not in NAME_STOP)


@dataclass
class TickerTable:
    rows: dict = field(default_factory=dict)    # ticker -> (title, cik)
    names: dict = field(default_factory=dict)   # normalized name -> ticker

    @classmethod
    def from_rows(cls, rows):
        t = cls()
        for ticker, title, cik in rows:
            ticker = ticker.upper()
            t.rows[ticker] = (title, cik)
            n = normalize_name(title)
            if n and (n not in t.names or len(ticker) < len(t.names[n])):
                t.names[n] = ticker
        return t

    @classmethod
    def from_csv(cls, path):
        with open(Path(path), newline="", encoding="utf-8") as f:
            return cls.from_rows((r["ticker"], r["title"], r["cik"]) for r in csv.DictReader(f))


class EntityResolver:
    def __init__(self, table: TickerTable):
        self.table = table

    def resolve(self, title: str = "", selftext: str = "", url: str = "") -> list:
        out: dict = {}

        def add(c: Candidate):
            k = (c.entity_type, c.id)
            old = out.get(k)
            if old is None:
                out[k] = c
                return
            best = c if c.confidence > old.confidence else old
            out[k] = Candidate(best.entity_type, best.id, min(0.99, best.confidence + 0.05),
                               best.match_type, best.name, best.cik, best.evidence)

        body = "\n".join(x for x in (title, selftext) if x)

        # GitHub repos are a separate entity type; strip URLs before text matching.
        for m in GITHUB_RE.finditer("\n".join(x for x in (body, url) if x)):
            repo = re.sub(r"(\.git)?[.\-_]*$", "", m.group(2))
            if m.group(1).lower() in {"orgs", "topics", "sponsors", "features"} or not repo:
                continue
            add(Candidate("repo", f"{m.group(1)}/{repo}", 0.95, "github_repo",
                          evidence=m.group(0)))
        text = URL_RE.sub(" ", body)

        low = re.findall(r"[a-z]+", text.lower())
        finance = any(t in FINANCE_WORDS for t in low)
        mathy = any(t in MATH_WORDS for t in low) or "\\" in text or "$$" in text

        letters = [c for c in title if c.isalpha()]
        shouting = len(letters) > 8 and sum(c.isupper() for c in letters) / len(letters) > 0.7

        # (a) cashtags
        for m in CASHTAG_RE.finditer(text):
            tk = m.group(1)
            if tk not in self.table.rows:
                continue
            name, cik = self.table.rows[tk]
            if len(tk) == 1:
                # math notation unless strongly supported by finance context
                if mathy or not finance:
                    continue
                conf = 0.6
            else:
                conf = 0.7 if (mathy and not finance) else 0.9
            add(Candidate("stock", tk, conf, "cashtag", name, cik, m.group(0)))

        # (c) company names (first, so bare tickers can be corroborated)
        name_hits = set()
        for ticker, evidence in self._name_matches(text):
            name, cik = self.table.rows[ticker]
            name_hits.add(ticker)
            add(Candidate("stock", ticker, 0.75, "company_name", name, cik, evidence))

        # (b) bare uppercase tickers, only with context
        for m in BARE_RE.finditer(text):
            tk = m.group(1)
            if tk not in self.table.rows or tk in COMMON_WORDS or shouting:
                continue
            before = text[m.start() - 1] if m.start() else ""
            after = text[m.end()] if m.end() < len(text) else ""
            paren = before == "(" and after == ")"
            corroborated = paren or tk in name_hits
            if not (finance or corroborated):
                continue
            if mathy and not corroborated:
                continue
            name, cik = self.table.rows[tk]
            add(Candidate("stock", tk, 0.7 if corroborated else 0.5, "bare_ticker",
                          name, cik, m.group(0)))

        return sorted(out.values(), key=lambda c: (-c.confidence, c.id))

    def _name_matches(self, text: str):
        norm = " " + normalize_name(text) + " "
        caps = set(re.findall(r"\b[A-Z][a-z]+\b", text))
        for n, ticker in self.table.names.items():
            if " " + n + " " not in norm:
                continue
            if " " not in n:
                if len(n) < 5 or n in SINGLE_NAME_BLOCK or n.upper() in COMMON_WORDS:
                    continue
                if n.capitalize() not in caps:
                    continue
            yield ticker, n
