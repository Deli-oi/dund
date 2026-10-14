import pytest

from dund.entities import EntityResolver, TickerTable

ROWS = [
    ("AAPL", "Apple Inc.", "0000320193"), ("AMD", "ADVANCED MICRO DEVICES INC", "0000002488"),
    ("TSLA", "Tesla, Inc.", "0001318605"), ("NVDA", "NVIDIA CORP", "0001045810"),
    ("K", "KELLANOVA", "0000055067"), ("L", "LOEWS CORP", "0000060086"),
    ("D", "DOMINION ENERGY, INC.", "0000715957"), ("P", "PANDORA", "0001230276"),
    ("N", "NETSOL TECHNOLOGIES", "0001039280"), ("IT", "GARTNER INC", "0000749251"),
    ("ALL", "ALLSTATE CORP", "0000899051"),
    ("ARE", "ALEXANDRIA REAL ESTATE EQUITIES", "0001035443"),
    ("ON", "ON SEMICONDUCTOR CORP", "0001097864"), ("A", "AGILENT TECHNOLOGIES, INC.", "0001090872"),
    ("GME", "GAMESTOP CORP.", "0001326380"), ("PLTR", "Palantir Technologies Inc.", "0001321655"),
    ("MSFT", "MICROSOFT CORP", "0000789019"), ("TGT", "Target Corp", "0000027419"),
]
R = EntityResolver(TickerTable.from_rows(ROWS))


def ids(c, typ="stock"):
    return {x.id for x in c if x.entity_type == typ}


def test_cashtag_basic():
    c = R.resolve("Loading up on $TSLA calls")
    assert ids(c) == {"TSLA"}
    assert c[0].match_type == "cashtag" and c[0].confidence >= 0.9


def test_cashtag_unlisted_ignored():
    assert not R.resolve("$ZZZZ to the moon")


@pytest.mark.parametrize("t", ["K", "L", "D", "P", "N"])
def test_single_letter_cashtag_math_rejected(t):
    c = R.resolve("Attention with $%s keys and queries" % t, "softmax over $%s dims" % t)
    assert not ids(c)


def test_single_letter_cashtag_no_finance_rejected():
    assert not ids(R.resolve("Let $K be the number of clusters and $D the data size"))


def test_single_letter_cashtag_with_finance_context_allowed():
    c = R.resolve("Bought $D shares, dividend looks great, stock is cheap")
    assert ids(c) == {"D"}
    assert c[0].confidence < 0.9


@pytest.mark.parametrize("word", ["IT", "ALL", "ARE", "ON", "A"])
def test_common_word_tickers_not_bare(word):
    c = R.resolve("I think %s stock market is crazy, buy calls %s" % (word, word))
    assert word not in ids(c)


def test_bare_ticker_with_finance_context():
    c = R.resolve("GME earnings tomorrow, buying calls")
    hit = [x for x in c if x.id == "GME"]
    assert hit and hit[0].match_type == "bare_ticker"


def test_bare_ticker_without_context_rejected():
    assert "PLTR" not in ids(R.resolve("PLTR was a fun project name"))


def test_bare_ticker_parenthesized():
    assert "PLTR" in ids(R.resolve("Some news from (PLTR) today"))


def test_all_caps_title_suppresses_bare():
    assert "GME" not in ids(R.resolve("WHY IS EVERYONE TALKING ABOUT GME TODAY OK"))


def test_company_name_amd():
    c = R.resolve("Advanced Micro Devices announces new chips")
    assert ids(c) == {"AMD"}
    assert c[0].match_type == "company_name"


def test_company_name_normalization_suffix_and_case():
    assert "TSLA" in ids(R.resolve("Tesla, Inc. is up"))
    assert "NVDA" in ids(R.resolve("Nvidia Corporation reported"))


def test_generic_single_word_not_matched():
    assert not ids(R.resolve("my target for this year is 10 pounds"))


def test_github_url_is_repo_not_stock():
    c = R.resolve("New library", "", "https://github.com/pytorch/pytorch")
    assert ids(c, "repo") == {"pytorch/pytorch"}
    assert not ids(c)
    assert c[0].match_type == "github_repo"


def test_github_owner_ticker_like_not_stock():
    c = R.resolve("check this out", "see https://github.com/AMD/ROCm/tree/main")
    assert "AMD/ROCm" in ids(c, "repo")
    assert not ids(c)


def test_dedup_and_boost_across_match_types():
    c = R.resolve("$AAPL", "Apple Inc. earnings were strong")
    assert len([x for x in c if x.id == "AAPL"]) == 1
    assert c[0].confidence > 0.9


def test_multiple_entities_sorted():
    c = R.resolve("$MSFT vs advanced micro devices")
    assert [x.id for x in c] == ["MSFT", "AMD"]


# ---- resolver tuning on real posts (docs/33-resolver-tuning.md) ----
ROWS2 = ROWS + [
    ("GOOG", "Alphabet Inc.", "0001652044"), ("GOOGL", "Alphabet Inc.", "0001652044"),
    ("META", "Meta Platforms, Inc.", "0001326801"), ("XYZ", "Block, Inc.", "0001512673"),
    ("BRK-A", "BERKSHIRE HATHAWAY INC", "0001067983"),
    ("BRK-B", "BERKSHIRE HATHAWAY INC", "0001067983"),
    ("AMZN", "AMAZON COM INC", "0001018724"), ("F", "FORD MOTOR CO", "0000037996"),
    ("MOMO", "Hello Group Inc.", "0001610601"), ("RDDT", "Reddit, Inc.", "0001713445"),
    ("UK", "Ucommune International Ltd", "0001821424"), ("HOOD", "Robinhood Markets, Inc.", "0001783879"),
    ("IP", "INTERNATIONAL PAPER CO /NEW/", "0000051434"), ("CVS", "CVS HEALTH CORP", "0000064803"),
    ("SPY", "SPDR S&P 500 ETF TRUST", "0000884394"),
    ("WFC", "WELLS FARGO & COMPANY/MN", "0000072971"),
    ("GE", "GENERAL ELECTRIC CO", "0000040545"),
    ("XX1", "Acme Corp", "0000000001"), ("XX2", "Acme Corp", "0000000002"),
]
R2 = EntityResolver(TickerTable.from_rows(ROWS2))


def test_lowercase_cashtag():
    c = R2.resolve("$amzn bye bye puts")
    assert ids(c) == {"AMZN"} and c[0].match_type == "cashtag"


def test_lowercase_common_word_cashtag_rejected():
    assert not ids(R2.resolve("costs me $it every time, $all gone"))


def test_class_share_brk_dot_b():
    assert ids(R2.resolve("BRK.B + VTI Investing Strategy")) == {"BRK-B"}
    assert ids(R2.resolve("long $BRK.B for years")) == {"BRK-B"}


def test_alias_google_and_facebook():
    assert ids(R2.resolve("Google to acquire Fitbit")) == {"GOOGL"}
    assert ids(R2.resolve("Facebook earnings, stock falls")) == {"META"}


def test_renamed_cashtag_alias_fb_sq():
    assert ids(R2.resolve("Short $FB here")) == {"META"}
    assert ids(R2.resolve("my $SQ puts printed")) == {"XYZ"}


def test_cik_dedup_share_classes():
    c = R2.resolve("$GOOG vs $GOOGL, Alphabet is cheap")
    assert len([x for x in c if x.cik == "0001652044"]) == 1
    c = R2.resolve("Google stock is up", "$GOOG calls")
    assert ids(c) == {"GOOG"}                     # explicit ticker wins over alias target
    assert len(c) == 1


def test_duplicate_company_name_distinct_ciks_is_ambiguous():
    assert not ids(R2.resolve("Acme Corp reported earnings"))


def test_platform_and_generic_names_not_matched():
    assert not ids(R2.resolve("Hello everyone, People ask about Reddit and Robinhood"))
    assert not ids(R2.resolve("I bought paper at the store and a visa for the trip, stock up"))


def test_single_word_name_needs_finance_context():
    assert "AMZN" in ids(R2.resolve("Amazon earnings tomorrow"))
    assert not ids(R2.resolve("Ucommune was fun"))


def test_country_and_jargon_not_bare_tickers():
    assert not ids(R2.resolve("UK citizen buying stock, what tax do I pay? EU options broker"))


def test_two_letter_bare_needs_stronger_context():
    assert not ids(R2.resolve("GE wins"))
    assert "GE" not in ids(R2.resolve("With cases like GE, the defensive stocks"))  # one finance word
    assert "GE" in ids(R2.resolve("GE earnings next week, buying calls"))


def test_bare_ticker_followed_by_price():
    assert "TSLA" in ids(R2.resolve("We did it boys TSLA $420.69"))
    assert "CVS" in ids(R2.resolve("$116K in CVS play about to break even"))


def test_jurisdiction_tag_stripped_from_name():
    assert "WFC" in ids(R2.resolve("Wells Fargo is being investigated"))


def test_name_index_fast():
    import time
    big = TickerTable.from_rows(
        [("T%d" % i, "Company Number %d Holdings" % i, "%010d" % i) for i in range(5000)] + ROWS)
    r = EntityResolver(big)
    t0 = time.time()
    for _ in range(200):
        r.resolve("Some post about Nvidia and nothing else", "lorem ipsum " * 50)
    assert time.time() - t0 < 2.0
