import asyncio
import os
import sys

from aiohttp import web
from parser import Parser
from storage import Storage

routes = web.RouteTableDef()

DEFAULT_PAGE_SIZE = 30
MAX_PAGE_SIZE = 100


@routes.get("/posts")
async def posts(request):
    try:
        limit = max(min(int(request.query.get("limit", DEFAULT_PAGE_SIZE)), MAX_PAGE_SIZE), 1)
    except ValueError:
        limit = DEFAULT_PAGE_SIZE

    try:
        offset = max(0, int(request.query.get("offset", 0)))
    except ValueError:
        offset = 0

    order = "id"
    if request.query.get("order", "").lstrip("-") in ["id", "title", "url"]:
        order = request.query.get("order")

    data = await request.app.db.load(offset, limit, order)
    data = [{**item, "created_at": item["created_at"].isoformat()} for item in data]
    return web.json_response(data)


app = web.Application()
app.add_routes(routes)


async def refresh_posts_task(app):
    parser = Parser()

    while True:
        data = await parser.load()
        if data:
            await parser.store(data, app.db)
        await asyncio.sleep(60 * 5)


async def on_startup(app):
    if not hasattr(sys, "_called_from_test"):
        db_name = "../db.sqlite"
    else:
        db_name = "../db_test.sqlite"
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), db_name))
    app.db = Storage(path)
    await app.db.setup()
    if not hasattr(sys, "_called_from_test"):
        asyncio.get_event_loop().create_task(refresh_posts_task(app))


app.on_startup.append(on_startup)


if __name__ == "__main__":
    web.run_app(app)
