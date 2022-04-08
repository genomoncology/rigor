import os

from a2wsgi import ASGIMiddleware
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route

from rigor import Suite, Config, execute


async def home(request):
    return JSONResponse({"a": 123})


asgi = Starlette(debug=True, routes=[Route("/home", home)])
wsgi = ASGIMiddleware(asgi)

ROOT_DIR = os.path.join(os.path.dirname(__file__), "wsgi")
paths = [ROOT_DIR]


def test_wsgi():
    config = Config.load(paths)
    suite = Suite.create(paths, config, app=wsgi, concurrency=0, retries=0)
    result = execute(suite)
    assert result.success


def test_asgi():
    config = Config.load(paths)
    suite = Suite.create(paths, config, app=asgi, concurrency=1, retries=0)
    result = execute(suite)
    assert result.success
