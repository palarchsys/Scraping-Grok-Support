from sscraping.scrape.html import extract_article


def test_extract_article_selectors() -> None:
    html = """
    <html><body>
      <h1>Titre réel</h1>
      <article><p>Corps pédagogique.</p><script>void 0</script></article>
    </body></html>
    """
    title, body = extract_article(html, {"title": "h1", "body": "article"})
    assert title == "Titre réel"
    assert "Corps pédagogique" in body
    assert "void" not in body


def test_og_title_fallback() -> None:
    html = '<html><head><meta property="og:title" content="Via OG"></head><body><main>Texte</main></body></html>'
    title, body = extract_article(html, {"title": "h1", "body": "main"})
    assert title == "Via OG"
    assert "Texte" in body
