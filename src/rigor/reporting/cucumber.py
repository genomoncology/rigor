import enum
import os
import aiohttp
import jmespath
import ast

from mako.template import Template

import related

from rigor.model import Result, Case, Step
from django.db import models

class Feature(object):
    uri: related.StringField(Cucumber)
    keyword: models.CharField(required=True, default='Feature')
    name: related.StringField(Cucumber.feature.name, required=True)





class Cucumber(object):
    elements = related.SequenceField()
    steps = related.SequenceField(Step)
    examples = related.ImmutableDict(Case.scenarios, required=False)
    feature = related.ImmutableDict(Result.case)

    def to_report(self, step, scenario, result):
        elements = self.elements
