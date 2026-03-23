import io
import uuid
from typing import Any
from uuid import UUID

import attrs
import cattrs
from collections import OrderedDict

from rigor import Namespace

converter = cattrs.Converter()


def mapping_field(cls, child_key, default=None):
    """
    Replicates related.MappingField using attrs/cattrs.
    :param cls: The attrs class for child items.
    :param child_key: Attribute name on the child used as the map key.
    :param default: Default factory (default: empty dict).
    """
    if default is None:
        default = attrs.Factory(dict)

    def _convert(values):
        if values is None:
            return {}
        if (isinstance(values, dict) and
                all(isinstance(v, cls) for v in values.values())):
            return values  # already structured
        if not isinstance(values, dict):
            raise TypeError(f"Expected dict, got {type(values)}")
        result = OrderedDict()
        for k, v in values.items():
            if isinstance(v, dict):
                # inject the key as a field
                v = {**v, child_key: k}
            result[k] = converter.structure(v, cls) \
                if isinstance(v, dict) else v
        return result

    return attrs.field(default=default, converter=_convert)


def structure_uuid_hook(value: str | bytes, _: type[UUID]) -> UUID:
    if isinstance(value, (str, bytes)):
        return uuid.UUID(value)
    # Handle other cases or raise an error if needed
    raise ValueError(f"Cannot structure {type(value)} to UUID")


def unstructure_uuid_hook(value: UUID) -> str:
    return str(value)


def structure_namespace(value, _):
    if isinstance(value, dict):
        return Namespace(value)
    raise TypeError(f"Cannot structure {type(value).__name__} as Namespace")


converter.register_structure_hook(Namespace, structure_namespace)
converter.register_structure_hook(uuid.UUID, structure_uuid_hook)
converter.register_unstructure_hook(uuid.UUID, unstructure_uuid_hook)
converter.register_unstructure_hook(
    io.BufferedReader, lambda obj: f"<file: {obj.name}>")
converter.register_structure_hook(Any, lambda value, _: value)
