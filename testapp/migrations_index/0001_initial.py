# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import pg_fts.fields
from pg_fts.migrations import CreateFTSIndexOperation, CreateFTSTriggerOperation


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='TSMultidicModel',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, verbose_name='ID', primary_key=True)),
                ('title', models.CharField(max_length=50)),
                ('body', models.TextField()),
                ('dictionary', models.CharField(max_length=15, default='english', choices=[('english', 'english'), ('portuguese', 'portuguese')])),
                ('tsvector', pg_fts.fields.TSVectorField(editable=False, dictionary='dictionary', default='', fields=(('title', 'A'), 'body'), serialize=False, null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='TSQueryModel',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, verbose_name='ID', primary_key=True)),
                ('title', models.CharField(max_length=50)),
                ('body', models.TextField()),
                ('tsvector', pg_fts.fields.TSVectorField(editable=False, dictionary='english', default='', fields=('title', 'body'), serialize=False, null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        CreateFTSIndexOperation(
            name='TSQueryModel',
            fts_vector='tsvector',
            index='gin'
        ),
        CreateFTSIndexOperation(
            name='TSMultidicModel',
            fts_vector='tsvector',
            index='gin'
        ),
        CreateFTSTriggerOperation(
            name='TSQueryModel',
            fts_vector='tsvector',
        ),
        CreateFTSTriggerOperation(
            name='TSMultidicModel',
            fts_vector='tsvector',
        ),

    ]
