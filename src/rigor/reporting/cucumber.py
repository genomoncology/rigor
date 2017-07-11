import json
import urllib
import related


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
    content_type = related.StringField()
    line = related.IntegerField()

    @classmethod
    def create(cls, res, result):
        v = []
        if result.status == "skipped":
            return cls(
                value="=== STEP NOT EXECUTED ===",
                content_type="application/json",
                line=6
            )
        spacer = "====================\n"
        for validation in res.validations:
            st = True
            if not validation.success:
                v.append(Validators.create_failing(validation.actual, validation.expect))
                st = False
            req = related.to_json(json.loads(related.to_json(res.fetch)))
            if res.fetch.method == "post":
                ret = related.to_json(json.loads(related.to_json(res.response)))
                ret = ret + "\nHTTP Response: " + str(res.status)
            else:
                ret = related.to_json(json.loads(related.to_json(validation.actual)))


        if st is True:
            return cls(
                value=(spacer + "   REQUEST   \n" + spacer + req + "\n\n\n" + spacer + "   RESULT   \n" + spacer + ret),
                content_type="application/json",
                line=6
            )
        else:
            return cls(
                value=spacer + "   RESULT   \n" + spacer + req + "\n\n\n" + spacer + "   RESULT   \n" + spacer + ret +
                      "\n\n\n" + " FAILED VALIDATIONS\n" + spacer + related.to_json(json.loads(related.to_json(v))),
                content_type="application/json",
                line=6
            )


@related.immutable
class Result(object):
    status = related.StringField()
    line = related.IntegerField()

    @classmethod
    def create(cls, res):
        if res.success is True:
            status = "passed"
        elif res.success is False:
            status = "failed"
        else:
            status = "skipped"
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
    result = related.ChildField(Result, required=False, default=None)

    @classmethod
    def create(cls, res, obj):
        keyword = ""
        temp = res.step.iterate.keys()
        for key in temp:
            keyword = key

        result = Result.create(res)
        return cls(
            keyword=keyword.title(),
            line=3,
            name=res.step.description,
            doc_string=DocString.create(res, result),
            duration=obj.running_time,
            match=Match.create(res.step),
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
    def create(cls, obj):
        stp = []
        for res in obj.step_results:
            s = Step.create(res, obj)
            stp.append(s)
        temp = obj.uuid

        return cls(
            keyword="Scenario",
            name=temp,
            id=(urllib.parse.quote_plus(obj.case.name) + ";" + str(obj.uuid)),
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
    elements = related.SequenceField(Element, default=[])
    description = related.StringField(required=False, default=None)
    tags = related.SequenceField(Tag, required=False, default=None)

    @classmethod
    def create(cls, suite_result):
        elm = []
        tg = []
        for obj in suite_result.passed:
            for tag in obj.case.tags:
                tg.append(Tag.create(tag))
            elm.append(Element.create(obj))
        for obj in suite_result.failed:
            elm.append(Element.create(obj))

        return cls(
            uri=obj.case.file_path,
            keyword="Feature",
            id=urllib.parse.quote_plus(obj.case.name),
            name=obj.case.name,
            line=1,
            elements=elm,
            tags=tg
        )


@related.immutable
class Cucumber(object):
    features = related.SequenceField(Feature)

    def load_init(self, suite_result):
        ret = []
        ret.append(Feature.create(suite_result))
        return ret



