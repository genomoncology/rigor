import related
import ast
import re
import addict
import string

from . import get_logger


class Namespace(related.ImmutableDict):

    def __getattr__(self, item):
        try:
            return self.__getitem__(item)
        except KeyError:
            return super(Namespace, self).__getattr__(item)

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
            value = cls.render_dict(value, namespace)

        elif isinstance(value, list):
            value = cls.render_list(value, namespace)

        value = cls.wrap(value)

        return value

    @classmethod
    def render_list(cls, value, namespace):
        new_value = []
        for sub_value in value:
            new_value.append(cls.render(sub_value, namespace))
        value = new_value
        return value

    @classmethod
    def render_dict(cls, value, namespace):
        new_value = {}
        for sub_key, sub_value in value.items():
            new_value[sub_key] = cls.render(sub_value, namespace)
        value = new_value
        return value

    @classmethod
    def render_string(cls, value, namespace):
        ns = addict.Dict(namespace)

        # 1st pass: substitute any $attr with the value from the namespace
        substituted = cls.do_substitute(namespace, ns, value)

        # 2nd pass: python string formatting with namespace
        formatted = cls.do_render(namespace, ns, substituted, value)

        # 3rd pass, if string repr of a list or dictionary, do literal eval
        evaluated = cls.do_evaluate(formatted)

        return evaluated

    @classmethod
    def do_substitute(cls, namespace, ns, value):
        try:
            substituted = string.Template(value).substitute(**ns)
            get_logger().debug("substitution success", value=value,
                               substituted=substituted, namespace=namespace)

        except Exception as error:
            substituted = value
            get_logger().debug("substitution failed", value=value,
                               namespace=namespace, error=error)

        return substituted

    @classmethod
    def do_render(cls, namespace, ns, substituted, value):
        try:
            formatted = substituted.format(**ns)
            get_logger().debug("render success", substituted=substituted,
                               formatted=formatted, namespace=namespace)

        except Exception as error:
            formatted = substituted
            get_logger().debug("render failed", value=value,
                               namespace=namespace, error=error)

        return formatted

    @classmethod
    def do_evaluate(cls, formatted):
        try:
            is_list_or_dict = formatted.strip()[0] in ("{", "[")
            is_number = re.match("^[\d\.]+$", formatted.strip())
            if is_list_or_dict or is_number:
                evaluated = ast.literal_eval(formatted)
            else:
                evaluated = formatted

        except Exception as error:
            evaluated = formatted
            get_logger().debug("literal eval failed", formatted=formatted,
                               error=error)
        return evaluated
