import logging
import os
from functools import partial

import aiohttp
import anyio
import pymorphy2
from aiohttp import web

from process_article import process_article
from text_tools import split_by_words


MAX_URLS = 10


async def handle(request: web.Request):
    if not 'urls' in request.query:
        return web.json_response({"error": "too few urls in request, should be 1 or more"}, status=400)

    urls = request.query.get('urls', '').split(',')
    if len(urls) > MAX_URLS:
        return web.json_response({"error": "too many urls in request, should be 10 or less"}, status=400)

    if len(urls) < 1:
        return web.json_response({"error": "too few urls in request, should be 1 or more"}, status=400)

    morph = request.app['morph']
    charged_words = request.app['charged_words']

    process_results = []
    async with aiohttp.ClientSession() as session:
        async with anyio.create_task_group() as tg:
            for url in urls:
                tg.start_soon(partial(process_article, session, morph, charged_words, url, process_results))

    request_results = [
        dict(url=result['url'],
             status=result['status'].value,
             score=result['score'],
             words_count=result['words_count'],
             title=result['title'])
        for result in process_results
    ]
    return web.json_response(request_results)


async def make_app():
    app = web.Application()
    app.add_routes([web.get('/', handle)])

    morph = pymorphy2.MorphAnalyzer()
    app['morph'] = morph
    charged_words = set()
    for dict_file in os.listdir('charged_dict'):
        with open(os.path.join('charged_dict', dict_file)) as f:
            charged_words.update(await split_by_words(morph, f.read()))

    app['charged_words'] = charged_words
    return app


def main():
    logging.basicConfig(level=logging.DEBUG)
    web.run_app(make_app(), port=int(os.getenv('PORT', 8080)))


if __name__ == '__main__':
    main()
