from .swagger import Path
import related


@related.mutable
class PathReport(object):
    path_url = related.StringField()
    path_obj = related.ChildField(Path)


@related.mutable
class CoverageReport(object):
    paths = related.MappingField(PathReport, "path_url")

    """
        iterate through schema and map based on paths
        iterate through result and determine calls to identify
                => result => suite => case => scenario => step => fetch
    """

    @classmethod
    def create(cls, suite, suite_result):
        pass

    def add_schema(self, schema):
        for path_url, path_obj in schema.paths.items():
            report = PathReport(path_url=path_url, path_obj=path_obj)
            self.paths[path_url] = report
