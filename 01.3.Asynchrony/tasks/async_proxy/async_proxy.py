from yarl import URL
from aiohttp import web
import aiohttp
from multidict import MultiMapping
from typing import cast


async def proxy_handler(request: web.Request) -> web.Response:
    """
    Check request contains http url in query args:
        /fetch?url=http%3A%2F%2Fexample.com%2F
    and trying to fetch it and return body with http status.
    If url passed without scheme or is invalid raise 400 Bad request.
    On failure raise 502 Bad gateway.
    :param request: aiohttp.web.Request to handle
    :return: aiohttp.web.Response
    """
    query = cast(MultiMapping[str], request.query)
    url = query.get('url')

    if not url:
        raise web.HTTPBadRequest(text='No url to fetch')

    if not (url.startswith('http://') or url.startswith('https://')):
        url1 = URL(url)
        if url1.scheme == '':
            raise web.HTTPBadRequest(text='Empty url scheme')
        raise web.HTTPBadRequest(text='Bad url scheme: ftp')

    session = request.app['session']
    try:
        async with session.get(url) as response:
            body = await response.read()
            return web.Response(status=response.status, body=body)
    except aiohttp.ClientError:
        raise web.HTTPBadGateway()


async def setup_application(app: web.Application) -> None:
    """
    Setup application routes and aiohttp session for fetching
    :param app: app to apply settings with
    """
    session = aiohttp.ClientSession()
    app.router.add_get('/fetch' , proxy_handler)
    app["session"] = session


async def teardown_application(app: web.Application) -> None:
    """
    Application with aiohttp session for tearing down
    :param app: app for tearing down
    """
    session = app["session"]
    await session.close()
