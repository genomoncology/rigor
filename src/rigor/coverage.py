from . import Suite, SuiteResult
import related


@related.mutable
class PathReport(object):
    path = related.StringField()


@related.mutable
class CoverageReport(object):
    paths = related.MappingField(PathReport, "path")

    """
        iterate through schema and map based on paths
        iterate through result and determine calls to identify
                => result => suite => case => scenario => step => fetch
    """
