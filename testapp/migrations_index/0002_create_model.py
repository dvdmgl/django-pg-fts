# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import pg_fts.fields
from pg_fts.migrations import UpdateVectorOperation

class Migration(migrations.Migration):

    dependencies = [
        ("testapp", "0001_initial"),
    ]

    operations = [

        migrations.CreateModel(
            name='TSVectorModel',
            fields=[
                ('id', models.AutoField(
                    serialize=False, auto_created=True,
                    verbose_name='ID', primary_key=True)),
                ('title', models.CharField(max_length=50)),
                ('body', models.TextField()),
                ('tsvector', pg_fts.fields.TSVectorField(
                    db_index=False, editable=False,
                    dictionary='english', default='',
                    fields=('title', 'body'),
                    serialize=False, null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        UpdateVectorOperation(
            name='TSVectorModel',
            fts_vector='tsvector'
        ),

    ]
