import os

from a2wsgi import ASGIMiddleware
from httpx import AsyncClient, Client
from httpx._transports.asgi import ASGITransport
from httpx._transports.wsgi import WSGITransport
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
    suite = Suite.create(
        paths, config, transport=WSGITransport(wsgi), concurrency=0, retries=0
    )
    result = execute(suite)
    assert result.success


def test_asgi():
    config = Config.load(paths)
    suite = Suite.create(
        paths, config, transport=ASGITransport(asgi), concurrency=1, retries=0
    )
    result = execute(suite)
    assert result.success


def test_transport_no_transport():
    """Session.create() omits transport kwarg when suite.transport is None."""
    from rigor.session import Session

    config = Config.load(paths)

    sync_suite = Suite.create(paths, config, concurrency=0, retries=0)
    assert isinstance(Session.create(sync_suite).http, Client)

    async_suite = Suite.create(paths, config, concurrency=1, retries=0)
    assert isinstance(Session.create(async_suite).http, AsyncClient)


def test_transport_with_transport():
    """Session.create() passes suite.transport directly to httpx."""
    from rigor.session import Session

    config = Config.load(paths)

    wsgi_suite = Suite.create(
        paths, config, transport=WSGITransport(wsgi), concurrency=0
    )
    wsgi_session = Session.create(wsgi_suite)
    assert isinstance(wsgi_session.http._transport, WSGITransport)

    asgi_suite = Suite.create(
        paths, config, transport=ASGITransport(asgi), concurrency=1
    )
    asgi_session = Session.create(asgi_suite)
    assert isinstance(asgi_session.http._transport, ASGITransport)


def test_semaphore_reuse():
    """Regression: semaphores must be rebound to the new event loop on each
    execute() call. Before the fix, the second call raised:
    RuntimeError: <Semaphore> is bound to a different event loop"""
    semaphore_path = [os.path.join(ROOT_DIR, "semaphore.rigor")]
    config = Config.load(semaphore_path)
    suite = Suite.create(
        semaphore_path, config, transport=ASGITransport(asgi), concurrency=1
    )

    assert "test_sem" in suite.semaphores

    result1 = execute(suite)
    assert result1.success

    result2 = execute(suite)
    assert result2.success
