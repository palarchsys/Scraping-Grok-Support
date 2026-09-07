from __future__ import annotations

import scrapy


class ArticleItem(scrapy.Item):
    source = scrapy.Field()
    url = scrapy.Field()
    titre = scrapy.Field()
    texte = scrapy.Field()
    date_publication = scrapy.Field()
    statut = scrapy.Field()
    error = scrapy.Field()
