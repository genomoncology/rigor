import json
import urllib
from collections import deque

import jmespath
import related
from django.db import models

from rigor.model import Suite


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
class Result(object):
    status = related.StringField()
    #todo: figure out durations & error message
    duration = related.IntegerField()
    # error_message = related.StringField(required=False, repr=False, cmp=False)

    @classmethod
    def create(cls, step):
        for validations in step.validate:
            if validations.actual != validations.expect:
                status = "failed"
                return cls(
                        status=status,
                        duration=1
                )
            status = "passed"
            return cls(
                status=status,
                duration=1
            )


@related.immutable
class Step(object):
    keyword = related.StringField()

    # line = related.IntegerField()
    match = related.ChildField(Match)
    name = related.StringField(default="Step")
    result = related.ChildField(Result, required=False, default=None)

    @classmethod
    def create(cls, step):
        return cls(
            keyword="",
            name=step.description,
            match=Match.create(step),
            result=Result.create(step)
        )


@related.immutable
class Row(object):
    # line = related.IntegerField()
    id = related.StringField()
    cells = related.SequenceField(str)

    @classmethod
    def create_first(cls, example, case):
        dct = example.result[0]
        dct = dct.keys()
        cells = []
        for key in dct:
            temp = key
            cells.append(temp)
        return cls(
            cells=cells,
            id=urllib.parse.quote_plus(case.name) + ";" + str(Element.name) + ";" + "PlaceHolder" + ";1"
            # todo: Find a way tor replace "PlaceHolder" with example.name
        )

    @classmethod
    def create(cls, example, case, i):
        dct = example.result[0]
        dct = dct.keys()
        cells = []
        for key in dct:
            cells.append(example.result[i][key])
        return cls(
            cells=cells,
            id=urllib.parse.quote_plus(case.name) + ";" + str(Element.name) + ";" + "PlaceHolder" + ";%s" % i
            # todo: Find a way to replace "PlaceHolder" with example.name
        )


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
    # examples = related.SequenceField(Example, required=False, default=None)
    tags = related.SequenceField(Tag, required=False, default=None)


    @classmethod
    def create(cls, case):
        stp = []
        exp = []
        tg = []
        for step in case.steps:
            stp.append(Step.create(step))
        # for scenario in case.scenarios:
        #     exp.append(Example.create(case, scenario))
        for tag in case.tags:
            tg.append(Tag.create(tag))
        return cls(
            keyword="Scenario",
            # Scenario name
            name="EGFR L858R and Non-Small Cell Lung Carcinoma",
            id=(urllib.parse.quote_plus(case.name) + ";PlaceHolder"),
            line=5,
            description="",
            type="scenario",
            steps=stp,
            # examples=exp,
            tags=tg
        )


@related.immutable
class Feature(object):
    uri = related.StringField()
    keyword = related.StringField()
    id = related.StringField()
    name = related.StringField()
    # line = related.IntegerField()
    elements = related.SequenceField(Element, default=[])
    description = related.StringField(required=False, default=None)

    # tags = related.SequenceField(Tag, required=False, default=None)

    @classmethod
    def create(cls, case):
        elm = []
        for scenario in case.scenarios:
            elm.append(Element.create(case))

        return cls(
            uri=case.file_path,
            keyword="Feature",
            id=urllib.parse.quote_plus(case.name),
            name=case.name,
            elements=elm,
        )

@related.immutable
class Cucumber(object):
    features = related.SequenceField(Feature)

    def load_init(self, suite):
        ret = []
        for failure in suite.failed:
            ret.append(Feature.create(failure.case))
        return ret

        # raw = Feature.create(suite.failed[0].case)
        # print(str(raw))
        # temp = related.to_json(raw)
        # cuke = json.loads(temp)
        # return cuke




