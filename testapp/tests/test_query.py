from django.test import TestCase
from testapp.models import TSQueryModel, TSMultidicModel
from django.core import exceptions


__all__ = ('TestQueryingSingleDictionary', 'TestQueryingMultiDictionary')


class TestQueryingSingleDictionary(TestCase):

    def setUp(self):
        TSQueryModel.objects.create(
            title='para for os the mesmo same malucos crazy',
            body="""para for os the mesmo same malucos crazy que that tomorow
salvão save o the planeta planet"""
        )

        TSQueryModel.objects.create(
            title='malucos crazy como like eu me',
            body="""para for os the mesmo same malucos crazy que that tomorow
salvão save o the planeta planet"""
        )

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


class TestQueryingMultiDictionary(TestCase):

    def setUp(self):
        title = 'para for os the mesmo same malucos crazy'
        body = """para for os the mesmo same malucos crazy que that tomorow
salvão save o the planeta planet"""
        TSMultidicModel.objects.create(
            title=title,
            body=body,
            dictionary='english'
        )

        TSMultidicModel.objects.create(
            title=title,
            body=body,
            dictionary='portuguese'
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

    def test_transform_dictionary_exception(self):
        with self.assertRaises(exceptions.FieldError) as msg:
            TSMultidicModel.objects.filter(tsvector__nodict='malucos'),
        self.assertEqual(str(msg.exception), "The 'nodict' is not in testapp.TSMultidicModel.dictionary choices")

    def test_transform_exception(self):
        with self.assertRaises(exceptions.FieldError) as msg:
            list(TSMultidicModel.objects.filter(tsvector__portuguese='malucos'))
        self.assertEqual(str(msg.exception), "'exact' isn't valid Lookup for TSVectorBaseField")
