from aioresponses import aioresponses

from parser import Parser
from server import app


def test_parse():
    markup = '<html><body><div id="hnmain"><table><tbody><tr id="1"><td><a href="url" class="storylink">title</a></td></tr></tbody></table></div></body></html>'
    data = Parser()._process_html(markup)
    assert data == [
        {
            "id": "1",
            "title": "title",
            "url": "url"
        }
    ]


async def test_load(aiohttp_client, loop):
    client = await aiohttp_client(app)

    parser = Parser()
    with aioresponses(passthrough=[f"http://{client.host}:{client.port}"]) as m:
        m.get(
            "https://news.ycombinator.com/",
            status=200,
            content_type="text/html",
            body='<html><body><div id="hnmain"><table><tbody><tr id="1"><td><a href="url" class="storylink">title</a></td></tr></tbody></table></div></body></html>',
        )
        data = await parser.load()
    await parser.store(data, app.db)
    res = await client.get("/posts")

    assert res.status == 200
    data = await res.json()
    data[0].pop('created_at')
    assert data == [
        {
            "id": 1,
            "title": "title",
            "url": "url"
        }
    ]
