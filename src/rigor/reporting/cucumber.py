import related


@related.immutable
class Tag(object):
    name = related.StringField()
    line = related.IntegerField()


@related.immutable
class Feature(object):
    uri = related.StringField()
    keyword = related.StringField()
    id = related.StringField()
    name = related.StringField()
    line = related.IntegerField()
    description = related.StringField()
    tags = related.SequenceField(Tag)


@related.immutable
class Cucumber(object):
    features = related.SequenceField(Feature)




# class Feature(object):
#     uri: related.StringField(Cucumber)
#     keyword: models.CharField(required=True, default='Feature')
#     name: related.StringField(Cucumber.feature.name, required=True)
#
#
# class Cucumber(object):
#     elements = related.SequenceField()
#     steps = related.SequenceField(Step)
#     examples = related.ImmutableDict(Case.scenarios, required=False)
#     feature = related.ImmutableDict(Result.case)
#
#     def to_report(self, step, scenario, result):
#         elements = self.elements
