# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from pg_fts.migrations import (DeleteFTSTriggerOperation,
                               DeleteFTSIndexOperation)


class Migration(migrations.Migration):

    dependencies = [
        ("testapp", "0004_create_trigger"),
    ]

    operations = [
        DeleteFTSTriggerOperation(
            name='TSVectorModel',
            fts_vector='tsvector'
            ),
        DeleteFTSIndexOperation(
            name='TSVectorModel',
            fts_vector='tsvector',
            index='gin'
            ),
        migrations.DeleteModel(
            name='TSVectorModel'
        )
    ]
