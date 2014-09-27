# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.test import TestCase
from testapp.models import TSQueryModel, TSMultidicModel, Related
from django.core import exceptions
from django.utils import encoding
from pg_fts.aggregates import FTSRank

__all__ = ('TestQueryingSingleDictionary', 'TestQueryingMultiDictionary')


class TestQueryingSingleDictionary(TestCase):

    def setUp(self):
        a = TSQueryModel.objects.create(
            title='para for os the mesmo same malucos crazy',
            body="""para for os the mesmo same malucos crazy que that tomorow
salvão save o the planeta planet"""
        )

        b = TSQueryModel.objects.create(
            title='malucos crazy como like eu me',
            body="""para for os the mesmo same malucos crazy que that tomorow
salvão save o the planeta planet"""
        )
        Related.objects.create(single=a)
        Related.objects.create(single=b)

    def test_search(self):
        q = TSQueryModel.objects.filter(tsvector__search='para mesmo')
        self.assertEqual(len(q), 2)
        self.assertIn('''WHERE "testapp_tsquerymodel"."tsvector" @@ to_tsquery('english', para & mesmo)''',
                      str(q.query))
        self.assertEqual(
            q[0].title, 'para for os the mesmo same malucos crazy')
        self.assertEqual(
            len(TSQueryModel.objects.filter(
                tsvector__search='para mesmo todos')),
            0
        )

    def test_isearch(self):
        q = TSQueryModel.objects.filter(tsvector__isearch='para mesmo')
        self.assertEqual(
            q[0].title, 'para for os the mesmo same malucos crazy')

        self.assertIn('''WHERE "testapp_tsquerymodel"."tsvector" @@ to_tsquery('english', para | mesmo)''',
                      str(q.query))
        self.assertEqual(
            len(TSQueryModel.objects.filter(
                tsvector__isearch='para mesmo todos')),
            2
        )

    def test_tsquery(self):
        q = TSQueryModel.objects.filter(tsvector__tsquery='para & mesmo')
        self.assertEqual(
            q[0].title, 'para for os the mesmo same malucos crazy')
        self.assertEqual(
            len(TSQueryModel.objects.filter(
                tsvector__tsquery='para | mesmo | todos')),
            2
        )
        self.assertIn('''WHERE "testapp_tsquerymodel"."tsvector" @@ to_tsquery('english', para & mesmo)''',
                      str(q.query))

    def test_tsquery_re(self):
        q = TSQueryModel.objects.filter(
            tsvector__tsquery="'single-quoted phrases' & prefix:A*B & !not  | or | weight:ABC"
        )
        self.assertEqual(len(q), 0)  # just test for no errors

    def test_nonasc(self):  # fail
        ao = TSQueryModel.objects.filter(
            tsvector__isearch='canção & é & vèz',
        )
        self.assertIn(
            b'''WHERE "testapp_tsquerymodel"."tsvector" @@ to_tsquery('english', can\xc3\xa7\xc3\xa3o | \xc3\xa9 | v\xc3\xa8z)''',
            encoding.smart_bytes(ao.query)
        )

    def test_related_search(self):
        q = Related.objects.filter(single__tsvector__search='para mesmo')
        self.assertEqual(len(q), 2)



class TestQueryingMultiDictionary(TestCase):

    def setUp(self):
        title = 'para for os the mesmo same malucos crazy'
        body = """para for os the mesmo same malucos crazy que that tomorow
salvão save o the planeta planet"""
        pt = TSMultidicModel.objects.create(
            title=title,
            body=body,
            dictionary='english'
        )

        en = TSMultidicModel.objects.create(
            title=title,
            body=body,
            dictionary='portuguese'
        )

        Related.objects.create(
            multiple=pt
        )

        Related.objects.create(
            multiple=en
        )

    def test_different_vectors_for_different_dictionaries(self):
        pt = TSMultidicModel.objects.filter(dictionary='portuguese')
        en = TSMultidicModel.objects.filter(dictionary='english')
        self.assertNotEqual(pt[0].tsvector, en[0].tsvector)

    def test_dictinary_transform_search(self):
        # `para``os` are stopwords in portuguese
        self.assertEqual(len(
            TSMultidicModel.objects.filter(
                tsvector__portuguese__tsquery='para & os',
                dictionary='portuguese'
            )
            ), 0)

        self.assertEqual(len(
            TSMultidicModel.objects.filter(
                tsvector__portuguese__search='para os',
                dictionary='portuguese'
            )
            ), 0)

        self.assertEqual(len(
            TSMultidicModel.objects.filter(
                tsvector__portuguese__isearch='para os',
                dictionary='portuguese'
            )
            ), 0)

        self.assertEqual(len(
            TSMultidicModel.objects.filter(
                tsvector__english__tsquery='para & os',
                dictionary='english'
            )
            ), 1)

        self.assertEqual(len(
            TSMultidicModel.objects.filter(
                tsvector__english__search='para os',
                dictionary='english'
            )
            ), 1)

        self.assertEqual(len(
            TSMultidicModel.objects.filter(
                tsvector__english__isearch='para & os',
                dictionary='english'
            )
            ), 1)

    def test_related_multidict(self):
        self.assertEqual(len(
            Related.objects.filter(
                multiple__tsvector__portuguese__tsquery='para & os',
                multiple__dictionary='portuguese'
            )
            ), 0)

        self.assertEqual(len(
            Related.objects.filter(
                multiple__tsvector__portuguese__search='para os',
                multiple__dictionary='portuguese'
            )
            ), 0)

        self.assertEqual(len(
            Related.objects.filter(
                multiple__tsvector__portuguese__isearch='para os',
                multiple__dictionary='portuguese'
            )
            ), 0)

        self.assertEqual(len(
            Related.objects.filter(
                multiple__tsvector__english__tsquery='para & os',
                multiple__dictionary='english'
            )
            ), 1)

        self.assertEqual(len(
            Related.objects.filter(
                multiple__tsvector__english__search='para os',
                multiple__dictionary='english'
            )
            ), 1)

        self.assertEqual(len(
            Related.objects.filter(
                multiple__tsvector__english__isearch='para & os',
                multiple__dictionary='english'
            )
            ), 1)

    def test_transform_dictionary_exception(self):
        with self.assertRaises(exceptions.FieldError) as msg:
            TSMultidicModel.objects.filter(tsvector__nodict='malucos'),
        self.assertEqual(str(msg.exception), "The 'nodict' is not in testapp.TSMultidicModel.dictionary choices")

    def test_transform_exception(self):
        with self.assertRaises(exceptions.FieldError) as msg:
            list(TSMultidicModel.objects.filter(tsvector__portuguese='malucos'))
        self.assertEqual(str(msg.exception), "'exact' isn't valid Lookup for TSVectorBaseField")
