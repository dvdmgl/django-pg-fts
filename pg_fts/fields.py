from __future__ import unicode_literals
from django.db.models import Field, Lookup, Transform
from django.db.models.lookups import RegisterLookupMixin
from django.utils import six
from django.core import checks, exceptions
from django.utils.translation import string_concat, ugettext_lazy as _
from django.db import models
from django.db.models.aggregates import Aggregate
import re

__all__ = ('TSVectorField', 'TSVectorBaseField', 'TSRank')


class TSVectorBaseField(Field):
    empty_strings_allowed = True

    def __init__(self, dictionary='english', **kwargs):
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


class TSVectorTsQueryLookup(Lookup):
    lookup_name = 'tsquery'

    def as_sql(self, qn, connection):
        lhs, lhs_params = self.process_lhs(qn, connection)
        rhs, rhs_params = self.process_rhs(qn, connection)
        params = lhs_params + rhs_params
        dictionary = self.lhs.dictionary if hasattr(self.lhs, 'dictionary') else self.lhs.source.dictionary

        return "%s @@ to_tsquery('%s', %s)" % (
            lhs, dictionary, rhs), params


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
        return "%s" % lhs, params

    @property
    def output_field(self):
        return TSVectorBaseField(self.dictionary)


class DictionaryTransformFactory(object):

    def __init__(self, dictionary):
        self.dictionary = dictionary

    def __call__(self, *args, **kwargs):
        return DictionaryTransform(self.dictionary, *args, **kwargs)
