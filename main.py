#!/usr/bin/env python

import requests
from aiohttp import web
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator

POSTOJ_CATEGORY_URLS = [
    'https://www.postoj.sk/komentare-nazory',
    'https://www.postoj.sk/politika',
    'https://www.postoj.sk/spolocnost',
    'https://www.postoj.sk/kultura',
    'https://www.postoj.sk/rodina',
    'https://svetkrestanstva.postoj.sk/svet-krestanstva',
]


def create_feed_generator():
    fg = FeedGenerator()
    fg.id('https://github.com/fadawar/postoj-rss')
    fg.title('Postoj.sk')
    fg.author({'name': 'Postoj.sk'})
    fg.link(href='https://www.postoj.sk', rel='alternate')
    fg.logo('https://www.postoj.sk/assets/frontend/build/img/brand-main.png')
    fg.subtitle('Konzervatívny denník')
    fg.language('sk')
    return fg


async def scrape(request):
    fg = create_feed_generator()
    for url in POSTOJ_CATEGORY_URLS:
        response = requests.get(url)
        page = BeautifulSoup(response.content, 'html.parser')
        articles = page.select('article.listing-article')
        for article in articles:
            fe = fg.add_entry()
            fe.id(article.select_one('h3 a').get('href'))
            fe.title(article.select_one('h3 a').text.strip())
            fe.link(href=article.select_one('h3 a').get('href'))
            fe.description(article.select_one('div.perex p').text.strip())
    return web.Response(text=fg.atom_str(pretty=True).decode("utf-8"))


app = web.Application()
app.router.add_get('/', scrape)

if __name__ == '__main__':
    web.run_app(app, host='localhost', port=5000)
