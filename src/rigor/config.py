import related
import os
import collections
import copy

from . import Namespace, const, get_logger


@related.immutable
class Profile(object):
    name = related.StringField(default="__root__")
    domain = related.StringField(required=False)
    schemas = related.ChildField(Namespace, required=False)
    globals = related.ChildField(Namespace, required=False)
    headers = related.ChildField(Namespace, required=False)


@related.immutable
class Config(Profile):
    profiles = related.MappingField(Profile, "name", default={})
    file_path = related.StringField(required=False, default=None)

    def get_profile(self, name):
        # todo: determine if name is valid, rather than just returning default.
        # todo: handle case insensitivity?
        return self.profiles.get(name, self)  # return default (self) if fail

    @classmethod
    def load(cls, paths):
        """ Find rigor.yml file and load it into a Config object. """
        file_path = cls.find_file_path(paths)

        if file_path and os.path.exists(file_path):
            content = open(file_path).read()
            config = cls.loads(content, file_path)
            get_logger().info("config file found", file_path=file_path)
        else:
            config = cls()
            get_logger().info("config file not found", paths=paths)

        return config

    @classmethod
    def find_file_path(cls, paths):
        """ Return valid 'rigor.yml' file in the paths or parents of paths. """

        for path in paths:
            path = os.path.abspath(path)
            file_path = os.path.join(path, const.RIGOR_YML)
            reached_top = path == "/"

            # iterate until finding a pyconduct.yml file or reaching top
            while not os.path.exists(file_path) and not reached_top:
                file_path = os.path.join(path, const.RIGOR_YML)
                path = os.path.dirname(path)
                reached_top = path == "/"

            if os.path.exists(file_path):
                return file_path

    @classmethod
    def loads(cls, content, file_path=None):
        """ Load JSON string into a Config object. """
        vals = related.from_yaml(content, file_path=file_path,
                                 object_pairs_hook=dict)

        # environment namespace (RIGOR_)
        env_ns = Namespace(env={k[6:]: v for k, v in os.environ.items()
                                if k.startswith("RIGOR_")})

        # pop profiles and file_path from root config
        profiles = vals.pop("profiles", {})
        file_path = vals.pop("file_path")

        # iterate and construct profile sub-dictionaries with root info
        for name, profile in profiles.items():
            from_root_profile = copy.deepcopy(vals)
            profile = nested_update(from_root_profile, profile)
            eval_update_ns(profile, env_ns)
            profiles[name] = profile

        # construct root config profile
        vals['name'] = '__root__'
        vals['file_path'] = file_path
        vals['profiles'] = profiles
        eval_update_ns(vals, env_ns)
        return related.to_model(cls, vals)


def eval_update_ns(profile, env_ns, field="globals"):
    profile[field] = Namespace(profile.get(field, {})).evaluate(env_ns)


# https://stackoverflow.com/a/3233356
def nested_update(d, u):
    for k, v in u.items():
        if isinstance(v, collections.Mapping):
            r = nested_update(d.get(k, {}), v)
            d[k] = r
        else:
            d[k] = u[k]
    return d
