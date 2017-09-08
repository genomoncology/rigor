import related
import ast
import re
import addict
import string

from . import get_logger


class Namespace(related.ImmutableDict):

    def __getattr__(self, item):
        return self.__getitem__(item)

    def evaluate(self, namespace, existing=None):
        values = existing or {}

        for key, value in self.items():
            values[key] = self.render(value, namespace)

        return Namespace(values)

    @classmethod
    def wrap(cls, value):
        if isinstance(value, dict) and not isinstance(value, cls):
            return cls(value)

        if isinstance(value, list):
            new_list = []
            for item in value:
                new_list.append(cls.wrap(item))
            value = new_list

        return value

    @classmethod
    def render(cls, value, namespace):
        if isinstance(value, str):
            ns = addict.Dict(namespace)

            try:
                value = string.Template(value).substitute(**ns)
            except ValueError:
                pass

            try:
                rendered = value.format(**ns)
            except Exception as error:
                get_logger().error("render failed", value=value,
                                   namespace=namespace, error=error)
                # rendered = str(error)
                raise

            try:
                # eval if rendered value is list, dict, int or float
                is_list_or_dict = rendered.strip()[0] in ("{", "[")
                is_number = re.match("^[\d\.]+$", rendered.strip())
                assert is_list_or_dict or is_number

                value = ast.literal_eval(rendered)

            except:
                value = rendered

        elif isinstance(value, dict):
            new_value = {}
            for sub_key, sub_value in value.items():
                new_value[sub_key] = cls.render(sub_value, namespace)
            value = new_value

        elif isinstance(value, list):
            new_value = []
            for sub_value in value:
                new_value.append(cls.render(sub_value, namespace))
            value = new_value

        value = cls.wrap(value)

        return value
