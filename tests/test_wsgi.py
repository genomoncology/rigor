import os
from flask import Flask
from a2wsgi import WSGIMiddleware
from rigor import Suite, Config, execute

wsgi = Flask(__name__)


@wsgi.route("/")
def home():
    return {"a": 123}


# noinspection PyTypeChecker
asgi = WSGIMiddleware(wsgi)

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
