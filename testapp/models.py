# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.utils.encoding import python_2_unicode_compatible

from pg_fts.fields import TSVectorField
from django.db import models


@python_2_unicode_compatible
class TSQueryModel(models.Model):
    title = models.CharField(max_length=50)
    body = models.TextField()

    tsvector = TSVectorField(('title', 'body'))

    def __str__(self):
        return self.title


@python_2_unicode_compatible
class TSMultidicModel(models.Model):
    title = models.CharField(max_length=50)
    body = models.TextField()
    dictionary = models.CharField(
        max_length=15,
        choices=(('english', 'english'), ('portuguese', 'portuguese')),
        default='english'
    )
    tsvector = TSVectorField((('title', 'A'), 'body'),
                             dictionary='dictionary')

    def __str__(self):
        return self.title


class Related(models.Model):
    single = models.ForeignKey(TSQueryModel, blank=True, null=True)
    multiple = models.ForeignKey(TSMultidicModel, blank=True, null=True)
