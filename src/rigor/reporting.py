import json
import urllib
import related
from itertools import chain

from . import SuiteResult, Comparison


@related.immutable
class Tag(object):
    name = related.StringField()

    @classmethod
    def create(cls, tag):
            return cls(
                name=tag,
            )


@related.immutable
class Match(object):
    location = related.StringField()

    @classmethod
    def create(cls, step):

        return cls(
            location="features/step_definitions/steps.rb" + ";1"
        )


@related.immutable
class Validators(object):
    actual = related.ChildField(object)
    expect = related.ChildField(object)

    @classmethod
    def create_failing(cls, actual, expect):
        return cls(
            actual=actual,
            expect=expect
        )


@related.immutable
class DocString(object):
    value = related.StringField()
    content_type = related.StringField(required=False)
    line = related.IntegerField(default=6)

    @classmethod
    def section(cls, title, obj, **kwargs):
        size = max(20, len(title))
        bar = "=" * size
        content = related.to_yaml(obj, **kwargs) if obj else "None"
        return "\n".join([bar, str.center(title, size), bar, "", content, ""])

    @classmethod
    def create(cls, step_result):
        return cls(value="\n".join([
            cls.section("REQUEST", step_result.fetch),
            cls.section("RESPONSE", step_result.response),
            cls.section("EXTRACT", step_result.extract),
            cls.section("FAILURES", step_result.failed_validations,
                        suppress_empty_values=False)
        ]))


@related.immutable
class StatusResult(object):
    status = related.StringField()
    line = related.IntegerField()

    @classmethod
    def create(cls, res):
        values = {True: "passed", False: "failed"}
        status = values.get(res.success, "skipped")
        return cls(
            status=status,
            line=4
        )


@related.immutable
class Step(object):
    keyword = related.StringField()

    line = related.IntegerField()
    match = related.ChildField(Match)
    name = related.StringField()
    duration = related.FloatField()
    doc_string = related.ChildField(DocString, required=False, default=None)
    result = related.ChildField(StatusResult, required=False, default=None)

    @classmethod
    def create(cls, step_result, scenario_result):
        return cls(
            keyword="",
            line=3,
            name=step_result.step.description,
            doc_string=DocString.create(step_result),
            duration=scenario_result.running_time,
            match=Match.create(step_result.step),
            result=StatusResult.create(step_result),
        )


@related.immutable
class Element(object):
    keyword = related.StringField()
    id = related.StringField()
    name = related.StringField()
    line = related.IntegerField()
    description = related.StringField()
    type = related.StringField()
    steps = related.SequenceField(Step, default=[])

    @classmethod
    def create(cls, scenario_result):
        uuid = "%s;%s" % (urllib.parse.quote_plus(scenario_result.case.name),
                          scenario_result.uuid)

        steps = [Step.create(step_result, scenario_result) for step_result in scenario_result.step_results]

        return cls(
            keyword="Scenario",
            name=scenario_result.scenario.__name__,
            id=uuid,
            line=2,
            description="",
            type="scenario",
            steps=steps,
        )


@related.immutable
class Feature(object):
    uri = related.StringField()
    keyword = related.StringField()
    id = related.StringField()
    name = related.StringField()
    line = related.IntegerField()
    elements = related.SequenceField(Element, default=[])
    description = related.StringField(required=False, default=None)
    tags = related.SequenceField(Tag, required=False, default=None)

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
            elements=[Element.create(scenario_result) for scenario_result in
                      chain(case_result.passed, case_result.failed)],
            tags=[Tag.create(tag) for tag in case.tags]
        )


@related.immutable
class Cucumber(object):

    @classmethod
    def create(cls, suite_result):
        features = []
        for case_result in chain(suite_result.passed, suite_result.failed):
            features.append(Feature.create(case_result))
        return features


@related.immutable
class ReportEngine(object):
    report_types = related.SequenceField(str)
    output_path = related.SequenceField(str)
    suite_result = related.ChildField(SuiteResult)

    def generate(self):
        cucumber = Cucumber.create(self.suite_result)
        fp = open("cucumber.json", "w+")
        fp.write(related.to_json(cucumber))
        fp.close()
