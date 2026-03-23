import enum
import hyperlink
import yaml
import attrs
from attrs import field
from typing import Any, List, Optional
from cattrs.gen import make_dict_structure_fn, override

from .converter import converter, mapping_field


@enum.unique
class Scheme(enum.Enum):
    HTTP = "http"
    HTTPS = "https"
    WS = "ws"
    WSS = "wss"


@enum.unique
class DataType(enum.Enum):
    STRING = "string"
    NUMBER = "number"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"


class MIMEType(str):
    pass


converter.register_structure_hook(MIMEType, lambda v, _: MIMEType(v))


@attrs.define
class Contact:
    """Contact information for the owners of the API."""

    name: Optional[str] = None
    url: Optional[str] = None
    email: Optional[str] = None


@attrs.define
class License:
    name: str
    url: Optional[str] = None


@attrs.define
class Info:
    """General information about the API."""

    version: str
    title: str
    description: Optional[str] = None
    termsOfService: Optional[str] = None
    contact: Optional[Contact] = None
    license: Optional[License] = None


@attrs.define
class Definition:
    key: str
    type: Optional[DataType] = None
    required: Optional[List[str]] = None
    allOf: Optional[List[Any]] = None
    anyOf: Optional[List[Any]] = None
    is_not: Optional[List[Any]] = None
    properties: Optional[Any] = None


converter.register_structure_hook(
    Definition,
    make_dict_structure_fn(
        Definition, converter, is_not=override(rename="not")
    ),
)


@attrs.define
class Response:
    code: str
    description: Optional[str] = None
    schema: Optional[dict] = None


@attrs.define
class Parameter:
    name: str
    is_in: str
    schema: Optional[dict] = None


converter.register_structure_hook(
    Parameter,
    make_dict_structure_fn(
        Parameter, converter, is_in=override(rename="in")
    ),
)


@attrs.define
class Operation:
    responses: dict = mapping_field(Response, "code")
    tags: Optional[List[str]] = None
    summary: Optional[str] = None
    description: Optional[str] = None
    operationId: Optional[str] = None
    parameters: Optional[List[Parameter]] = None
    consumes: Optional[List[MIMEType]] = None
    produces: Optional[List[MIMEType]] = None
    externalDocs: Optional[dict] = None
    schemes: Optional[List[Scheme]] = None
    deprecated: Optional[bool] = None
    security: Optional[List[dict]] = None


@attrs.define
class Path:
    path: str
    delete: Optional[Operation] = None
    get: Optional[Operation] = None
    head: Optional[Operation] = None
    options: Optional[Operation] = None
    patch: Optional[Operation] = None
    post: Optional[Operation] = None
    put: Optional[Operation] = None

    @property
    def methods(self):
        return [method for method in METHODS if getattr(self, method)]


@attrs.define
class Swagger:
    swagger: str
    info: Info
    paths: dict = mapping_field(Path, "path")

    host: Optional[str] = None
    basePath: Optional[str] = None
    schemes: Optional[List[Scheme]] = None
    consumes: Optional[List[MIMEType]] = None
    produces: Optional[List[MIMEType]] = None
    definitions: dict = mapping_field(
        Definition, "key", default=attrs.Factory(dict)
    )

    _lookup: dict = field(init=False, factory=dict)

    def __attrs_post_init__(self):
        """populate the nested _lookup dictionary."""
        self.populate_lookup()

    @classmethod
    def loads(cls, content):
        as_dict = yaml.safe_load(content)
        return converter.structure(as_dict, cls)

    def resolve(self, url):
        """Resolve to Path object based on the URL path provided."""
        return self.descend_lookup(url, try_var=True).get(OBJ)

    def populate_lookup(self):
        """Populate the lookup nested dictionary with paths."""
        # todo: use basePath to ensure mapping is correct?
        self._lookup = {}
        for path_url, path_obj in self.paths.items():
            nested = self.descend_lookup(path_url)
            nested[OBJ] = path_obj

    def descend_lookup(self, url, try_var=False):
        """Descend lookup nested dictionary, finding bottom dict and tuple."""
        as_tuple = self.path_as_tuple(url)
        sub_lookup = self._lookup
        for item in as_tuple:
            # if in resolve mode, and VAR is only option, return var
            if try_var and (item not in sub_lookup) and (VAR in sub_lookup):
                sub_lookup = sub_lookup.get(VAR)

            # if build mode or item exists, return that.
            else:
                sub_lookup = sub_lookup.setdefault(item, {})

        return sub_lookup

    @classmethod
    def path_as_tuple(cls, url):
        """Convert URL path into a set of tuples replacing variables."""

        # remove leading and trailing blanks
        items = hyperlink.URL.from_text(url).path
        items = items[1:] if items and not items[0] else items
        items = items[:-1] if items and not items[-1] else items

        # replace variables with VAR indicator for resolve
        return tuple([VAR if cls.is_var(item) else item for item in items])

    @staticmethod
    def is_var(s):
        """Determines if follows path variable format of {pk}."""
        return isinstance(s, str) and s.startswith("{") and s.endswith("}")

    @classmethod
    def gather_schemas(cls, suite):
        from . import utils

        schemas = []
        for name, path in suite.schemas.items():
            data = utils.download_json_with_headers(suite, path)
            schema = converter.structure(data, cls)
            schemas.append(schema)
        return schemas


# constants

VAR = "$var"  # indicates a variable in a path (e.g. id in /pets/{id})
OBJ = "$obj"  # indicates a path sitting at this branch (e.g. /pets)
METHODS = ["get", "post", "put", "patch", "delete", "head", "options"]
