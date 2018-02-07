from . import Swagger, Path, SuiteResult
import related
import os
import xlwt
import tempfile
import datetime


@related.mutable
class Counts(object):
    key = related.StringField()
    passed = related.IntegerField(default=0)
    failed = related.IntegerField(default=0)
    total = related.IntegerField(default=0)

    def add(self, passed):
        if passed:
            self.passed += 1
        else:
            self.failed += 1

        self.total += 1


@related.mutable
class MethodReport(object):
    url = related.StringField()
    method = related.StringField()
    counts = related.MappingField(Counts, "key", default={})

    def add(self, case_pass, scenario_pass, step_pass, params):
        self.case_counts.add(case_pass)
        self.scenario_counts.add(scenario_pass)
        self.step_counts.add(step_pass)

        all_pass = case_pass and scenario_pass and step_pass
        for param in params:
            self.param_counts(param).add(all_pass)

    @property
    def case_counts(self):
        return self.param_counts(CASE)

    @property
    def scenario_counts(self):
        return self.param_counts(SCENARIO)

    @property
    def step_counts(self):
        return self.param_counts(STEP)

    def param_counts(self, param):
        return self.counts.setdefault(param, Counts(param))

    @property
    def cases_passed(self):
        return self.case_counts.passed

    @property
    def cases_failed(self):
        return self.case_counts.failed

    @property
    def scenarios_passed(self):
        return self.scenario_counts.passed

    @property
    def scenarios_failed(self):
        return self.scenario_counts.failed

    @property
    def steps_passed(self):
        return self.step_counts.passed

    @property
    def steps_failed(self):
        return self.step_counts.failed


@related.mutable
class PathReport(object):
    url = related.StringField()
    obj = related.ChildField(Path)
    methods = related.MappingField(MethodReport, "method", default={})

    def get_method_report(self, method):
        return self.methods.setdefault(method, MethodReport(self.url, method))


@related.mutable
class CoverageReport(object):
    suite_result = related.ChildField(SuiteResult)
    schemas = related.SequenceField(Swagger)
    paths = related.MappingField(PathReport, "url")

    def prepare(self):
        """ iterate through all scenario-steps and record the counts. """
        for scenario_result, scenario_pass, case_pass in self.iterate():
            for step_result in scenario_result.step_results:
                step_pass = step_result.success
                url, method = step_result.fetch.url, step_result.fetch.method
                params = step_result.fetch.kwargs.get("params")
                method_report = self.get_method_report(url, method)
                if method_report:
                    method_report.add(case_pass, scenario_pass, step_pass,
                                      params)

    def get_method_report(self, url, method):
        """ return method report for a given url & method combination """
        path_obj = None

        # scan schemas
        for schema in self.schemas:
            path_obj = schema.resolve(url)
            if path_obj is not None:
                break

        # hard fail
        # assert path_obj, "No path report for: %s" % url

        # resolve path report and then method report
        if path_obj:
            path_report = self.paths.get(path_obj.path)
            return path_report.get_method_report(method)

    def iterate(self):  # pragma: no mccabe
        """ yields scenario_result, scenario_pass, case_pass """
        for case_result in self.suite_result.passed:
            for scenario_result in case_result.passed:
                yield scenario_result, True, True
            for scenario_result in case_result.failed:
                yield scenario_result, False, True  # pragma: no cover

        for case_result in self.suite_result.failed:
            for scenario_result in case_result.passed:
                yield scenario_result, True, False  # pragma: no cover
            for scenario_result in case_result.failed:
                yield scenario_result, False, False

    def generate(self, output_path):
        output_path = output_path or tempfile.mkdtemp()
        timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        output_path = os.path.join(output_path, "coverage-%s.xls" % timestamp)

        book = xlwt.Workbook()
        sheet = book.add_sheet("coverage")
        self.write_row(sheet.row(0), HEADERS, True)

        index = 1
        for url, path_report in self.paths.items():
            for method, method_report in path_report.methods.items():
                values = [getattr(method_report, column) for column in COLUMNS]
                self.write_row(sheet.row(index), values)
                index += 1

        for index, width in enumerate(WIDTHS):
            sheet.col(index).width = width

        book.save(output_path)
        return output_path

    def write_row(self, row, values, bolded=False):
        style = xlwt.XFStyle()
        if bolded:
            style.font = xlwt.Font()
            style.font.bold = True

        for index, value in enumerate(values):
            row.write(index, value, style=style)

    @classmethod
    def create(cls, suite_result):
        schemas = Swagger.gather_schemas(suite=suite_result.suite)

        # populate report with 0 counts for all discovered path/methods
        paths = {}
        for schema in schemas:
            for url, obj in schema.paths.items():
                report = PathReport(obj=obj, url=url)
                paths[url] = report
                for method in obj.methods:
                    report.get_method_report(method)

        # create and prepare report
        report = CoverageReport(suite_result=suite_result, schemas=schemas,
                                paths=paths)
        report.prepare()
        return report


# constants

CASE = "__key_case__"
SCENARIO = "__key_scenario__"
STEP = "__key_step__"
COLUMNS = ["url", "method", "cases_passed", "cases_failed", "scenarios_passed",
           "scenarios_failed", "steps_passed", "steps_failed"]
HEADERS = [column.replace("_", " ").title() for column in COLUMNS]
WIDTHS = [10000] + [4000] * (len(COLUMNS))
