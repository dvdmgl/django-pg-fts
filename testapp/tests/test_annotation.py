# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.test import TestCase
from testapp.models import TSQueryModel, Related, TSMultidicModel
from pg_fts.ranks import (FTSRank, FTSRankDictionay, FTSRankCd,
                          FTSRankCdDictionary)
from django.core import exceptions

__all__ = ('AnnotateTestCase', 'FTSRankDictionayTestCase')


class AnnotateTestCase(TestCase):

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

    def test_ts_rank_search(self):
        q = TSQueryModel.objects.annotate(
            rank=FTSRank(tsvector__search='para mesmo')
        )

        self.assertIn('''WHERE ("testapp_tsquerymodel"."tsvector" @@ to_tsquery('english', para & mesmo))''',
                      str(q.query))

        self.assertIn('''ts_rank("testapp_tsquerymodel"."tsvector", to_tsquery('english', para & mesmo)) AS "rank"''',
                      str(q.query))

        self.assertEqual(
            q.order_by('-rank')[0].title, 'para for os the mesmo same malucos crazy')

        self.assertEqual(
            q.order_by('rank')[0].title, 'malucos crazy como like eu me')

    def test_ts_rank_isearch(self):
        q = TSQueryModel.objects.annotate(
            rank=FTSRank(tsvector__isearch='para mesmo'))

        self.assertIn('''WHERE ("testapp_tsquerymodel"."tsvector" @@ to_tsquery('english', para | mesmo))''',
                      str(q.query))

        self.assertIn('''ts_rank("testapp_tsquerymodel"."tsvector", to_tsquery('english', para | mesmo)) AS "rank"''',
                      str(q.query))

        self.assertEqual(
            q.order_by('-rank')[0].title, 'para for os the mesmo same malucos crazy')

        self.assertEqual(
            q.order_by('rank')[0].title, 'malucos crazy como like eu me')

    def test_ts_rank_tsquery(self):
        q = TSQueryModel.objects.annotate(
            rank=FTSRank(tsvector__tsquery='para & mesmo'))

        self.assertIn('''WHERE ("testapp_tsquerymodel"."tsvector" @@ to_tsquery('english', para & mesmo))''',
                      str(q.query))

        self.assertIn('''ts_rank("testapp_tsquerymodel"."tsvector", to_tsquery('english', para & mesmo)) AS "rank"''',
                      str(q.query))

        self.assertEqual(
            q.order_by('-rank')[0].title, 'para for os the mesmo same malucos crazy')

        self.assertEqual(
            q.order_by('rank')[0].title, 'malucos crazy como like eu me')

    def test_ts_rank_search_related(self):
        q = Related.objects.annotate(
            rank=FTSRank(single__tsvector__search='para mesmo')
        )
        self.assertEqual(len(q), 2)
        self.assertIn('''WHERE ("testapp_tsquerymodel"."tsvector" @@ to_tsquery('english', para & mesmo))''',
                      str(q.query))

        self.assertIn('''ts_rank("testapp_tsquerymodel"."tsvector", to_tsquery('english', para & mesmo)) AS "rank"''',
                      str(q.query))

        self.assertEqual(
            q.order_by('-rank')[0].single.title, 'para for os the mesmo same malucos crazy')

        self.assertEqual(
            q.order_by('rank')[0].single.title, 'malucos crazy como like eu me')

    def test_rank_dictionay_group_by_related(self):
        qn = Related.objects.annotate(
            rank=FTSRank(single__tsvector__search='para mesmo'))
        self.assertIn('"testapp_tsquerymodel"."tsvector"',
                      str(qn.query).split('GROUP BY')[-1])

    def test_normalization(self):
        qs = TSQueryModel.objects.annotate(
            rank=FTSRank(tsvector__tsquery='para & mesmo', normalization=[32, 8]))
        self.assertIn('''ts_rank("testapp_tsquerymodel"."tsvector", to_tsquery('english', para & mesmo), 32|8) AS "rank"''',
                      str(qs.query))
        self.assertEqual(len(qs), 2)

    def test_weights(self):
        qs = TSQueryModel.objects.annotate(
            rank=FTSRank(
                tsvector__tsquery='para & mesmo',
                normalization=(32, 8),
                weights=(0.1, 0.2, 0.4, 1.0)
            )
        )

        self.assertIn('''ts_rank('{0.1, 0.2, 0.4, 1.0}', "testapp_tsquerymodel"."tsvector", to_tsquery('english', para & mesmo), 32|8) AS "rank"''',
                      str(qs.query))

        self.assertEqual(len(qs), 2)

    def test_rank_assertions(self):
        with self.assertRaises(AssertionError):
            qs = TSQueryModel.objects.annotate(
                rank=FTSRank(
                    tsvector__tsquery='para & mesmo',
                    normalization=(2, 8),
                    weights=(0.1, 'asd', 0.4, 1.0)
                )
            )
            list(qs)
        with self.assertRaises(AssertionError):
            qs = TSQueryModel.objects.annotate(
                rank=FTSRank(
                    tsvector__tsquery='para & mesmo',
                    normalization=(3, 8),
                    weights=(0.1, 2, 0.4, 1.0)
                )
            )
            list(qs)

    # need to find a way to catch FieldError raised by
    # django.db.models.sql.query in add fields
    #
    def test_transform_dictionary_exception(self):
        with self.assertRaises(exceptions.FieldError) as msg:
            TSQueryModel.objects.annotate(
                rank=FTSRank(tsvector__nodict='malucos')),
        self.assertEqual(
            str(msg.exception),
            "The 'nodict' isn't valid Lookup for FTSRank")

        with self.assertRaises(exceptions.FieldError) as msg:
            TSQueryModel.objects.annotate(
                rank=FTSRank(tsvector='malucos')),
        self.assertEqual(
            str(msg.exception),
            "The 'tsvector' isn't valid Lookup for FTSRank")

    def test_ts_rank_cd_search(self):
        q = TSQueryModel.objects.annotate(
            rank=FTSRankCd(tsvector__search='para mesmo')
        )

        self.assertIn('''WHERE ("testapp_tsquerymodel"."tsvector" @@ to_tsquery('english', para & mesmo))''',
                      str(q.query))

        self.assertIn('''ts_rank_cd("testapp_tsquerymodel"."tsvector", to_tsquery('english', para & mesmo)) AS "rank"''',
                      str(q.query))

        self.assertEqual(
            q.order_by('-rank')[0].title, 'para for os the mesmo same malucos crazy')

        self.assertEqual(
            q.order_by('rank')[0].title, 'malucos crazy como like eu me')


class FTSRankDictionayTestCase(TestCase):
    '''tests for FTSRankDictionayTestCase'''

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

    def test_rank_dictionay_transform_search(self):
        # `para``os` are stopwords in portuguese
        qn_base_pt = TSMultidicModel.objects.filter(dictionary='portuguese')
        qn_base_en = TSMultidicModel.objects.filter(dictionary='english')
        pt = qn_base_pt.annotate(
            rank=FTSRankDictionay(tsvector__portuguese__tsquery='para & os'))

        self.assertIn(
            '''("testapp_tsmultidicmodel"."tsvector" @@ to_tsquery('portuguese', para & os))''',
            str(pt.query))

        self.assertIn(
            '''ts_rank("testapp_tsmultidicmodel"."tsvector", to_tsquery('portuguese', para & os)) AS "rank"''',
            str(pt.query))

        en = qn_base_pt.annotate(
            rank=FTSRankDictionay(tsvector__english__tsquery='para & os'))

        self.assertIn(
            '''("testapp_tsmultidicmodel"."tsvector" @@ to_tsquery('english', para & os))''',
            str(en.query))

        self.assertIn(
            '''ts_rank("testapp_tsmultidicmodel"."tsvector", to_tsquery('english', para & os)) AS "rank"''',
            str(en.query))

        qn_base_pt.annotate(
            rank=FTSRankDictionay(tsvector__portuguese__tsquery='para & os')
        )

    def test_rank_dictionay_related_multidict(self):
        qn_base_pt = Related.objects.filter(multiple__dictionary='portuguese')
        qn_base_en = Related.objects.filter(multiple__dictionary='english')
        qn_pt = qn_base_pt.annotate(rank=FTSRankDictionay(
            multiple__tsvector__portuguese__tsquery='para & os'))

        qn_en = qn_base_en.annotate(rank=FTSRankDictionay(
            multiple__tsvector__english__tsquery='para & os'))

        self.assertIn('''"testapp_tsmultidicmodel"."tsvector" @@ to_tsquery('english', para & os))''',
                      str(qn_en.query))

        self.assertIn('''ts_rank("testapp_tsmultidicmodel"."tsvector", to_tsquery('english', para & os)) AS "rank"''',
                      str(qn_en.query))

        self.assertIn('''"testapp_tsmultidicmodel"."tsvector" @@ to_tsquery('portuguese', para & os))''',
                      str(qn_pt.query))

        self.assertIn('''ts_rank("testapp_tsmultidicmodel"."tsvector", to_tsquery('portuguese', para & os)) AS "rank"''',
                      str(qn_pt.query))

        self.assertEqual(len(qn_en), 1)
        self.assertEqual(len(qn_pt), 0)

    def test_rank_dictionay_group_by_related(self):
        qn_base_pt = Related.objects.filter(multiple__dictionary='portuguese')
        qn_pt = qn_base_pt.annotate(rank=FTSRankDictionay(
            multiple__tsvector__portuguese__tsquery='para & os'))

        self.assertIn('"testapp_tsmultidicmodel"."tsvector"',
                      str(qn_pt.query).split('GROUP BY')[-1])

    def test_rank_cd_dictionary(self):
        qn_base_pt = Related.objects.filter(multiple__dictionary='portuguese')
        qn_base_en = Related.objects.filter(multiple__dictionary='english')
        qn_pt = qn_base_pt.annotate(rank=FTSRankCdDictionary(
            multiple__tsvector__portuguese__tsquery='para & os'))

        qn_en = qn_base_en.annotate(rank=FTSRankCdDictionary(
            multiple__tsvector__english__tsquery='para & os'))

        self.assertIn('''"testapp_tsmultidicmodel"."tsvector" @@ to_tsquery('english', para & os))''',
                      str(qn_en.query))

        self.assertIn('''ts_rank_cd("testapp_tsmultidicmodel"."tsvector", to_tsquery('english', para & os)) AS "rank"''',
                      str(qn_en.query))

        self.assertIn('''"testapp_tsmultidicmodel"."tsvector" @@ to_tsquery('portuguese', para & os))''',
                      str(qn_pt.query))

        self.assertIn('''ts_rank_cd("testapp_tsmultidicmodel"."tsvector", to_tsquery('portuguese', para & os)) AS "rank"''',
                      str(qn_pt.query))

    def test_transform_dictionary_exception(self):
        with self.assertRaises(exceptions.FieldError) as msg:
            TSMultidicModel.objects.annotate(
                rank=FTSRankDictionay(tsvector__nodict='malucos')),
        self.assertEqual(
            str(msg.exception),
            "The 'nodict' isn't valid Lookup for FTSRankDictionay")

    def test_transform_exception(self):
        with self.assertRaises(exceptions.FieldError) as msg:
            list(TSMultidicModel.objects.annotate(
                rank=FTSRankDictionay(tsvector__portuguese='malucos')))
        self.assertEqual(
            str(msg.exception),
            "The 'portuguese' isn't valid Lookup for FTSRankDictionay")
