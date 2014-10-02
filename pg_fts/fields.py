# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db.models import Field, Lookup, Transform
from django.db.models.lookups import RegisterLookupMixin
from django.utils import six
from django.core import checks, exceptions
from django.utils.translation import string_concat, ugettext_lazy as _
from django.db import models
import re

__all__ = ('TSVectorField', 'TSVectorBaseField', 'TSVectorTsQueryLookup',
           'TSVectorSearchLookup', 'TSVectorISearchLookup',
           'DictionaryTransform')

"""
    pg_fts.fields
    -------------

    Implementation of postgres full text search

    @author: David Miguel

"""

tsvector_re = re.compile(r'[^\w &:\|\!\*\']', flags=re.U)
search_re = re.compile(r'[^\w ]', flags=re.U)


class TSVectorBaseField(Field):

    """
    Base vector field

    :param dictionary: Dictionary name as is in PostgreSQL
        ```pg_catalog.pg_ts_config``` more information in
        :pg_docs:`PostgreSQL documentation 12.6. Dictionaries
        <textsearch-dictionaries.html>`

    :raises: exceptions.FieldError if lookup isn't tsquery, search or isearch

    """
    valid_lookups = ('search', 'isearch', 'tsquery')
    empty_strings_allowed = True

    def __init__(self, dictionary='english', **kwargs):
        """Vector field"""
        kwargs['null'] = True
        kwargs['default'] = ''
        kwargs['editable'] = False
        kwargs['serialize'] = False
        kwargs['db_index'] = False  # use migrations for index creation
        self.dictionary = dictionary
        super(TSVectorBaseField, self).__init__(**kwargs)

    def db_type(self, connection):
        return 'tsvector'

    def get_db_prep_lookup(self, lookup_type, value, connection,
                           prepared=False):

        if lookup_type not in self.valid_lookups:
            raise exceptions.FieldError("'%s' isn't valid Lookup for %s" % (
                lookup_type, self.__class__.__name__))

        return [self.get_db_prep_value(
            self._get_db_prep_lookup(lookup_type, value),
            connection=connection,
            prepared=prepared)]

    @staticmethod
    def _get_db_prep_lookup(lookup_type, value):
        if lookup_type in ('search', 'isearch'):
            operation = ' & ' if lookup_type == 'search' else ' | '
            return "%s" % operation.join(search_re.sub('', value).split())
        elif lookup_type == 'tsquery':
            return "%s" % ' '.join(tsvector_re.sub('', value).split())

    def deconstruct(self):
        name, path, args, kwargs = super(TSVectorBaseField, self).deconstruct()
        path = 'pg_fts.fields.TSVectorBaseField'
        kwargs['dictionary'] = self.dictionary
        return name, path, args, kwargs


class TSVectorField(TSVectorBaseField):
    """
    :param fields: A tuple containing a tuple of fields and rank to be indexed,
        it can be only the field name the default the rank 'D' will be added

        Example::

            ('field_name', ('field_name2', 'A'))

        Will result in::

            (('field_name', 'D'), ('field_name2', 'A'))

    :param dictionary: available options:

        - Can be string with the dictionary name ```pg_catalog.pg_ts_config```
            consult :pg_docs:`PostgreSQL documentation 12.6. Dictionaries
            <textsearch-dictionaries.html>`

        - A TextField name in case of multiple dictionaries

        .. caution::

            Dictionary(ies) used must be installed in your database, check
                ``pg_catalog.pg_ts_config``

    :raises: exceptions.FieldError if lookup isn't tsquery, search or isearch
        or not a valid option dictionary (in case of multiple dictionaries)

    .. caution::

            TSVectorField does not support iexact, it will raise an exception


    """

    DEFAUL_RANK = 'D'
    RANK_LEVELS = ('A', 'B', 'C', 'D')
    default_error_messages = {
        'fields_error': _('Fields must be tuple or list of fields:'),
        'index_error': _('Invalid index:'),
    }

    def __init__(self, fields, dictionary='english', **kwargs):
        self.fields = fields
        super(TSVectorField, self).__init__(dictionary, **kwargs)

    def _get_fields_and_ranks(self):
        for field in self.fields:
            if isinstance(field, (tuple, list)):
                yield (self.model._meta.get_field_by_name(field[0])[0],
                       field[1].upper())
            else:
                yield (self.model._meta.get_field_by_name(field)[0],
                       self.DEFAUL_RANK)

    def check(self, **kwargs):
        errors = super(TSVectorField, self).check(**kwargs)
        for f in self.fields:
            field = None
            if isinstance(f, (tuple, list)):
                if len(f) > 2:
                    errors.append(
                        checks.Error(
                            'Invalid value in fields "%s"' % (str(f),),
                            hint='can be "field" or ("field", "rank")',
                            obj=self,
                            id='fts.E001'
                        )
                    )
                else:
                    field = f[0]
                    if f[1].upper() not in self.RANK_LEVELS:
                        errors.append(
                            checks.Error(
                                'Invalid rank "%s" in "%s"' % (str(f[1]), f),
                                hint=('Available ranks %s' %
                                      ' or '.join(self.RANK_LEVELS)),
                                obj=self,
                                id='fts.E001'
                            )
                        )
            else:
                field = f
            if field and not isinstance(field, six.string_types):
                errors.append(
                    checks.Error(
                        'Invalid value in fields "%s"' % (str(f),),
                        hint='can be name of field or (field, rank)',
                        obj=self,
                        id='fts.E001'
                    )
                )
            elif field:
                try:
                    t = self.model._meta.get_field_by_name(field)[0]
                    if not isinstance(t, (models.CharField, models.TextField)):
                        errors.append(
                            checks.Error(
                                'Field must be CharField or TextField.',
                                hint=None,
                                obj=self,
                                id='fts.E001'
                            )
                        )
                except models.FieldDoesNotExist:
                    errors.append(
                        checks.Error(
                            'FieldDoesNotExistFieldDoesNotExist %s' % str(f),
                            hint=None,
                            obj=self,
                            id='fts.E001'
                        )
                    )

        return errors

    @property
    def description(self):
        return 'TSVector of (%s)' % ', '.join(self.fields)

    def deconstruct(self):
        name, path, args, kwargs = super(TSVectorField, self).deconstruct()
        path = 'pg_fts.fields.TSVectorField'
        kwargs['fields'] = self.fields
        return name, path, args, kwargs

    def get_dictionary(self):
        try:
            df = self.model._meta.get_field(self.dictionary)
            return df.default if df.default else df.options[0][0]
        except models.FieldDoesNotExist:
            return self.dictionary

    def get_transform(self, name):
        transform = super(TSVectorField, self).get_transform(name)
        if transform:
            return transform
        try:
            if name in map(
                    lambda x: x[1],
                    self.model._meta.get_field(self.dictionary).choices):
                return DictionaryTransformFactory(name)
            else:
                raise exceptions.FieldError("The '%s' is not in %s choices" % (
                    name, self.model._meta.get_field(self.dictionary))
                )
        except ValueError:
            pass


class TSVectorTsQueryLookup(Lookup):
    """
    TSVectorField Lookup tsquery

    Raw to_tsquery lookup, check the documentation for more details
        :pg_docs:`12.3.2. Parsing Queries
        <textsearch-controls.html#TEXTSEARCH-PARSING-QUERIES>`

    :param query values: valid PostgreSQL tsquery

        .. caution::
            If the query is not a valid PostgreSQL to_tsquery will result in a
            syntax error

    Example::

        Article.objects.filter(
            tsvector__tsquery="'single-quoted phrases' & prefix:A*B & !not | or | weight:ABC"
        )

    SQL equivalent:

    .. code-block:: sql

        "tsvector" @@ to_tsquery('english', '''singlequoted phrases'' & prefix:A*B & !not | or | weight:ABC')

    .. note::

        The lookup will get dictionary value in
            :class:`~pg_fts.fields.TSVectorField`, this case *english*

        In case of multiple dictionaries see
            :class:`~pg_fts.fields.DictionaryTransform`

    """

    lookup_name = 'tsquery'
    lookup_sql = "%s @@ to_tsquery('%s', %s)"

    def as_sql(self, qn, connection):
        lhs, lhs_params = self.process_lhs(qn, connection)
        rhs, rhs_params = self.process_rhs(qn, connection)
        params = lhs_params + rhs_params
        if hasattr(self.lhs, 'dictionary'):
            dictionary = self.lhs.dictionary
        else:
            dictionary = self.lhs.source.get_dictionary()
        return self.lookup_sql % (lhs, dictionary, rhs), params

    @property
    def output_field(self):
        return TSVectorBaseField(self.dictionary)


TSVectorBaseField.register_lookup(TSVectorTsQueryLookup)


class TSVectorSearchLookup(TSVectorTsQueryLookup):
    """
    TSVectorField Lookup search

    An to_tsquery with AND *&* operator

    :param query values: a string with words

    Example::

        Article.objects.filter(
            tsvector__search="an and query"
        )

    SQL equivalent:::

    .. code-block:: sql

        "tsvector" @@ to_tsquery('english', 'an & and & query')

    .. note::

        The lookup will get dictionary value in
            :class:`~pg_fts.fields.TSVectorField`, this case *english*

        In case of multiple dictionaries see
            :class:`~pg_fts.fields.DictionaryTransform`

    """

    lookup_name = 'search'


TSVectorBaseField.register_lookup(TSVectorSearchLookup)


class TSVectorISearchLookup(TSVectorTsQueryLookup):
    """
    TSVectorField Lookup isearch

    An to_tsquery with OR *|* operator

    :param query values: a string with words

    Example::

        Article.objects.filter(
            tsvector__isearch="an and query"
        )

    SQL equivalent:

    .. code-block:: sql

        "tsvector" @@ to_tsquery('english', 'an | and | query')

    .. note::

        The lookup will get dictionary value in
            :class:`~pg_fts.fields.TSVectorField`, this case *english*

        In case of multiple dictionaries see
            :class:`~pg_fts.fields.DictionaryTransform`

    """

    lookup_name = 'isearch'


TSVectorBaseField.register_lookup(TSVectorISearchLookup)


class DictionaryTransform(Transform):
    """
    TSVectorField dictionary transform

    :param query values: a valid dictionary in
        :class:`~pg_fts.fields.TSVectorField` field dictionary.options

    Example::

        # in models.py

        class Article(models.Model):
            title = models.CharField(max_length=255)
            article = models.TextField()
            dictionary = models.CharField(
                max_length=15,
                choices=(
                    ('english', 'english'),
                    ('portuguese', 'portuguese')
                ),
                default='english',
                db_index=True
            )
            fts_index = TSVectorField(
                (('title', 'A'), 'article'),
                dictionary='dictionary'
            )

    >>> Article.objects.filter(
            tsvector__english__isearch="an and query"
        )
    # will create a ts_query with english dictionary
    # SQL -> to_tsquery('english', 'an | and | query')

    >>> Article.objects.filter(
            tsvector__portuguese__isearch="an and query"
        )
    # will create a ts_query with portuguese dictionary
    # SQL -> to_tsquery('portuguese', 'an | and | query')

    >>> Article.objects.filter(
            tsvector__isearch="an and query"
        )
    # will create a ts_query with english dictionary, it's the default in
    # dictionary, but if there was no default it wold get the 1st option in
    # options
    # SQL -> to_tsquery('english', 'an | and | query')
    # but if dictionary is not in options will raise FieldError
    >>> Article.objects.filter(
            tsvector__japonese__isearch="an and query"  # will raise an error
        )
    FieldError: The 'japonese' is not in article.Article.dictionary choices


    """

    def __init__(self, dictionary, *args,
                 **kwargs):
        super(DictionaryTransform, self).__init__(*args, **kwargs)
        self.dictionary = dictionary

    def as_sql(self, qn, connection):
        lhs, params = qn.compile(self.lhs)
        return "%s" % lhs, params

    @property
    def output_field(self):
        return TSVectorBaseField(self.dictionary)


class DictionaryTransformFactory(object):

    def __init__(self, dictionary):
        self.dictionary = dictionary

    def __call__(self, *args, **kwargs):
        return DictionaryTransform(self.dictionary, *args, **kwargs)
