from django.test import TestCase
from pg_fts.fields import TSVectorField
from django.db import models

__all__ = ('TestChecks', )


class TestChecks(TestCase):

    def test_check_erros(self):
        class TSVectorModelClean(models.Model):
            title = models.CharField(max_length=50)
            body = models.TextField()

            tsvector = TSVectorField(
                (('title', 'A'), 'body'), fts_index='gin')

        error_clean = TSVectorModelClean._meta.get_field('tsvector')
        self.assertEqual(len(error_clean.check()), 0)

        class TSVectorModelError(models.Model):
            title = models.CharField(max_length=50)
            body = models.TextField()

            tsvector = TSVectorField(
                (('x', 'z'), 'body'), fts_index='asd')

        error = TSVectorModelError._meta.get_field('tsvector')

        self.assertEqual(len(error.check()), 3)
