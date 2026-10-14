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
# lower/mixed-case cashtags ($amzn, $Goos) and class shares ($BRK.B); resolved after the strict form
CASHTAG_ANY_RE = re.compile(r"(?<![\w$])\$([A-Za-z]{1,5})(?:[.\-]([A-Za-z]))?(?![A-Za-z0-9])")
CLASS_SHARE_RE = re.compile(r"(?<![\w$.\-/])([A-Z]{1,4})[./\-]([AB])(?![\w$])")
PRICE_AFTER_RE = re.compile(r"\s+\$?\d")
MONEY_BEFORE_RE = re.compile(r"\$\d[\d.,]*\s?[kKmMbB]?\s+(?:in|on|into)\s+$")
BARE_RE = re.compile(r"(?<![\w$.\-/])([A-Z]{2,5})(?![\w$])")

FINANCE_WORDS = {
    "stock", "stocks", "share", "shares", "calls", "puts", "call", "put",
    "earnings", "buy", "buying", "sell", "bullish", "bearish", "dividend",
    "dividends", "ticker", "price", "market", "options", "strike", "short",
    "long", "etf", "invest", "investing", "portfolio", "premarket", "ipo",
    "eps", "nasdaq", "nyse", "yolo", "shorting", "squeeze", "valuation", "rally",
    "plays", "puts", "gains", "tendies", "dip", "trade", "trades", "trading",
    "revenue", "profit", "quarter", "shareholders",
    "million", "billion", "ceo", "merger", "acquisition", "acquire", "acquires",
    "lawsuit", "antitrust", "guidance", "stonk", "stonks", "bagholder", "tendie",
    "expiry", "expiration", "otc", "pump", "dump", "bonds",
}
MATH_WORDS = {
    "matrix", "kernel", "gradient", "loss", "tensor", "vector", "dimension",
    "dimensions", "lemma", "theorem", "equation", "latex", "sigma", "softmax",
    "attention", "embedding", "weights", "epsilon", "logits", "norm",
    "pytorch", "tensorflow", "cuda", "arxiv", "dataset", "datasets", "neural",
    "backprop", "transformer", "transformers", "llm", "llms", "finetune",
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
    # round 2 (real-post tuning): countries/regions, trading jargon, generic acronyms
    "UK", "EU", "ET", "ES", "PR", "PDT", "AP", "NC", "VIP", "ACA", "ASH", "RS",
    "CMC", "FUND", "COO", "RBC", "PE", "PS", "PT", "TA", "RSI", "EMA", "SMA",
    "MACD", "ATH", "ATL", "DCA", "IRA", "ROTH", "HSA", "WSB", "OTC", "CAGR",
    "ROI", "YTD", "QE", "IRS", "SPAC", "ER", "EOD", "ITM", "OTM", "ATM", "IV",
    "DTE", "FD", "FDS", "ETH", "UAE", "EV", "VR", "AR", "HR", "PC", "TV", "PA",
    "NY", "LA", "CA", "TX", "FL", "DC", "UN", "NATO", "OPEC", "FOMC", "CPI",
    "PPI", "NFP", "LLC", "PEG", "RE", "VS", "IR", "QA", "ID", "OS", "AWS",
    "USD", "EUR", "GBP", "CAD", "JPY", "BTC", "TBH", "IIRC", "AFAIK", "HODL",
    "FOMO", "BRO", "MAN", "BOY", "GUY", "TAX", "WAR", "WIN", "LOSS", "GAIN",
    "RISK", "FIRE", "LAND", "WORK", "FIRST", "ONLY", "MOST", "SOME", "LESS",
    "MORE", "THEY", "THAT", "THIS", "WITH", "FROM", "HAVE", "WILL", "BEEN",
    "JUST", "LIKE", "WHAT", "WHEN", "THEN", "THAN", "THEM", "SAME", "ALSO",
    "ANY", "CAR", "BAD", "SHOP", "HOME", "PAY", "DAY", "MAY", "CAP", "ACT",
    "BEAT", "BULL", "BEAR", "PUMP", "DUMP", "MOON", "DIP", "RIP", "BAG", "ARM",
    "RTX", "GTX", "ICLR", "NIPS", "NYC", "DNA", "AGI", "CV", "NN", "IP", "DB", "PD",
    "SF", "RA", "MD", "VC", "PI", "MA", "TD", "IEX", "CSV", "FCF", "BAND", "NET",
    "HERE", "POST", "LOT", "ATR", "ADX", "SVM", "GMM", "MCS", "ASR", "UCL", "CLUS",
    "RNA", "NGS", "FIX", "TRX", "NMT", "UI", "TILE", "ICO", "ROE", "ROA", "EBIT",
    "COMP", "HELP", "OC", "CD", "AZ", "LTM", "PRE", "LAKE",
    "GAP", "HUGE", "WEEK", "YEAR", "NEXT", "LAST", "MAKE", "TAKE", "CALL",
    "PUT", "BUY", "SELL", "LONG", "SHORT", "GOLD", "OIL", "GAS", "CORN",
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


# Brand/alias names -> (ticker, needs_finance_context).  Only used when the ticker
# is present in the table (so tests with small tables are unaffected).  Several
# of these are also ordinary words, hence the context flag.
NAME_ALIASES = {
    "google": ("GOOGL", False), "alphabet": ("GOOGL", False),
    "facebook": ("META", False), "meta platforms": ("META", False),
    "berkshire": ("BRK-B", True), "berkshire hathaway": ("BRK-B", False),
    "amazon": ("AMZN", False), "apple": ("AAPL", False), "tesla": ("TSLA", False),
    "telsa": ("TSLA", True), "microsoft": ("MSFT", False), "netflix": ("NFLX", False),
    "nvidia": ("NVDA", False), "intel": ("INTC", False), "boeing": ("BA", False),
    "disney": ("DIS", False), "starbucks": ("SBUX", False), "walmart": ("WMT", False),
    "paypal": ("PYPL", False), "uber": ("UBER", False), "lyft": ("LYFT", False),
    "ford": ("F", True), "jpmorgan": ("JPM", False), "jp morgan": ("JPM", False), "goldman": ("GS", True),
    "goldman sachs": ("GS", False), "morgan stanley": ("MS", False),
    "coca cola": ("KO", False), "pepsi": ("PEP", False),
    "mcdonalds": ("MCD", False), "mcdonald s": ("MCD", False), "costco": ("COST", False),
    "at and t": ("T", False), "verizon": ("VZ", False), "exxon": ("XOM", False),
    "exxon mobil": ("XOM", False), "chevron": ("CVX", False), "pfizer": ("PFE", False),
    "moderna": ("MRNA", False), "gamestop": ("GME", False), "amc entertainment": ("AMC", False),
    "coinbase": ("COIN", False), "palantir": ("PLTR", False),
    "salesforce": ("CRM", False), "oracle": ("ORCL", True), "adobe": ("ADBE", False),
    "qualcomm": ("QCOM", False), "micron": ("MU", False), "spotify": ("SPOT", False),
}
# Platforms, indices, places and generic words that are NOT a mention of the
# stock even though a company name normalizes to them (checked on full name).
NAME_BLOCK = {
    "robinhood", "interactive brokers", "webull", "wealthfront", "td ameritrade",
    "charles schwab", "schwab", "acorns", "stash", "betterment", "nasdaq", "nyse",
    "strategy", "paper", "korea", "coffee", "senior", "taiwan", "orange", "founder",
    "workshop", "genius", "frontier", "joint", "lithium", "stem cell",
    "quantum computing", "bancorp", "financial institutions", "york times",
    "usa today", "oppenheimer", "visa", "snap", "target", "square", "block",
    "reddit", "hello", "people", "here", "post", "buckle", "noble", "waters",
}
# Renamed / merged tickers that people still write as cashtags or tickers.
TICKER_ALIASES = {"FB": "META", "SQ": "XYZ", "GPS": "GAP", "BRK.B": "BRK-B",
                  "BRK.A": "BRK-A", "BRKB": "BRK-B", "BF.B": "BF-B", "GOOGL": "GOOGL"}
# Normalized single names that are ordinary words / platforms / places (found by
# eyeballing top company_name false positives in the census).
SINGLE_NAME_BLOCK |= {
    "hello", "people", "emerging", "reddit", "bullish", "honest", "germany",
    "morgan", "morning", "income", "pacific", "premium", "here", "post", "stock",
    "momentum", "spirit", "express", "century", "central", "western", "eastern",
    "northern", "southern", "mexico", "china", "india", "japan", "brazil", "canada",
    "russia", "europe", "asia", "africa", "world", "market", "markets", "alpha",
    "growth", "value", "income", "total", "royal", "liberty", "freedom", "summit",
    "pioneer", "premier", "select", "universal", "advanced", "applied", "innovative",
    "quantum", "crypto", "intelligent", "pattern", "track", "click", "reading",
    "service", "gold", "silver", "oil", "life", "home", "good", "fund", "trust",
    "enterprise", "enterprises", "medical", "healthcare", "pharmaceuticals",
    "entertainment", "media", "interactive", "solutions", "products", "brands",
    "realty", "properties", "mining", "minerals", "exploration", "metals",
    "street", "wall", "river", "mountain", "ocean", "island", "bay", "park",
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


def normalize_name(s: str, is_title: bool = False) -> str:
    if is_title:   # SEC titles: "/DE/", "/NEW/", "COMPANY/MN" jurisdiction tags
        s = re.sub(r"/[A-Za-z]{1,4}(?:/|\s*$)", " ", s)
    s = s.lower().replace("&", " and ")
    s = re.sub(r"[^a-z0-9 ]+", " ", s)
    toks = [t for t in s.split() if t not in NAME_STOP]
    while toks and toks[-1] == "and":      # "Wells Fargo & Company" -> "wells fargo"
        toks.pop()
    return " ".join(toks)


def _canon_rank(ticker: str):
    """Preference among tickers of one CIK: plain common stock, then shortest."""
    return (("-" in ticker) or ("." in ticker), len(ticker), ticker)


@dataclass
class TickerTable:
    rows: dict = field(default_factory=dict)    # ticker -> (title, cik)
    names: dict = field(default_factory=dict)   # normalized name -> ticker (unambiguous only)
    ambiguous: set = field(default_factory=set)  # names shared by >1 CIK (never matched)
    aliases: dict = field(default_factory=dict)  # alias name -> (ticker, needs_finance)
    index: dict = field(default_factory=dict)    # first token -> [(tokens tuple, ticker, needs_finance)]
    by_cik: dict = field(default_factory=dict)   # cik -> [tickers]

    @classmethod
    def from_rows(cls, rows):
        t = cls()
        by_name: dict = {}   # normalized name -> {cik: [tickers]}
        for ticker, title, cik in rows:
            ticker = ticker.upper()
            t.rows[ticker] = (title, cik)
            t.by_cik.setdefault(cik, []).append(ticker)
            n = normalize_name(title, is_title=True)
            if n:
                by_name.setdefault(n, {}).setdefault(cik, []).append(ticker)
        for n, ciks in by_name.items():
            if len(ciks) > 1:
                t.ambiguous.add(n)      # unrelated issuers with the same name
                continue
            tickers = next(iter(ciks.values()))
            t.names[n] = min(tickers, key=_canon_rank)
        for a, (tk, needs) in NAME_ALIASES.items():
            if tk in t.rows:
                t.aliases[a] = (tk, needs)
        # precompiled phrase index keyed on the first token
        for n, tk in t.names.items():
            if n in t.aliases:
                continue
            toks = tuple(n.split())
            t.index.setdefault(toks[0], []).append((toks, tk, False))
        for a, (tk, needs) in t.aliases.items():
            toks = tuple(a.split())
            t.index.setdefault(toks[0], []).append((toks, tk, needs))
        return t

    def canonical(self, ticker: str) -> str:
        """Map renamed/class-share spellings onto a table ticker ('' if unknown)."""
        tk = TICKER_ALIASES.get(ticker, ticker)
        return tk if tk in self.rows else ""

    @classmethod
    def from_csv(cls, path):
        with open(Path(path), newline="", encoding="utf-8") as f:
            return cls.from_rows((r["ticker"], r["title"], r["cik"]) for r in csv.DictReader(f))


class EntityResolver:
    def __init__(self, table: TickerTable):
        self.table = table

    def resolve(self, title: str = "", selftext: str = "", url: str = "") -> list:
        return self.resolve_ex(title, selftext, url)[0]

    def resolve_ex(self, title: str = "", selftext: str = "", url: str = ""):
        """Return (candidates, rejected); rejected is [(raw_token, kind, reason)]."""
        out: dict = {}
        rejected: list = []
        rows = self.table.rows

        def add(c: Candidate):
            # CIK dedup: GOOG/GOOGL, BRK-A/BRK-B are one company; one candidate per issuer.
            k = (c.entity_type, c.id)
            if c.entity_type == "stock" and c.cik and k not in out:
                for ok, oc in list(out.items()):
                    if oc.entity_type == "stock" and oc.cik == c.cik:
                        if c.match_type == "company_name" or oc.match_type != "company_name":
                            # keep the existing ticker, boost it
                            c = Candidate(oc.entity_type, oc.id, c.confidence, c.match_type,
                                          oc.name, oc.cik, c.evidence)
                            k = ok
                        else:
                            del out[ok]   # explicit ticker beats a name-derived share class
                        break
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
        n_fin = len({t for t in low if t in FINANCE_WORDS})
        finance = n_fin > 0
        mathy = any(t in MATH_WORDS for t in low) or "\\" in text or "$$" in text

        letters = [c for c in title if c.isalpha()]
        shouting = len(letters) > 8 and sum(c.isupper() for c in letters) / len(letters) > 0.7

        # (a) cashtags: $TSLA, $amzn, $Goos, $BRK.B, $FB (renamed)
        for m in CASHTAG_ANY_RE.finditer(text):
            raw, cls_ = m.group(1), m.group(2)
            strict = raw.isupper() and (cls_ is None or cls_.isupper())
            if cls_:
                tk = (self.table.canonical(f"{raw.upper()}.{cls_.upper()}")
                      or self.table.canonical(f"{raw.upper()}-{cls_.upper()}"))
            else:
                tk = self.table.canonical(raw.upper())
            if not tk:
                rejected.append((m.group(0), "cashtag", "not_in_table"))
                continue
            name, cik = rows[tk]
            if len(tk) == 1 and not cls_:
                # math notation unless strongly supported by finance context
                if not strict:
                    continue
                if mathy:
                    rejected.append((m.group(0), "cashtag", "single_letter_math_context"))
                    continue
                if not finance:
                    rejected.append((m.group(0), "cashtag", "single_letter_no_finance_context"))
                    continue
                conf = 0.6
            elif strict:
                conf = 0.7 if (mathy and not finance) else 0.9
            else:
                if raw.upper() in COMMON_WORDS or len(raw) < 2:
                    rejected.append((m.group(0), "cashtag", "lowercase_common_word"))
                    continue
                if mathy and not finance:
                    rejected.append((m.group(0), "cashtag", "lowercase_math_context"))
                    continue
                conf = 0.75 if finance else 0.65
            add(Candidate("stock", tk, conf, "cashtag", name, cik, m.group(0)))

        # (c) company names (first, so bare tickers can be corroborated)
        name_hits = set()
        for ticker, evidence in self._name_matches(text, finance):
            name, cik = rows[ticker]
            name_hits.add(ticker)
            add(Candidate("stock", ticker, 0.75, "company_name", name, cik, evidence))

        # (b) bare uppercase tickers, only with context
        for m in BARE_RE.finditer(text):
            raw = m.group(1)
            tk = raw if raw in rows else (self.table.canonical(raw) if raw in TICKER_ALIASES else "")
            if not tk:
                continue
            if raw in COMMON_WORDS:
                rejected.append((raw, "bare", "common_word"))
                continue
            if shouting:
                continue
            before = text[m.start() - 1] if m.start() else ""
            after = text[m.end()] if m.end() < len(text) else ""
            paren = before == "(" and after == ")"
            price = len(tk) >= 3 and bool(
                PRICE_AFTER_RE.match(text, m.end())
                or MONEY_BEFORE_RE.search(text[max(0, m.start() - 24):m.start()]))
            corroborated = paren or tk in name_hits
            if not (finance or corroborated or price):
                continue
            if len(tk) == 2 and not (corroborated or price or n_fin >= 2):
                rejected.append((raw, "bare", "two_letter_weak_context"))
                continue
            if mathy and not corroborated:
                continue
            name, cik = rows[tk]
            add(Candidate("stock", tk, 0.7 if (corroborated or price) else 0.5, "bare_ticker",
                          name, cik, raw))

        # (d) class shares written BRK.B / BRK/B
        for m in CLASS_SHARE_RE.finditer(text):
            tk = self.table.canonical(f"{m.group(1)}-{m.group(2)}")
            if tk and (len(m.group(1)) >= 3 or finance):
                name, cik = rows[tk]
                add(Candidate("stock", tk, 0.85, "bare_ticker", name, cik, m.group(0)))

        return sorted(out.values(), key=lambda c: (-c.confidence, c.id)), rejected

    def _name_matches(self, text: str, finance: bool = True):
        toks = normalize_name(text).split()
        if not toks:
            return
        caps = set(re.findall(r"\b[A-Z][a-z]+\b", text))
        index = self.table.index
        aliases = self.table.aliases
        seen = set()
        for i, tok in enumerate(toks):
            cands = index.get(tok)
            if not cands:
                continue
            for ntoks, ticker, needs in cands:
                k = len(ntoks)
                if ticker in seen or tuple(toks[i:i + k]) != ntoks:
                    continue
                n = " ".join(ntoks)
                if n in NAME_BLOCK:
                    continue
                if k == 1:
                    if n.upper() in COMMON_WORDS or n.capitalize() not in caps:
                        continue
                    if n not in aliases and (n in SINGLE_NAME_BLOCK or len(n) < 5 or not finance):
                        continue
                if needs and not finance:
                    continue
                seen.add(ticker)
                yield ticker, n
