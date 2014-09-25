from __future__ import unicode_literals
from django.db.models import Field, Lookup, Transform
from django.db.models.lookups import RegisterLookupMixin
from django.utils import six
from django.core import checks, exceptions
from django.utils.translation import string_concat, ugettext_lazy as _
from django.db import models
import re

__all__ = ('TSVectorField', 'TSVectorBaseField', 'TSVectorTsQueryLookup',
           'TSVectorSearchLookup', 'TSVectorISearchLookup')

"""
    pg_fts.fields
    -------------

    Implementation of postgres full text search

    @author: David Miguel

"""


class TSVectorBaseField(Field):

    """
    Base vector field

    :param dictionary: Dictionary name as is in PostgreSQL
        ```pg_catalog.pg_ts_config``` more information in
        :pg_docs:`PostgreSQL documentation 12.6. Dictionaries
        <textsearch-dictionaries.html>`

    """

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
        if lookup_type == 'exact':
            lookup_type = 'search'
        if lookup_type in ('search', 'isearch'):
            values = re.sub(r'[^\w ]', '', value, flags=re.U).split(' ')
            operation = ' & ' if lookup_type == 'search' else ' | '
            return [self.get_db_prep_value(
                "%s" % operation.join(v for v in values if v),
                connection=connection,
                prepared=prepared)]

        elif lookup_type == 'tsquery':
            value = re.sub(r'[^\w &\|]', '', value)
            return [self.get_db_prep_value(value, connection=connection,
                                           prepared=prepared)]

        raise exceptions.FieldError("'%s' isn't valid Lookup for %s" % (
            lookup_type, self.__class__.__name__)
        )

    def deconstruct(self):
        name, path, args, kwargs = super(TSVectorBaseField, self).deconstruct()
        path = 'pg_fts.fields.TSVectorBaseField'
        kwargs['dictionary'] = self.dictionary
        return name, path, args, kwargs


class TSVectorField(TSVectorBaseField):
    """
    :param fields: A tuple containing a tuple of fields and rank to be indexed,
        it can be only the field name the default the rank 'D' will be added

        Example:
            ```('field_name', ('field_name2', 'A'))```

        Will result in:
            ```(('field_name', 'D'), ('field_name2', 'A'))```

    :param dictionary: available options:

        - Can be string with the dictionary name ```pg_catalog.pg_ts_config```
            consult :pg_docs:`PostgreSQL documentation 12.6. Dictionaries
            <textsearch-dictionaries.html>`

        - A TextField name in case of multiple dictionaries

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
            return self.model._meta.get_field(self.dictionary).default
        except models.FieldDoesNotExist:
            return self.dictionary

    def get_transform(self, name):
        transform = super(TSVectorField, self).get_transform(name)
        if transform:
            return transform
        try:
            if name in map(lambda x: x[1],
                           self.model._meta.get_field(self.dictionary).choices):
                return DictionaryTransformFactory(name)
            else:
                raise exceptions.FieldError("The '%s' is not in %s choices" % (
                    name, self.model._meta.get_field(self.dictionary))
                )
        except ValueError:
            pass


class TSVectorQuerySQL(object):

    @staticmethod
    def _as_sql(lhs, rhs, dictionary):
        return "%s @@ to_tsquery('%s', %s)" % (lhs, dictionary, rhs)


class BaseAggregate(TSVectorQuerySQL):
    sql_function = ''
    name = ''

    def __init__(self, lookup, **extra):
        self.lookup = lookup
        self.extra = extra

    def _default_alias(self):
        return '%s__%s' % (self.lookup, self.name.lower())
    default_alias = property(_default_alias)

    def add_to_query(self, query, alias, col, source, is_summary=False):

        query.aggregates[alias] = aggregate


class TSVectorTsQueryLookup(TSVectorQuerySQL, Lookup):
    lookup_name = 'tsquery'

    def as_sql(self, qn, connection):
        lhs, lhs_params = self.process_lhs(qn, connection)
        rhs, rhs_params = self.process_rhs(qn, connection)
        params = lhs_params + rhs_params
        dictionary = self.lhs.dictionary if hasattr(self.lhs, 'dictionary') else self.lhs.source.dictionary
        return "%s @@ to_tsquery('%s', %s)" % (lhs, dictionary, rhs), params

    @property
    def output_field(self):
        return TSVectorBaseField(self.dictionary)


TSVectorBaseField.register_lookup(TSVectorTsQueryLookup)


class TSVectorSearchLookup(TSVectorTsQueryLookup):
    lookup_name = 'search'


TSVectorBaseField.register_lookup(TSVectorSearchLookup)


class TSVectorISearchLookup(TSVectorTsQueryLookup):
    lookup_name = 'isearch'


TSVectorBaseField.register_lookup(TSVectorISearchLookup)


class DictionaryTransform(Transform):

    def __init__(self, dictionary, *args,
                 **kwargs):
        super(DictionaryTransform, self).__init__(*args, **kwargs)
        self.dictionary = dictionary

    def as_sql(self, qn, connection):
        lhs, params = qn.compile(self.lhs)
        print('AS_SQL', lhs, params)
        return "%s" % lhs, params

    @property
    def output_field(self):
        return TSVectorBaseField(self.dictionary)


class DictionaryTransformFactory(object):

    def __init__(self, dictionary):
        self.dictionary = dictionary

    def __call__(self, *args, **kwargs):
        return DictionaryTransform(self.dictionary, *args, **kwargs)
