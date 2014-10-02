"""
Classes to represent the default SQL aggregate functions
"""
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db.models.fields import FloatField
from django.db.models.constants import LOOKUP_SEP
from django.db.models.sql import aggregates
from django.core import exceptions
from pg_fts.fields import TSVectorBaseField

__all__ = ('FTSRankCd', 'FTSRank', 'FTSRankDictionay', 'FTSRankCdDictionary')


class AggregateRegister(aggregates.Aggregate):
    """
    Fake aggregate to add rank to querysets
    """
    is_ordinal = False
    is_computed = True
    sql_template = ("%(function)s(%(weights)s%(field_name)s, to_tsquery('%(dictionary)s',"
                    " %(place)s)%(normalization)s)")

    def __init__(self, col, source=None, sql_function=None, **extra):
        self.col, self.source, self.sql_function = col, source, sql_function
        self.extra, self.field = extra, FloatField()
        self.params = self.extra['params']
        self.normalization = self.extra['_normalization']
        self.weights = self.extra['_weights']

    def as_sql(self, qn, connection):
        field_name = '.'.join(qn(c) for c in self.col)
        if self.normalization:
            normalization_params = ', ' + '|'.join(
                '%d' % i for i in self.normalization)
        else:
            normalization_params = ''

        if self.weights:
            weights_params = "'{" + ', '.join(
                '%.1f' % i for i in self.weights) + "}', "
        else:
            weights_params = ''

        substitutions = {
            'field_name': '.'.join(qn(c) for c in self.col),
            'function': self.sql_function,
            'place': '%s',
            'normalization': normalization_params,
            'weights': weights_params
        }
        substitutions.update(self.extra)
        return self.sql_template % substitutions, [self.params]


class RankBase(object):
    NORMALIZATION = (0, 1, 2, 4, 8, 16, 32)
    sql_function, rhs, dictionary, srt_lookup = '', '', '', ''

    def __init__(self, lookup, **extra):
        self.lookup, self.extra = lookup, extra

    def _default_alias(self):
        return '%s__%s' % (self.lookup, self.name.lower())
    default_alias = property(_default_alias)

    def add_to_query(self, query, alias, col, source, is_summary=False):
        if self.dictionary:
            # test for if is a valid transform, if not will raise error
            source.get_transform(self.dictionary)
        else:
            self.dictionary = source.dictionary

        lookup = source.get_lookup(self.srt_lookup)
        fts_query = lookup.lookup_sql % (
            '.'.join('"%s"' % c for c in col), self.dictionary, '%s')
        params = source._get_db_prep_lookup(self.srt_lookup, self.rhs)

        self.extra = {
            'params': params,
            'dictionary': self.dictionary,
            '_normalization': self.normalization,
            '_weights': self.weights
        }

        query.add_extra(
            select=None,
            select_params=None,
            where=[fts_query % ("%s")],
            params=[params],
            tables=None,
            order_by=None
        )

        aggregate = AggregateRegister(
            col,
            source=source,
            sql_function=self.sql_function,
            **self.extra)
        query.aggregates[alias] = aggregate
        # in case of related
        if col not in query.group_by:
            query.group_by.append(col)

    def _do_checks(self):
        assert not self.weights or (len(self.weights) is 4 and all(map(
            lambda x: isinstance(x, (int, float)),
            self.weights
        ))), 'weights must be of length 4 and type float or integer'

        assert not self.normalization or all(map(
            lambda x: (isinstance(x, int) and x in self.NORMALIZATION),
            self.normalization
        )), 'normalization must be in (%s)' % (
            ', '.join('%d' % i for i in self.NORMALIZATION))
        assert len(self.extra) == 1, 'to many arguments for %s' % (
            self.__class__.__name__)
        if self.srt_lookup not in TSVectorBaseField.valid_lookups:
            raise exceptions.FieldError(
                "The '%s' isn't valid Lookup for %s" % (
                    self.srt_lookup, self.__class__.__name__))


class FTSRank(RankBase):
    """
    Interface for PostgreSQL ts_rank

    Provides a interface for
        :pg_docs:`12.3.3. Ranking Search Results *ts_rank*
        <textsearch-controls.html#TEXTSEARCH-RANKING>`

    Example::

        Article.objects.annotate(rank=FTSRank(fts_index__search='Hello world',
                                 normalization=[1,2]))

    SQL equivalent:

    .. code-block:: sql

        SELECT
            ...,
            ts_rank("article"."fts_index" @@ to_tsquery('english', 'Hello & world'), 1|2) AS "rank"
        WHERE
            "article"."fts_index" @@ to_tsquery('english', 'Hello & world')

    :param fieldlookup: required

    :param normalization: iterable integer

    :param weights: iterable float

    :returns: rank

    :raises: exceptions.FieldError if lookup isn't valid

    """

    name = 'FTSRank'
    sql_function = 'ts_rank'
    dictionary = ''

    def __init__(self, **extra):
        self.normalization = extra.pop('normalization', [])
        self.weights = extra.pop('weights', [])
        params = tuple(extra.items())[0]
        self.extra = extra
        lookups, self.rhs = params[0].split(LOOKUP_SEP), params[1]
        self.srt_lookup = lookups[-1]
        self.lookup = LOOKUP_SEP.join(lookups[:-1])
        self._do_checks()


class FTSRankCd(FTSRank):
    """
    Interface for PostgreSQL ts_rank_cd

    Provides a interface for
        :pg_docs:`12.3.3. Ranking Search Results *ts_rank_cd*
        <textsearch-controls.html#TEXTSEARCH-RANKING>`


    :param fieldlookup: required


    :param normalization: list or tuple of integers PostgreSQL normalization
        values

    :returns: rank_cd

    :raises: exceptions.FieldError if lookup isn't valid

    Example::

        Article.objects.annotate(
            rank=FTSRank(fts_index__search='Hello world',
                         normalization=[1,2]))

    SQL equivalent:

    .. code-block:: sql

        SELECT
            ...,
            ts_rank_cd("article"."fts_index" @@ to_tsquery('english', 'Hello & world'), 1|2) AS "rank"
        WHERE
            "article"."fts_index" @@ to_tsquery('english', 'Hello & world')
    """

    sql_function = 'ts_rank_cd'
    name = 'FTSRankCd'


class FTSRankDictionay(FTSRank):
    """
    Interface for PostgreSQL ts_rank with **language lookup**

    Provides a interface for
        :pg_docs:`12.3.3. Ranking Search Results *rank*
        <textsearch-controls.html#TEXTSEARCH-RANKING>`

    :param fieldlookup: required

    :param normalization: list or tuple of integers PostgreSQL normalization
        values

    :returns: rank

    :raises: exceptions.FieldError if lookup isn't valid

    Example::

        Article.objects.annotate(
            rank=FTSRankDictionay(fts_index__portuguese__search='Hello world',
                                  normalization=[1,2]))

    SQL equivalent:

    .. code-block:: sql

        SELECT
            ...,
            ts_rank("article"."fts_index" @@ to_tsquery('portuguese', 'Hello & world'), 1|2) AS "rank"
        WHERE
            "article"."fts_index" @@ to_tsquery('portuguese', 'Hello & world')

    """

    def __init__(self, **extra):
        self.normalization = extra.pop('normalization', [])
        self.weights = extra.pop('weights', [])
        params = tuple(extra.items())[0]
        self.extra, self.rhs = extra, params[1]
        lookups = params[0].split(LOOKUP_SEP)
        self.dictionary, self.srt_lookup = lookups[-2:]
        self.lookup = LOOKUP_SEP.join(lookups[:-2])
        self._do_checks()


class FTSRankCdDictionary(FTSRankDictionay):
    """
    Interface for PostgreSQL ts_rank_cd with **language lookup**

    Provides a interface for
        :pg_docs:`12.3.3. Ranking Search Results *rank_cd*
        <textsearch-controls.html#TEXTSEARCH-RANKING>` with **language lookup**

    :param fieldlookup: required

    :param normalization: list or tuple of integers PostgreSQL normalization
        values

    :returns: rank_cd

    :raises: exceptions.FieldError if lookup isn't valid

    Example::

        Article.objects.annotate(
            rank=FTSRankCdDictionary(fts_index__portuguese__search='Hello world',
                                     normalization=[1,2]))

    SQL equivalent:

    .. code-block:: sql

        SELECT
            ...,
            ts_rank("article"."fts_index" @@ to_tsquery('portuguese', 'Hello & world'), 1|2) AS "rank"
        WHERE
            "article"."fts_index" @@ to_tsquery('portuguese', 'Hello & world')

    """

    sql_function = 'ts_rank_cd'
    name = 'FTSRankCdDictionary'
