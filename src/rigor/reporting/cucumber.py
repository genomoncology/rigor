import json
import urllib
import related


@related.immutable
class Tag(object):
    name = related.StringField()
    # line = related.IntegerField()

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
    def create_failure(cls, step, failure):
        v = []
        for fail_validation in failure.fail_validations:
            i = 0
            for item in fail_validation.actual:
                if fail_validation.actual[i] != fail_validation.expect[i]:
                    v.append(Validators.create_failing(fail_validation.actual[i], fail_validation.expect[i]))
                i += 1
        spacer = "====================\n"

        return cls(
            value=spacer + " FAILED VALIDATIONS\n" + spacer + related.to_json(json.loads(related.to_json(v))),
            content_type="application/json",
            line=5
        )


@related.immutable
class Result(object):
    status = related.StringField()
    line = related.IntegerField()
    #todo: figure out durations & error message
    duration = related.IntegerField()

    @classmethod
    def create(cls, step):

        for validations in step.validate:
            if validations.actual != validations.expect:
                status = "failed"
                return cls(
                        status=status,
                        line=4,
                        duration=1
                )
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
    def create(cls, step, failure):

        return cls(
            keyword="",
            line=3,
            name=step.description,
            doc_string=DocString.create_failure(step, failure),
            match=Match.create(step),
            result=Result.create(step)
        )


# @related.immutable
# class Row(object):
#     # line = related.IntegerField()
#     id = related.StringField()
#     cells = related.SequenceField(str)
#
#     @classmethod
#     def create_first(cls, example, case):
#         dct = example.result[0]
#         dct = dct.keys()
#         cells = []
#         for key in dct:
#             temp = key
#             cells.append(temp)
#         return cls(
#             cells=cells,
#             id=urllib.parse.quote_plus(case.name) + ";" + str(Element.name) + ";" + "PlaceHolder" + ";1"
#             # todo: Find a way tor replace "PlaceHolder" with example.name
#         )
#
#     @classmethod
#     def create(cls, example, case, i):
#         dct = example.result[0]
#         dct = dct.keys()
#         cells = []
#         for key in dct:
#             cells.append(example.result[i][key])
#         return cls(
#             cells=cells,
#             id=urllib.parse.quote_plus(case.name) + ";" + str(Element.name) + ";" + "PlaceHolder" + ";%s" % i
#             # todo: Find a way to replace "PlaceHolder" with example.name
#         )


# @related.immutable
# class Example(object):
#     keyword = related.StringField()
#     name = related.StringField()
#     # line = related.IntegerField()
#     description = related.StringField()
#     id = related.StringField()
#     rows = related.SequenceField(Row)
#
#     @classmethod
#     def create(cls, case, example):
#         rows = []
#         rows.append(Row.create_first(example, case))
#         i = 0
#         for item in example.result:
#             rows.append(Row.create(example, case, i))
#             i += 1
#         return cls(
#             keyword="Examples",
#             # Todo: Figure out how to replace "PlaceHolder" with example.name
#             name="PlaceHolder",
#             description="Placeholder description",
#             # Todo: Figure out how to replace "Placeholder description" with example.description
#             id=urllib.parse.quote_plus(case.name) + ";outline;" + "PlaceHolder",
#             rows=rows
#         )


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
    def create(cls, case, failure):
        stp = []
        tg = []
        for step in case.steps:
            stp.append(Step.create(step, failure))
        for tag in case.tags:
            tg.append(Tag.create(tag))
        return cls(
            keyword="Scenario",
            # Scenario name
            name="EGFR L858R and Non-Small Cell Lung Carcinoma",
            id=(urllib.parse.quote_plus(case.name) + ";PlaceHolder"),
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
    def create(cls, case, failure):
        elm = []
        for scenario in case.scenarios:
            elm.append(Element.create(case, failure))

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
        for failure in suite.failed:
            ret.append(Feature.create(failure.case, failure))
        return ret




