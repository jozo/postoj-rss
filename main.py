#!/usr/bin/env python
import asyncio
from datetime import datetime, timezone

import aiohttp
from aiohttp import web
from bs4 import BeautifulSoup
from feedgen.entry import FeedEntry
from feedgen.feed import FeedGenerator

POSTOJ_CATEGORY_URLS = [
    "https://www.postoj.sk/komentare-nazory",
    "https://www.postoj.sk/politika",
    "https://www.postoj.sk/spolocnost",
    "https://www.postoj.sk/kultura",
    "https://www.postoj.sk/rodina",
    "https://svetkrestanstva.postoj.sk/svet-krestanstva",
]


async def scrape(request):
    start = datetime.now()
    fg = create_feed_generator()
    async with aiohttp.ClientSession() as session:
        tasks = [scrape_articles(session, url) for url in POSTOJ_CATEGORY_URLS]
        for coroutine in asyncio.as_completed(tasks):
            entries = await coroutine
            for entry in entries:
                fg.add_entry(entry)
    delta = datetime.now() - start
    print(f"Feed generated in {delta}!")
    return web.Response(text=fg.atom_str(pretty=True).decode("utf-8"))


def create_feed_generator():
    fg = FeedGenerator()
    fg.id("https://github.com/fadawar/postoj-rss")
    fg.title("Postoj.sk")
    fg.author({"name": "Postoj.sk"})
    fg.link(href="https://www.postoj.sk", rel="alternate")
    fg.logo("https://www.postoj.sk/assets/frontend/build/img/brand-main.png")
    fg.subtitle("Konzervatívny denník")
    fg.language("sk")
    return fg


async def scrape_articles(session, url):
    entries = []
    async with session.get(url) as resp:
        if resp.status == 200:
            body = await resp.text()
            page = BeautifulSoup(body, "html.parser")
            articles = page.select(".author-main article")
            for article in articles:
                entry = await create_entry(article)
                entries.append(entry)
    print(f"URL: {resp.status} - {len(entries)} articles - {url}")
    return entries


async def create_entry(article):
    heading = article.select_one(".main-article-heading-box")
    entry = FeedEntry()
    entry.id(heading.select_one("a").get("href"))
    entry.link(href=heading.select_one("a").get("href"))
    entry.title(" / ".join(s.text for s in heading.select("span")))
    name = article.select_one(".main-article-author-box a").text.strip()
    entry.author({"name": name})
    entry.summary(article.select_one(".perex-lim").text.strip())
    date = article.select_one(".main-article-author-box small").text.strip()
    date = datetime.strptime(date, "%d.%m.%Y, %H:%M")
    entry.published(date.replace(tzinfo=timezone.utc))
    return entry


app = web.Application()
app.add_routes([web.get("/", scrape)])

if __name__ == "__main__":
    web.run_app(app, host="localhost", port=5000)
