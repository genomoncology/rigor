import related
import enum
import hyperlink


@enum.unique
class Scheme(enum.Enum):
    HTTP = "http"
    HTTPS = "https"
    WS = "ws"
    WSS = "wss"


@enum.unique
class DataType(enum.Enum):
    STRING = 'string'
    NUMBER = 'number'
    INTEGER = 'integer'
    BOOLEAN = 'boolean'
    ARRAY = 'array'
    OBJECT = 'object'


class MIMEType(str):
    pass


@related.mutable
class Contact(object):
    """Contact information for the owners of the API."""
    name = related.StringField(required=False)
    url = related.StringField(required=False)
    email = related.StringField(required=False)


@related.mutable
class License(object):
    name = related.StringField(required=True)
    url = related.StringField(required=False)


@related.mutable
class Info(object):
    """General information about the API."""
    version = related.StringField(required=True)
    title = related.StringField(required=True)
    description = related.StringField(required=False)
    termsOfService = related.StringField(required=False)
    contact = related.ChildField(Contact, required=False)
    license = related.ChildField(License, required=False)


@related.mutable
class Definition(object):
    key = related.StringField(required=True)
    type = related.ChildField(DataType, required=False)
    required = related.SequenceField(str, required=False)
    allOf = related.SequenceField(object, required=False)
    anyOf = related.SequenceField(object, required=False)
    is_not = related.SequenceField(object, required=False, key="not")
    properties = related.ChildField(object, required=False)


@related.mutable
class Response(object):
    code = related.StringField(required=True)
    description = related.StringField(required=False)
    schema = related.ChildField(dict, required=False)


@related.mutable
class Parameter(object):
    name = related.StringField(required=True)
    is_in = related.StringField(required=True, key="in")
    schema = related.ChildField(dict, required=False)


@related.mutable
class Operation(object):
    responses = related.MappingField(Response, "code", required=True)
    tags = related.SequenceField(str, required=False)
    summary = related.StringField(required=False)
    description = related.StringField(required=False)
    operationId = related.StringField(required=False)
    parameters = related.SequenceField(Parameter, required=False)
    consumes = related.SequenceField(MIMEType, required=False)
    produces = related.SequenceField(MIMEType, required=False)
    externalDocs = related.ChildField(dict, required=False)
    schemes = related.SequenceField(Scheme, required=False)
    deprecated = related.BooleanField(required=False)
    security = related.ChildField(dict, required=False)


@related.mutable
class Path(object):
    path = related.StringField(required=True)
    delete = related.ChildField(Operation, required=False)
    get = related.ChildField(Operation, required=False)
    head = related.ChildField(Operation, required=False)
    options = related.ChildField(Operation, required=False)
    patch = related.ChildField(Operation, required=False)
    post = related.ChildField(Operation, required=False)
    put = related.ChildField(Operation, required=False)

    @property
    def methods(self):
        return [method for method in METHODS if getattr(self, method)]


@related.mutable
class Swagger(object):
    swagger = related.StringField(required=True)
    info = related.ChildField(Info, required=True)
    paths = related.MappingField(Path, "path", required=True)

    host = related.StringField(required=False)
    basePath = related.StringField(required=False)
    schemes = related.SequenceField(Scheme, required=False)
    consumes = related.SequenceField(MIMEType, required=False)
    produces = related.SequenceField(MIMEType, required=False)
    definitions = related.MappingField(Definition, "key", required=False)

    _lookup = related.ChildField(dict, required=False)

    def __attrs_post_init__(self):
        """ populate the nested _lookup dictionary."""
        self.populate_lookup()

    @classmethod
    def loads(cls, content):
        as_dict = related.from_yaml(content, object_pairs_hook=dict)
        return related.to_model(cls, as_dict)

    def resolve(self, url):
        """ Resolve to Path object based on the URL path provided. """
        return self.descend_lookup(url, try_var=True).get(OBJ)

    def populate_lookup(self):
        """ Populate the lookup nested dictionary with paths. """
        # todo: use basePath to ensure mapping is correct?
        self._lookup = {}
        for path_url, path_obj in self.paths.items():
            nested = self.descend_lookup(path_url)
            nested[OBJ] = path_obj

    def descend_lookup(self, url, try_var=False):
        """ Descend lookup nested dictionary, finding bottom dict and tuple."""
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
        """ Convert URL path into a set of tuples replacing variables. """

        # remove leading and trailing blanks
        items = hyperlink.URL.from_text(url).path
        items = items[1:] if items and not items[0] else items
        items = items[:-1] if items and not items[-1] else items

        # replace variables with VAR indicator for resolve
        return tuple([VAR if cls.is_var(item) else item for item in items])

    @staticmethod
    def is_var(s):
        """ Determines if follows path variable format of {pk}. """
        return isinstance(s, str) and s.startswith("{") and s.endswith("}")

    @classmethod
    def gather_schemas(cls, suite):
        from . import utils
        schemas = []
        for name, path in suite.schemas.items():
            json = utils.download_json_with_headers(suite, path)
            schema = related.to_model(cls, json)
            schemas.append(schema)
        return schemas


# constants

VAR = "$var"  # indicates a variable in a path (e.g. id in /pets/{id})
OBJ = "$obj"  # indicates a path sitting at this branch (e.g. /pets)
METHODS = ["get", "post", "put", "patch", "delete", "head", "options"]
