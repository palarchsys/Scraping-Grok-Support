from pathlib import Path

from sscraping.scrape.rss import parse_feed

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "sample.rss.xml"


def test_parse_rss_demo() -> None:
    arts = parse_feed(FIXTURE.read_text(encoding="utf-8"), "demo", "Europe/Paris")
    assert len(arts) == 1
    assert arts[0].url.endswith("budget-municipal")
    assert "budget" in arts[0].titre.lower()
    assert arts[0].date_publication is not None
