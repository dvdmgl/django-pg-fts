from django.db import models

from pg_fts.fields import TSVectorField


class Article(models.Model):
    title = models.CharField(max_length=255)
    article = models.TextField()

    fts_index = TSVectorField(
        (('title', 'A'), 'article'),
        dictionary='portuguese'
    )

    def __str__(self):
        return self.title
