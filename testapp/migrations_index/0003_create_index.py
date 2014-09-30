# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from pg_fts.migrations import CreateFTSIndexOperation


class Migration(migrations.Migration):

    dependencies = [
        ("testapp", "0002_create_model"),
    ]

    operations = [
        CreateFTSIndexOperation(
            name='TSVectorModel',
            fts_vector='tsvector',
            index='gin'
            ),
        ]
