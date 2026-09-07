from sscraping.nlp.connectors.openai_compat import _strip_fence


def test_strip_fence() -> None:
    raw = '```json\n{"is_aggression": false}\n```'
    assert _strip_fence(raw) == '{"is_aggression": false}'
