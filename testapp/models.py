# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.utils.encoding import python_2_unicode_compatible

from pg_fts.fields import TSVectorField
from django.db import models


@python_2_unicode_compatible
class TSVectorModel(models.Model):
    title = models.CharField(max_length=50)
    body = models.TextField()

    tsvector = TSVectorField(('title', 'body'), db_column='wtf', db_index=True)

    def __str__(self):
        return self.title


@python_2_unicode_compatible
class TSQueryModel(models.Model):
    title = models.CharField(max_length=50)
    body = models.TextField()

    tsvector = TSVectorField(('title', 'body'), fts_index='gin')

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
    tsvector = TSVectorField((('title', 'A'), 'body'), fts_index='gin',
                             dictionary='dictionary')

    def __str__(self):
        return self.title
