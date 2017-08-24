import related
import jmespath
import ast
import re
import addict

from . import get_logger


class Namespace(related.ImmutableDict):

    def __getattr__(self, item):
        return self.__getitem__(item)

    def __getitem__(self, name):
        if name in self:
            return self.get(name)
        else:
            try:
                return jmespath.search(name, self)
            except jmespath.exceptions.ParseError:
                pass

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
            try:
                rendered = value.format(**addict.Dict(namespace))
            except Exception as error:
                get_logger().error("render failed", value=value,
                                   namespace=namespace, error=error)
                rendered = str(error)
                # raise

            try:
                # eval if rendered value is list, dict, int or float
                is_list_or_dict = rendered.strip()[0] in ("{", "[")
                is_number = re.match("^[\d\.]+$", rendered.strip())
                assert is_list_or_dict or is_number

                value = ast.literal_eval(rendered)

            except:
                value = rendered

        elif isinstance(value, dict):
            items = value.items()
            value = {}
            for sub_key, sub_value in items:
                value[sub_key] = cls.render(sub_value, namespace)

        value = cls.wrap(value)

        return value
