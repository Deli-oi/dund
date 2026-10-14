"""Run entity resolver over finished census files.  Usage: python -I resolver_eval_run.py OUT.json
Writes counts, top tickers, rejected cashtags and seeded samples (as JSON)."""
import glob, gzip, json, os, random, re, sys
from collections import Counter, defaultdict
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from dund.entities import EntityResolver, TickerTable, CASHTAG_RE, URL_RE

DATA = r"C:\Users\dalele\dund-data\posts_v3"
TICK = r"C:\Users\dalele\dund-data\entities\sec_20261014\out\tickers.csv"
PH = {"[removed]", "[deleted]"}

def clean(v):
    return "" if not isinstance(v, str) or v.strip() in PH else v

def main(out):
    res = EntityResolver(TickerTable.from_csv(TICK))
    rows = TickerTable.from_csv(TICK).rows
    posts = Counter(); hit = Counter(); tops = defaultdict(Counter); rej = defaultdict(Counter)
    rej_all = Counter(); cand_pool = []; dollar_none = []
    rng = random.Random(42); names = Counter()
    for fp in sorted(glob.glob(os.path.join(DATA, "*.jsonl.gz"))):
        base = os.path.basename(fp)[:-len(".jsonl.gz")]
        sub, ym = base.rsplit("_", 1); year = ym[:4]
        with gzip.open(fp, "rt", encoding="utf-8") as fh:
            for line in fh:
                try: d = json.loads(line)
                except Exception: continue
                t, s, u = clean(d.get("title")), clean(d.get("selftext")), d.get("url") if isinstance(d.get("url"), str) else ""
                g = (sub, year); posts[g] += 1
                allc, rjs = res.resolve_ex(t, s, u) if hasattr(res, "resolve_ex") else (res.resolve(t, s, u), None)
                cs = [c for c in allc if c.entity_type == "stock"]
                for c in cs:
                    if c.match_type == "company_name": names[c.evidence] += 1
                text = URL_RE.sub(" ", t + "\n" + s)
                if cs:
                    hit[g] += 1
                    for c in cs: tops[g][c.id] += 1
                    for c in cs: cand_pool.append((d.get("id"), g, c.id, c.match_type, round(c.confidence, 2), t, s))
                if rjs is not None:
                    for raw, kind, why in rjs:
                        rej[g][(raw, kind + ":" + why)] += 1; rej_all[(raw, kind + ":" + why)] += 1
                elif "$" in (t + s):
                    for m in CASHTAG_RE.finditer(text):
                        tk = m.group(1)
                        if tk not in {c.id for c in cs} or tk not in rows:
                            why = "not_in_ticker_table" if tk not in rows else "context_filter(single-letter/math/no-finance)" if len(tk) == 1 else "other"
                            rej[g][(tk, why)] += 1; rej_all[(tk, why)] += 1
                if "$" in (t + s) and not cs:
                    dollar_none.append((d.get("id"), g, t, s))
    sample_c = rng.sample(cand_pool, min(150, len(cand_pool)))
    sample_n = rng.sample(dollar_none, min(100, len(dollar_none)))
    json.dump({
        "posts": {f"{a}|{b}": v for (a, b), v in posts.items()},
        "hit": {f"{a}|{b}": v for (a, b), v in hit.items()},
        "tops": {f"{a}|{b}": c.most_common(40) for (a, b), c in tops.items()},
        "rej": {f"{a}|{b}": [[k[0], k[1], n] for k, n in c.most_common(40)] for (a, b), c in rej.items()},
        "rej_all": [[k[0], k[1], n] for k, n in rej_all.most_common(40)],
        "names": names.most_common(200), "n_cand": len(cand_pool), "n_dollar_none": len(dollar_none),
        "pool_keys": [[i, tk] for i, g, tk, mt, cf, t, s in cand_pool],
        "sample_c": [[i, f"{g[0]}|{g[1]}", tk, mt, cf, t[:400], s[:600]] for i, g, tk, mt, cf, t, s in sample_c],
        "sample_n": [[i, f"{g[0]}|{g[1]}", t[:400], s[:800]] for i, g, t, s in sample_n],
    }, open(out, "w", encoding="utf-8"), indent=1)

main(sys.argv[1])
