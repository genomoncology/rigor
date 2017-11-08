import related
import os
import copy

from . import Namespace, const, get_logger, utils


@related.immutable
class Profile(object):
    name = related.StringField(default="__root__")
    host = related.StringField(required=False)
    schemas = related.ChildField(Namespace, required=False)
    globals = related.ChildField(Namespace, required=False)
    headers = related.ChildField(Namespace, required=False)
    prefixes = related.SequenceField(str, default=None)
    extensions = related.SequenceField(str, default=["rigor"])
    includes = related.SequenceField(str, default=None)
    excludes = related.SequenceField(str, default=None)
    concurrency = related.IntegerField(default=5)

    def __attrs_post_init__(self):
        # circumvent frozen error due to immutable
        extensions = [ext[1:] if ext.startswith(".") else ext
                      for ext in self.extensions or []]
        object.__setattr__(self, "extensions", extensions)

    def as_dict(self):
        kwargs = related.to_dict(self)
        kwargs.pop("profiles", None)
        kwargs.pop("file_path", None)
        return kwargs


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
            get_logger().info("config file", file_path=file_path)
            get_logger().debug("config details", **related.to_dict(config))
        else:
            config = cls()
            get_logger().info("no config file not found", paths=paths)

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
            profile = utils.nested_update(from_root_profile, profile)
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
