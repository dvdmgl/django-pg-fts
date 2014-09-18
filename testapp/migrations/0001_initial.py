# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from testapp.models import TSQueryModel, TSMultidicModel
import pg_fts.fields
from pg_fts.migrations import CreateFTSIndexOperation


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
                ('tsvector', pg_fts.fields.TSVectorField(editable=False, dictionary='dictionary', default='', fields=(('title', 'A'), 'body'), serialize=False, null=True, fts_index='gin')),
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
                ('tsvector', pg_fts.fields.TSVectorField(editable=False, dictionary='english', default='', fields=('title', 'body'), serialize=False, null=True, fts_index='gin')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='TSVectorModel',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, verbose_name='ID', primary_key=True)),
                ('title', models.CharField(max_length=50)),
                ('body', models.TextField()),
                ('tsvector', pg_fts.fields.TSVectorField(db_index=True, editable=False, dictionary='english', default='', db_column='wtf', fields=('title', 'body'), serialize=False, null=True, fts_index='gin')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        CreateFTSIndexOperation(
            model=TSQueryModel,
            fts_vectors=[
                ('tsvector', pg_fts.fields.TSVectorField(
                    editable=False, dictionary='english',
                    fts_index='gin',
                    fields=('title', 'body'), serialize=False,
                    null=True, default='')),
            ]
        ),
        CreateFTSIndexOperation(
            model=TSMultidicModel,
            fts_vectors=[
                ('tsvector', pg_fts.fields.TSVectorField(
                    editable=False, dictionary='dictionary',
                    fts_index='gin',
                    fields=(('title', 'A'), 'body'), serialize=False,
                    null=True, default='')),
            ]
        )


    ]
