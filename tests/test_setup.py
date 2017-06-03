"""Comparison of fetching web pages sequentially vs. asynchronously
Requirements: Python 3.5+, Requests, aiohttp, cchardet
For a walkthrough see this blog post:
http://mahugh.com/2017/05/23/http-requests-asyncio-aiohttp-vs-requests/
"""
import asyncio
from timeit import default_timer
import json

from aiohttp import ClientSession


def demo_async(urls):
    """Fetch list of web pages asynchronously."""
    start_time = default_timer()

    loop = asyncio.get_event_loop()  # event loop
    future = asyncio.ensure_future(fetch_all(urls))  # tasks to do
    loop.run_until_complete(future)  # loop until done

    for result in future.result():
        print(json.dumps(json.loads(result), indent=4))

    tot_elapsed = default_timer() - start_time
    print(' WITH ASYNCIO: '.rjust(30, '-') + '{0:5.2f} {1}'. \
          format(tot_elapsed, asterisks(tot_elapsed)))


async def fetch_all(urls):
    """Launch requests for all web pages."""
    tasks = []
    fetch.start_time = dict()  # dictionary of start times for each url
    headers = {"Authorization": "Token e1ec1eb80340ffbef8c9b8baf5312f6250d283bc"}
    async with ClientSession(headers=headers) as session:
        for url in urls:
            task = asyncio.ensure_future(fetch(url, session))
            tasks.append(task)  # create list of tasks
        return await asyncio.gather(*tasks)  # gather task responses


async def fetch(url, session):
    """Fetch a url, using specified ClientSession."""
    fetch.start_time[url] = default_timer()
    async with session.get(url) as response:
        resp = await response.read()
        elapsed = default_timer() - fetch.start_time[url]
        print('{0:30}{1:5.2f} {2}'.format(url, elapsed, asterisks(elapsed)))
        return resp


def asterisks(num):
    """Returns a string of asterisks reflecting the magnitude of a number."""
    return int(num * 10) * '*'


if __name__ == '__main__':
    URL_LIST = [
        "http://localhost/api/annotations/hgvs?delete_if_exists=true&batch=NC_000007.13:g.140453136A>T",
        "http://localhost/api/annotations/hgvs?delete_if_exists=true&batch=NC_000005.9:g.114916256A>C",
        "http://localhost/api/annotations/hgvs?delete_if_exists=true&batch=NC_000005.9:g.1295073C>A",
    ]
    demo_async(URL_LIST)
