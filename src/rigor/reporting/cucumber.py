import json
import urllib
import related

from rigor import State


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
        if step.name is None:
            name = "Placeholder"
        else:
            name = step.name
        return cls(
            location="features/step_definitions/steps.rb"
        )


@related.immutable
class Validators(object):
    actual = related.ChildField(object)
    # comparison = related.StringField()
    expect = related.ChildField(object)

    #todo: Account for other comparators

    @classmethod
    def create_failing(cls, actual, expect):
        return cls(
            actual=actual,
            expect=expect
        )


@related.immutable
class DocString(object):
    value = related.StringField()
    content_type = related.StringField()
    line = related.IntegerField()

    #todo: Figure out alternative for results
    @classmethod
    def create(cls, step, obj):
        v = []
        j = 0
        spacer = "====================\n"
        for fail_validation in obj.fail_validations:
            i = 0
            for item in fail_validation.actual:
                if fail_validation.actual[i] != fail_validation.expect[i]:
                    v.append(Validators.create_failing(fail_validation.actual[i], fail_validation.expect[i]))
                i += 1
                j += 1
        result = related.to_json(json.loads(related.to_json(step.extract.result)))
        if j == 0:
            return cls(
                value=(spacer + "   RESULT   \n" + spacer + result),
                content_type="application/json",
                line=6
            )
        else:
            return cls(
                value=spacer + "   RESULT   \n" + spacer + result + "\n\n\n" + spacer + " FAILED VALIDATIONS\n" + spacer + related.to_json(json.loads(related.to_json(v))),
                content_type="application/json",
                line=6
            )


@related.immutable
class Result(object):
    status = related.StringField()
    line = related.IntegerField()
    duration = related.IntegerField()

    @classmethod
    def create(cls, step, obj):
        i = 0
        for fail_validation in obj.fail_validations:
            for item in fail_validation.actual:
                if fail_validation.actual[i] != fail_validation.expect[i]:
                    status = "failed"
                i += 1
        if i == 0:
            status = "passed"
        return cls(
            status=status,
            line=4,
            duration=1
        )



@related.immutable
class Step(object):
    keyword = related.StringField()

    line = related.IntegerField()
    match = related.ChildField(Match)
    name = related.StringField()
    doc_string = related.ChildField(DocString)
    result = related.ChildField(Result, required=False, default=None)

    @classmethod
    def create(cls, step, obj):

        return cls(
            keyword="",
            line=3,
            name=step.description,
            doc_string=DocString.create(step, obj),
            match=Match.create(step),
            result=Result.create(step, obj)
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
    tags = related.SequenceField(Tag, required=False, default=None)


    @classmethod
    def create(cls, case, obj):
        stp = []
        tg = []
        for step in case.steps:
            stp.append(Step.create(step, obj))
        for tag in case.tags:
            tg.append(Tag.create(tag))
        temp = State.uuid.default
        return cls(
            keyword="Scenario",
            # todo: Scenario name = uuid & replace placeholder with uuid
            name=temp,
            id=(urllib.parse.quote_plus(case.name) + ";" + str(State.uuid.default)),
            line=2,
            description="",
            type="scenario",
            steps=stp,
            tags=tg
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

    @classmethod
    def create(cls, case, obj):
        elm = []
        for scenario in case.scenarios:
            elm.append(Element.create(case, obj))

        return cls(
            uri=case.file_path,
            keyword="Feature",
            id=urllib.parse.quote_plus(case.name),
            name=case.name,
            line=1,
            elements=elm,
        )


@related.immutable
class Cucumber(object):
    features = related.SequenceField(Feature)

    def load_init(self, suite):
        ret = []
        for obj in suite.passed:
            ret.append(Feature.create(obj.case, obj))
        for entry in suite.failed:
            ret.append(Feature.create(entry.case, entry))
        return ret




