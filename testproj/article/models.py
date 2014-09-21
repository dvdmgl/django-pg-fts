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


class ArticleMulti(models.Model):
    title = models.CharField(max_length=255)
    article = models.TextField()
    dictionary = models.CharField(
        max_length=15,
        choices=(('english', 'english'), ('portuguese', 'portuguese')),
        default='english'
    )

    fts_index = TSVectorField(
        (('title', 'A'), 'article'),
        dictionary='dictionary'
    )

    def __str__(self):
        return self.title
