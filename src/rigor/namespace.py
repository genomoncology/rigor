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
            value = cls.render_string(value, namespace)

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

    @classmethod
    def render_string(cls, value, namespace):
        ns = addict.Dict(namespace)

        # 1st pass: substitute any $attr with the value from the namespace
        try:
            substituted = string.Template(value).substitute(**ns)
            get_logger().debug("substitution success", value=value,
                               substituted=substituted, namespace=namespace)

        except Exception as error:
            substituted = value
            get_logger().info("substitution failed", value=value,
                              namespace=namespace, error=error)

        # 2nd pass: python string formatting with namespace
        try:
            formatted = substituted.format(**ns)
            get_logger().debug("render success", substituted=substituted,
                               formatted=formatted, namespace=namespace)

        except Exception as error:
            formatted = substituted
            get_logger().info("render failed", value=value,
                              namespace=namespace, error=error)

        # 3rd pass, if string repr of a list or dictionary, do literal eval
        try:
            is_list_or_dict = formatted.strip()[0] in ("{", "[")
            is_number = re.match("^[\d\.]+$", formatted.strip())
            if is_list_or_dict or is_number:
                evaluated = ast.literal_eval(formatted)
            else:
                evaluated = formatted

        except Exception as error:
            evaluated = formatted
            get_logger().info("literal eval failed", formatted=formatted,
                              error=error)

        return evaluated
