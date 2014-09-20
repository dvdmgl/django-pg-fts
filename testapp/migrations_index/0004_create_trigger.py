# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from pg_fts.migrations import CreateFTSTriggerOperation


class Migration(migrations.Migration):

    dependencies = [
        ("testapp", "0003_create_index"),
    ]

    operations = [
        CreateFTSTriggerOperation(
            name='TSVectorModel',
            fts_vector='tsvector'
            ),
        ]
