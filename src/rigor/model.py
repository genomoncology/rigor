import related


@related.immutable
class File(object):
    rigor = related.StringField()
    context = related.ChildField(dict)
    outline = related.ChildField(dict)
