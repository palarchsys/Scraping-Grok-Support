from sscraping.nlp.connectors.openai_compat import _strip_fence


def test_strip_fence() -> None:
    raw = '```json\n{"is_crime": false}\n```'
    assert _strip_fence(raw) == '{"is_crime": false}'
