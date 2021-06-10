import os
import time
import urllib.parse
from contextlib import contextmanager
from enum import Enum
import logging
from typing import Callable
from typing import Generator

import aiohttp
import asyncio

import anyio
import async_timeout
import pymorphy2
from aiohttp import ClientError
from aioresponses import aioresponses

from adapters import ArticleNotFound
from adapters import SANITIZERS
from text_tools import calculate_jaundice_rate
from text_tools import split_by_words

TEST_ARTICLES = [
    'https://inosmi.ru/politic/20210608/249884545q.html',
    'https://inosmi.ru/economic/20190629/245384784.html',
    'https://inosmi.ru/politic/20210607/249874429.html',
    'https://lenta.ru/news/2021/06/08/zelensky_football/',
]

TEST_BOOK = ('https://dvmn.org/media/filer_public/51/83/51830f54-7ec7-4702-847b-c5790ed3724c'
             '/gogol_nikolay_taras_bulba_-_bookscafenet.txt')

ANALIZE_TIMEOUT = 10


logger = logging.getLogger('main')


class ProcessingStatus(Enum):
    OK = 'OK'
    FETCH_ERROR = 'FETCH_ERROR'
    PARSING_ERROR = 'PARSING_ERROR'
    TIMEOUT = 'TIMEOUT'


async def fetch(session, url):
    async with session.get(url) as response:
        response.raise_for_status()
        return await response.text()


def get_sanitizer(url):
    host = urllib.parse.urlparse(url).hostname.replace('.', '_')
    default = SANITIZERS['inosmi_ru']
    SANITIZERS['dvmn_org'] = lambda x: x
    return SANITIZERS.get(host, default)


@contextmanager
def timeit_context(log_msg: str = 'Анализ закончен за') -> Generator[Callable[[], float], None, None]:
    state = dict(_time=time.monotonic())
    try:
        yield lambda: state['_time']
    finally:
        state['_time'] = time.monotonic() - state['_time']
        logger.info('%s %.2f сек', log_msg, state['_time'])


async def process_article(session, morph, charged_words, url, title, results, analize_timeout: float=ANALIZE_TIMEOUT):
    status = ProcessingStatus.OK
    words_count = None
    score = None
    try:
        async with async_timeout.timeout(analize_timeout):
            with timeit_context('Анализ закончен за'):
                html = await fetch(session, url)
                sanitize = get_sanitizer(url)
                sanitized_article = sanitize(html)
                words = await split_by_words(morph, sanitized_article)
                score = calculate_jaundice_rate(words, charged_words)
                logger.debug('score: %r', score)
                logger.debug('charged_words: %r', len(charged_words))
            words_count = len(words)
            return

    except asyncio.TimeoutError:
        status = ProcessingStatus.TIMEOUT
        return
    except ClientError:
        status = ProcessingStatus.FETCH_ERROR
        return
    except ArticleNotFound:
        status = ProcessingStatus.PARSING_ERROR
        return
    finally:
        result = dict(status=status, score=score, words_count=words_count)
        if title:
            result['title'] = title
        results.append(result)


def test_process_article():
    morph = pymorphy2.MorphAnalyzer()
    charged_words = set()
    for dict_file in os.listdir('charged_dict'):
        with open(os.path.join('charged_dict', dict_file)) as f:
            charged_words.update(set(asyncio.run(split_by_words(morph, f.read()))))
    results = []
    url = 'https://inosmi.ru/politic/20210608/249884545q.html'

    with aioresponses() as mocked:
        async def _async_test_fetch_error():
            mocked.get(url, status=404, body='Not found')
            async with aiohttp.ClientSession() as session:
                await process_article(session, morph, charged_words, url, 'title', results)

        asyncio.run(_async_test_fetch_error())
        assert results[-1]['status'] == ProcessingStatus.FETCH_ERROR

        async def _async_test_parse_error():
            mocked.get(url, status=200, body='some text')
            async with aiohttp.ClientSession() as session:
                await process_article(session, morph, charged_words, url, 'title', results)

        asyncio.run(_async_test_parse_error())
        assert results[-1]['status'] == ProcessingStatus.PARSING_ERROR

        async def _async_test_timeout():
            async def callback(url, **kwargs):
                await asyncio.sleep(1)
            mocked.get(url, status=200, callback=callback)
            async with aiohttp.ClientSession() as session:
                await process_article(session, morph, charged_words, url, 'title', results, analize_timeout=0.5)

        asyncio.run(_async_test_timeout())
        assert results[-1]['status'] == ProcessingStatus.TIMEOUT


async def main():

    morph = pymorphy2.MorphAnalyzer()
    charged_words = set()
    for dict_file in os.listdir('charged_dict'):
        with open(os.path.join('charged_dict', dict_file)) as f:
            charged_words.update(set(await split_by_words(morph, f.read())))

    results = []
    async with aiohttp.ClientSession() as session:
        async with anyio.create_task_group() as tg:
            for url in TEST_ARTICLES:
                title = url
                tg.start_soon(process_article, session, morph, charged_words, url, title, results)

            tg.start_soon(process_article, session, morph, charged_words, TEST_BOOK, 'Книга', results)

    for result in results:
        print('Заголовок:', result.get('title'))
        print('Статус:', result.get('status'))
        print('Рейтинг:', result.get('score'))
        print('Слов в статье:', result.get('words_count'))


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    asyncio.run(main())
