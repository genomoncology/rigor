import json
import urllib
from typing import Any, List

import attrs
import os
import datetime
import tempfile
import yaml

from itertools import chain
from subprocess import DEVNULL, STDOUT, check_call

from . import SuiteResult, get_logger
from .converter import converter


@attrs.frozen
class Tag:
    name: str


@attrs.frozen
class Match:
    location: str = attrs.field(default="?")

    @classmethod
    def create(cls, step):
        return cls(location="features/step_definitions/steps.rb;1")


@attrs.frozen
class Validators:
    actual: Any = attrs.field()
    expect: Any = attrs.field()


@attrs.frozen
class DocString:
    value: str
    content_type: str = None
    line: int = 6

    @classmethod
    def section(cls, title, obj, **kwargs):
        size = max(20, len(title))
        bar = "=" * size
        if isinstance(obj, str):
            content = obj  # pragma: no cover
        elif obj:
            content = yaml.dump(converter.unstructure(obj))
        else:
            content = "None"

        return "\n".join([bar, str.center(title, size), bar, "", content, ""])

    @classmethod
    def create(cls, step_result):
        return cls(
            value="\n".join(
                [
                    cls.section("REQUEST", step_result.fetch),
                    cls.section(
                        "RESPONSE [%s]" % step_result.status,
                        step_result.response,
                    ),
                    cls.section("TRANSFORM", step_result.transform),
                    cls.section("EXTRACT", step_result.extract),
                    cls.section(
                        "FAILURES",
                        step_result.failed_validations,
                        suppress_empty_values=False,
                    ),
                ]
            )
        )


@attrs.frozen
class StatusResult:
    status: str
    duration: int
    line: int = 4

    @classmethod
    def create(cls, success, duration):
        status = {True: "passed", False: "failed"}.get(success, "skipped")
        return cls(status=status, duration=duration)


@attrs.frozen
class Step:
    keyword: str

    line: int
    name: str
    match: Match = None
    doc_string: DocString = None
    result: StatusResult = None

    @classmethod
    def create(cls, step_result, scenario_result):
        if step_result is None:
            output = converter.unstructure(scenario_result.scenario)
            output["__file__"] = scenario_result.case.file_path
            return cls(
                keyword="",
                line=3,
                name="Scenario Setup",
                doc_string=DocString(
                    value=DocString.section("SCENARIO", output)
                ),
                match=Match(),
                result=StatusResult.create(True, 0),
            )
        else:
            return cls(
                keyword="",
                line=3,
                name=step_result.step.description,
                doc_string=DocString.create(step_result),
                match=Match.create(step_result.step),
                result=StatusResult.create(
                    step_result.success, step_result.duration
                ),
            )


@attrs.frozen
class Element:
    keyword: str
    id: str
    name: str
    line: int
    description: str
    type: str
    steps: List[Step] = attrs.field(factory=list)

    @classmethod
    def create(cls, scenario_result):
        uuid = "%s;%s" % (
            urllib.parse.quote_plus(scenario_result.case.name),
            scenario_result.uuid,
        )

        # scenario step + steps
        steps = [Step.create(None, scenario_result)] + [
            Step.create(step_result, scenario_result)
            for step_result in scenario_result.step_results
        ]

        return cls(
            keyword="Scenario",
            name=scenario_result.scenario.__name__,
            id=uuid,
            line=2,
            description="",
            type="scenario",
            steps=steps,
        )


@attrs.frozen
class Feature:
    uri: str
    keyword: str
    id: str
    name: str
    line: int
    elements: List[Element] = attrs.field(factory=list)
    description: str = None
    tags: List = None

    @classmethod
    def create(cls, case_result):
        case = case_result.case
        uuid = "%s;%s" % (urllib.parse.quote_plus(case.name), case.uuid)
        return cls(
            uri=case.file_path,
            keyword="Feature",
            id=uuid,
            name=case.name,
            line=1,
            elements=[
                Element.create(scenario_result)
                for scenario_result in chain(
                    case_result.passed, case_result.failed
                )
            ],
            tags=[Tag(name=tag) for tag in case.tags],
        )


@attrs.frozen
class Cucumber:
    @classmethod
    def create(cls, suite_result):
        features = []
        for case_result in chain(suite_result.passed, suite_result.failed):
            features.append(Feature.create(case_result))
        return features


@attrs.frozen
class ReportEngine:
    suite_result: SuiteResult
    output_path: str = None
    with_html: bool = False

    CUCUMBER_JSON = "cucumber.json"
    JAR_NAME = "cucumber-sandwich.jar"
    CUKE_DIR = "cucumber-html-reports"
    CUKE_PATH = os.path.join(CUKE_DIR, CUKE_DIR, "overview-features.html")

    def generate_json(self, output_path):
        get_logger().debug("generate json", output_path=output_path)

        success = False

        try:
            cucumber = Cucumber.create(self.suite_result)
            path = os.path.join(output_path, self.CUCUMBER_JSON)

            file = open(path, "w+")
            data = converter.unstructure(cucumber)
            file.write(json.dumps(data, indent=4, sort_keys=True))
            file.close()
            get_logger().debug("created cucumber json", path=path)
            success = True

        except Exception as e:  # pragma: no cover
            get_logger().error("failed cucumber json", error=str(e))
            raise e

        return success

    def generate_html(self, output_path):
        get_logger().debug("generate html", output_path=output_path)

        dir_path = os.path.dirname(__file__)
        jar_path = os.path.join(dir_path, "assets", self.JAR_NAME)
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        html_dir_path = os.path.join(output_path, "html-%s" % timestamp)
        html_report_path = None

        args = [
            "java",
            "-jar",
            jar_path,  # java command w/ jar path
            "-o",
            html_dir_path,  # where to place html
            "-n",  # run once, not daemon
            "-f",
            output_path,
        ]  # where to find cucumber.json

        try:
            # call cucumber sandwich
            check_call(args, stdout=DEVNULL, stderr=STDOUT)

            # check report path
            html_report_path = os.path.join(html_dir_path, self.CUKE_PATH)
            assert os.path.exists(html_report_path)
            get_logger().debug(
                "generated html", html_report_path=html_report_path
            )

        except Exception as e:  # pragma: no cover
            get_logger().error("failed html report", error=str(e))

        return html_report_path

    def generate(self):
        output_path = self.output_path or tempfile.mkdtemp()

        json_created = self.generate_json(output_path)
        do_html = json_created and self.with_html
        html_report_path = self.generate_html(output_path) if do_html else None

        return html_report_path
