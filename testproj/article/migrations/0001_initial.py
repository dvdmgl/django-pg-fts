# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import pg_fts.fields
from pg_fts.migrations import (CreateFTSIndexOperation,
                               CreateFTSTriggerOperation)


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Article',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=255)),
                ('article', models.TextField()),
                ('fts_index', pg_fts.fields.TSVectorField(editable=False, serialize=False, null=True, fields=(('title', 'A'), 'article'), dictionary='portuguese', default='')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ArticleMulti',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=255)),
                ('article', models.TextField()),
                ('dictionary', models.CharField(max_length=15, default='english', choices=[('english', 'english'), ('portuguese', 'portuguese')])),
                ('fts_index', pg_fts.fields.TSVectorField(editable=False, serialize=False, null=True, fields=(('title', 'A'), 'article'), dictionary='dictionary', default='')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        CreateFTSIndexOperation(
            name='Article',
            fts_vector='fts_index',
            index='gin'
        ),
        CreateFTSIndexOperation(
            name='ArticleMulti',
            fts_vector='fts_index',
            index='gin'
        ),
        CreateFTSTriggerOperation(
            name='Article',
            fts_vector='fts_index'
        ),
        CreateFTSTriggerOperation(
            name='ArticleMulti',
            fts_vector='fts_index'
        ),
    ]
