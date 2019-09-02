import typing
import asyncio
import logging
from aiohttp import ClientSession, ClientTimeout, web
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class Parser:
    BASE_URL = "https://news.ycombinator.com/"
    SESSION = ClientSession(timeout=ClientTimeout(connect=10, sock_read=60))
    USER_AGENT = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/74.0.3729.169 YaBrowser/19.6.0.1583 Yowser/2.5 Safari/537.36"
    )

    async def load(self):
        html = await self.load_resource()
        if html:
            data = await self.process_html(html)
            return data

    async def store(self, data, storage):
        if data:
            await storage.insert(data)

    async def load_resource(self) -> typing.Optional[str]:
        """
        Load original resource from proxied host.
        """
        try:
            res = await self.SESSION.get(
                f"{self.BASE_URL}",
                headers={
                    "User-Agent": self.USER_AGENT,
                    "Accept": "text/html",
                    "Accept-Language": "en,ru;q=0.9,cs;q=0.8,la;q=0.7",
                    "Accept-Encoding": "gzip, deflate",
                },
                verify_ssl=False,
            )
            res.raise_for_status()
        except Exception as e:
            logger.exception("Error while loading page (error=%s)", e)
            return None
        else:
            return await res.text(encoding="utf-8")

    async def process_html(self, html: str) -> str:
        try:
            return await asyncio.get_event_loop().run_in_executor(None, self._process_html, html)
        except Exception as e:
            logger.exception("Error while parsing page, returning original (error=%s)", e)
            return html

    def _process_html(self, html: str) -> list:
        soup = BeautifulSoup(markup=html, features="html5lib", from_encoding="utf-8")
        data = []
        for link in soup.select('#hnmain a.storylink'):
            try:
                item = {
                    "id": link.find_parent("tr")["id"],
                    "title": link.string,
                    "url": link["href"]
                }
            except Exception as e:
                logger.exception("Error while processing link (error=%s, link=%s)", e, link)
            else:
                data.append(item)

        return data
