from rigor.namespace import Namespace
import asyncio
import aiohttp
from bs4 import BeautifulSoup

URL = "https://en.wikipedia.org/wiki/Dorothy_Vaughan"
TITLE = "Dorothy Vaughan - Wikipedia"


def test_aiohttp_call():

    async def go():
        async with aiohttp.ClientSession() as session:
            async with session.get(URL) as context:
                headers = context.headers
                content_type = headers.get(aiohttp.hdrs.CONTENT_TYPE).lower()
                assert "text/html" in content_type
                text = await context.text()
                return text

    loop = asyncio.new_event_loop()
    text = loop.run_until_complete(go())
    assert isinstance(text, str)

    soup = BeautifulSoup(text, 'html.parser')
    assert soup.title.string == TITLE

    fmt = "{soup.title.string}"
    rendered = Namespace().render_string(fmt, Namespace(dict(soup=soup)))
    assert rendered == TITLE
