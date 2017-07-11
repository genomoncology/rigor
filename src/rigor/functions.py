import os
import glob
import yaml


class Functions(object):

    def __init__(self, runner):
        self.runner = runner

    def get_pattern(self, relative_pattern):
        return os.path.join(self.runner.case.dir_path, relative_pattern)

    def load_yaml(self, filename):
        return next(self.iter_yaml(filename))

    def iter_yaml(self, *filenames):
        for filename in filenames:
            file_pattern = self.get_pattern(filename)
            for path in glob.glob(file_pattern, recursive=True):
                content = self.read_render(path)
                for doc in yaml.load_all(content):
                    yield doc

    def list_yaml(self, *filenames):
        return list(self.iter_yaml(*filenames))

    def function_map(self):
        return dict(list_yaml=self.list_yaml, load_yaml=self.load_yaml)

    def read_render(self, filepath):
        from . import Namespace
        content = open(filepath).read()
        return Namespace.render(content, self.runner.namespace)
