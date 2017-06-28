import urllib

import related


@related.immutable
class Tag(object):
    name = related.StringField()
    line = related.IntegerField()


@related.immutable
class Match(object):
    location = related.StringField()

    # def get_location(self, step):
    #     self.location = step.name
    #     return self


@related.immutable
class Result(object):
    status = related.StringField()
    duration = related.IntegerField()
    error_message = related.StringField(required=False, repr=False, cmp=False)

    # def get_status(self, step):
    #     for validations in step.validate:
    #         if step.validate.actual != step.validate.expect:
    #             self.status = "failed"
    #             return self
    #     self.status = "passed"
    #     return self

    # def load_result(self, step):
    #     self.status = self.get_status(step)
    #     return self


@related.immutable
class Embedding(object):
    mime_type = related.StringField()
    data = related.StringField()


@related.immutable
class Step(object):
    keyword = related.StringField()
    name = related.StringField()
    line = related.IntegerField()
    match = related.ChildField(Match)
    result = related.ChildField(Result, required=False, default=None)
    embeddings = related.SequenceField(Embedding, required=False, default=None)

    # def load_step(self, step):
    #     self.keyword = ""
    #     self.name = step.name
    #     self.match = Match.get_location(self.match, step)
    #     self.result = Result.load_result(self.result, step)
    #     return self


@related.immutable
class Row(object):
    line = related.IntegerField()
    id = related.StringField()
    cells = related.SequenceField(str)


@related.immutable
class Example(object):
    keyword = related.StringField()
    name = related.StringField()
    line = related.IntegerField()
    description = related.StringField()
    id = related.StringField()
    rows = related.SequenceField(Row)

    # def load_example(self):


@related.immutable
class Element(object):
    keyword = related.StringField()
    id = related.StringField()
    name = related.StringField()
    line = related.IntegerField()
    description = related.StringField()
    type = related.StringField()
    steps = related.SequenceField(Step)
    examples = related.SequenceField(Example, required=False, default=None)
    tags = related.SequenceField(Tag, required=False, default=None)

    # def add_step(self, step):
    #     temp = Step.load_step(self.temp, step)
    #     self.steps.add(temp)

    # def add_example(self, scenario):
    #     temp = Example.load_example(self.temp, scenario)



    # def load_element(self, case):
    #     for step in case.steps:
    #         self.add_step(step)
        # for example in case.scenarios:
        #     self.add_example(example)



@related.immutable
class Feature(object):
    uri = related.StringField()
    keyword = related.StringField()
    id = related.StringField()
    name = related.StringField()
    line = related.IntegerField()
    description = related.StringField()
    elements = related.SequenceField(Element)
    tags = related.SequenceField(Tag, required=False, default=None)

    # def generate_id(self, case):
    #     id = urllib.parse.quote_plus(case.name)
    #     self.id = id

    # def load_feature(self, case):
    #     self.generate_id(case)
    #     self.keyword = "Feature"
    #     self.name = case.name
    #     self.description = case.description


@related.immutable
class Cucumber(object):
    features = related.SequenceField(Feature)
