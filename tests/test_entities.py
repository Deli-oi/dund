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
