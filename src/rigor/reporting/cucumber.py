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

        return cls(
            location="features/step_definitions/steps.rb" + ";1"
        )


@related.immutable
class Validators(object):
    actual = related.ChildField(object)
    # compare = related.StringField()
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

    @classmethod
    def create(cls, step, obj, status):
        v = []
        if status == "skipped":
            return cls(
                value="=== STEP NOT EXECUTED ===",
                content_type="application/json",
                line=6
            )
        spacer = "====================\n"
        for fail_validation in obj.fail_validations:
            i = 0
            #todo:  compare!?!?
            for item in fail_validation.actual:
                if fail_validation.actual[i] != fail_validation.expect[i]:
                    v.append(Validators.create_failing(fail_validation.actual[i], fail_validation.expect[i]))
                i += 1
        result = related.to_json(json.loads(related.to_json(step.extract.result)))
        if status == "passed":
            if result == "null":
                result = "HTTP Respose: Success"
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
    def create(cls, step, obj, prev, tags, suite):
        if step == obj.fail_step:
            status = "failed"
        elif prev is False or tags in suite.tags_excluded:
            status = "skipped"
        else:
            status = "passed"
        return cls(
            status=status,
            line=4,
            duration=14748
        )



@related.immutable
class Step(object):
    keyword = related.StringField()

    line = related.IntegerField()
    match = related.ChildField(Match)
    name = related.StringField()
    duration = related.FloatField()
    doc_string = related.ChildField(DocString, required=False, default=None)
    result = related.ChildField(Result, required=False, default=None)

    @classmethod
    def create(cls, step, obj, prev, tags, suite):
        keyword = ""
        temp = step.iterate.keys()
        for key in temp:
            keyword = key

        result = Result.create(step, obj, prev, tags, suite)
        st = result.status
        return cls(
            keyword=keyword.title(),
            line=3,
            name=step.description,
            doc_string=DocString.create(step, obj, st),
            duration=14748,
            match=Match.create(step),
            result=result
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
    def create(cls, case, obj, tags, suite):
        stp = []
        prev = True
        for step in case.steps:
            s = Step.create(step, obj, prev, tags, suite)
            stp.append(s)
            if s.result.status == "failed":
                prev = False
        temp = State.uuid.default

        return cls(
            keyword="Scenario",
            name=temp,
            id=(urllib.parse.quote_plus(case.name) + ";" + str(State.uuid.default)),
            line=2,
            description="",
            type="scenario",
            steps=stp,
        )


@related.immutable
class Feature(object):
    uri = related.StringField()
    keyword = related.StringField()
    id = related.StringField()
    name = related.StringField()
    line = related.IntegerField()
    duration = related.FloatField()
    elements = related.SequenceField(Element, default=[])
    description = related.StringField(required=False, default=None)
    tags = related.SequenceField(Tag, required=False, default=None)

    @classmethod
    def create(cls, case, obj, suite):
        elm = []
        tg = []
        for tag in case.tags:
            tg.append(Tag.create(tag))
        for scenario in case.scenarios:
            elm.append(Element.create(case, obj, tg, suite))

        duration = obj.running_time

        return cls(
            uri=case.file_path,
            keyword="Feature",
            id=urllib.parse.quote_plus(case.name),
            name=case.name,
            line=1,
            duration=duration,
            elements=elm,
            tags=tg
        )


@related.immutable
class Cucumber(object):
    features = related.SequenceField(Feature)

    def load_init(self, suite):
        ret = []
        for obj in suite.passed:
            ret.append(Feature.create(obj.case, obj, suite))
        for entry in suite.failed:
            ret.append(Feature.create(entry.case, entry, suite))
        return ret




