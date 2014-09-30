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
                ('dictionary', models.CharField(max_length=15, default='english', choices=[('english', 'english'), ('portuguese', 'portuguese')])),
                ('body', models.TextField()),
                ('tsvector', pg_fts.fields.TSVectorField(
                    db_index=True, editable=False,
                    dictionary='dictionary', default='',
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
