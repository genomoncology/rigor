import os
import copy
from typing import Optional

import attrs
import yaml
from attrs import define, field

from . import Namespace, const, get_logger, utils
from .converter import mapping_field, converter


@define
class Profile:
    name: str = field(default="__root__")
    host: Optional[str] = field(default=None)
    schemas: Optional[Namespace] = field(default=None)
    globals: Optional[Namespace] = field(default=None)
    headers: Optional[Namespace] = field(default=None)
    prefixes: Optional[list] = field(factory=list)
    extensions: list = field(factory=lambda: ["rigor"])
    includes: Optional[list] = field(factory=list)
    excludes: Optional[list] = field(factory=list)
    concurrency: int = field(default=5)
    retries: int = field(default=0)
    sleep: int = field(default=60)
    retry_failed: bool = False

    def as_dict(self):
        kwargs = converter.unstructure(self)
        kwargs.pop("profiles", None)
        kwargs.pop("file_path", None)
        return kwargs


@define
class Config(Profile):
    profiles: dict = mapping_field(Profile, "name",
                                   default=attrs.Factory(dict))
    file_path: str | None = attrs.field(default=None)

    def get_profile(self, name):
        # todo: determine if name is valid, rather than just returning default.
        # todo: handle case insensitivity?
        return self.profiles.get(name, self)  # return default (self) if fail

    @classmethod
    def load(cls, paths):
        """Find rigor.yml file and load it into a Config object."""
        file_path = cls.find_file_path(paths)

        if file_path and os.path.exists(file_path):
            content = open(file_path).read()
            config = cls.loads(content, file_path)
            get_logger().info("config file", file_path=file_path)
            details = converter.unstructure(config)
            get_logger().debug("config details", **details)
        else:
            config = cls()
            get_logger().info("no config file not found", paths=paths)

        return config

    @classmethod
    def find_file_path(cls, paths):
        """Return valid 'rigor.yml' file in the paths or parents of paths."""

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

        """Load YAML string into a Config object."""
        vals = yaml.safe_load(content) or {}

        # environment namespace (RIGOR_)
        env_ns = Namespace(
            env={
                k[6:]: v
                for k, v in os.environ.items()
                if k.startswith("RIGOR_")
            }
        )

        # pop profiles and file_path from root config
        profiles = vals.pop("profiles", {})

        # iterate and construct profile sub-dictionaries with root info
        for name, profile in profiles.items():
            from_root_profile = copy.deepcopy(vals)
            profile = utils.nested_update(from_root_profile, profile)
            eval_update_ns(profile, env_ns)
            profiles[name] = profile

        # construct root config profile
        vals["name"] = "__root__"
        vals["file_path"] = file_path
        vals["profiles"] = profiles
        eval_update_ns(vals, env_ns)
        return converter.structure(vals, cls)


def eval_update_ns(profile, env_ns, field="globals"):
    profile[field] = Namespace(profile.get(field, {})).evaluate(env_ns)
