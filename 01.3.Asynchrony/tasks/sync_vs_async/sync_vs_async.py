import threading
import aiohttp
import asyncio
import requests


async def async_fetch(session: aiohttp.ClientSession, url: str) -> str:
    """
    Asyncronously fetch (get-request) single url using provided session
    :param session: aiohttp session object
    :param url: target http url
    :return: fetched text
    """
    async with session.get(url) as response:
        return await response.text()


async def async_requests(urls: list[str]) -> list[str]:
    """
    Concurrently fetch provided urls using aiohttp
    :param urls: list of http urls ot fetch
    :return: list of fetched texts
    """
    async with aiohttp.ClientSession() as session:
        tasks = [asyncio.create_task(async_fetch(session, url)) for url in urls]
        results = await asyncio.gather(*tasks)
        return list(results)


def sync_fetch(session: requests.Session, url: str) -> str:
    """
    Syncronously fetch (get-request) single url using provided session
    :param session: requests session object
    :param url: target http url
    :return: fetched text
    """
    return session.get(url).text


def threaded_requests(urls: list[str]) -> list[str]:
    """
    Concurrently fetch provided urls with requests in different threads
    :param urls: list of http urls ot fetch
    :return: list of fetched texts
    """
    session = requests.Session()
    results = []
    threads = []

    def worker(url):
        results.append(sync_fetch(session, url))

    for url in urls:
        thread = threading.Thread(target=worker, args=(url,))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    return results

