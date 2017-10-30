from rigor.swagger import Swagger, VAR
import pytest
import os.path


DATA_DIR = os.path.join(os.path.dirname(__file__), "swagger")


@pytest.fixture()
def swagger_json():
    json = open(os.path.join(DATA_DIR, "swagger_petstore_simple.json")).read()
    return Swagger.loads(json)


def test_swagger_paths(swagger_json):
    assert swagger_json.info.title == "Swagger Petstore"
    assert len(swagger_json.paths) == 2

    list_path = swagger_json.paths.get("/pets")
    assert list_path.get is not None
    assert list_path.post is not None
    assert list_path.delete is None
    assert list_path.patch is None

    detail_path = swagger_json.paths.get("/pets/{id}")
    assert detail_path.get is not None
    assert detail_path.delete is not None
    assert detail_path.post is None
    assert detail_path.patch is None


def test_swagger_resolve(swagger_json):
    list_path = swagger_json.paths.get("/pets")
    detail_path = swagger_json.paths.get("/pets/{id}")

    resolved = swagger_json.resolve("/pets")
    assert resolved == list_path

    resolved = swagger_json.resolve("/pets/1")
    assert resolved == detail_path


def test_is_var():
    assert Swagger.is_var("{pk}")
    assert not Swagger.is_var("{pk")
    assert not Swagger.is_var("pk}")
    assert not Swagger.is_var("pk")


def test_path_as_tuple():
    assert Swagger.path_as_tuple("/pets") == ("pets",)
    assert Swagger.path_as_tuple("/pets/{pk}") == ("pets", VAR)
    assert Swagger.path_as_tuple("/pets/{pk}/name") == ("pets", VAR, "name")
