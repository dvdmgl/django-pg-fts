from django.db.migrations.operations.base import Operation
from django.db.models.loading import get_model
from pg_fts.fields import TSVectorField


__all__ = ('CreateFTSIndexOperation',)


class CreateFTSIndexOperation(Operation):
    # http://www.postgresql.org/docs/9.3/static/textsearch-indexes.html
    sql_create_index = ("CREATE INDEX {model}_{fts_name} ON {model} "
                        "USING {fts_index}({fts_name});")

    sql_delete_index = 'DROP INDEX {model}_{fts_name};'

    sql_delete_trigger = ("DROP TRIGGER {model}_{fts_name}_update ON {model};"
                          "DROP FUNCTION {model}_{fts_name}_update();")

    sql_create_trigger = """
CREATE FUNCTION {model}_{fts_name}_update() RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        new.{fts_name} = {vectors};
    END IF;
    IF TG_OP = 'UPDATE' THEN
        IF {fts_fields} THEN
            new.{fts_name} = {vectors};
        END IF;
    END IF;
RETURN NEW;
END;
$$ LANGUAGE 'plpgsql';
CREATE TRIGGER {model}_{fts_name}_update BEFORE INSERT OR UPDATE ON {model}
FOR EACH ROW EXECUTE PROCEDURE {model}_{fts_name}_update();"""

    # If this is False, it means that this operation will be ignored by
    # sqlmigrate; if true, it will be run and the SQL collected for its output.
    reduces_to_sql = False

    # If this is False, Django will refuse to reverse past this operation.
    reversible = True
    triggers = []
    indexs = []

    def __init__(self, model, fts_vectors):
        self.model = model
        self.fts_vectors = fts_vectors

    def state_forwards(self, app_label, state):
        # The Operation should take the 'state' parameter (an instance of
        # django.db.migrations.state.ProjectState) and mutate it to match
        # any schema changes that have occurred.
        pass

    def database_forwards(self, app_label, schema_editor, from_state,
                          to_state):

        indexs = self._create_index_sql()
        triggers = self._create_fts_triggers_sql()
        if indexs:
            schema_editor.execute(indexs)

        if triggers:
            schema_editor.execute(triggers)
        # The Operation should use schema_editor to apply any changes it
        # wants to make to the database.

    def database_backwards(self, app_label, schema_editor, from_state,
                           to_state):

        indexs = self._delete_index_sql()
        triggers = self._delete_trigger_sql()

        if indexs:
            schema_editor.execute(indexs)

        if triggers:
            schema_editor.execute(triggers)

        # If reversible is True, this is called when the operation is reversed.

    def describe(self):
        # This is used to describe what the operation does in console output.
        return "Create trigger `%s` for model `%s`" % (
            ','.join(v[0] for v in self.fts_vectors), self.model.__name__,
            )

    def _create_fts_triggers_sql(self):
        out = []
        err = 'Field %s `%s` not equal in model `%s` and migration `%s`'
        for field_name, field in self.fts_vectors:
            model_field = self.model._meta.get_field_by_name(field_name)[0]
            assert model_field.fields == field.fields, err % (
                field_name, 'fields', model_field.fields, field.fields)
            assert model_field.dictionary == field.dictionary, err % (
                field_name, 'dictionary', model_field.dictionary,
                field.dictionary)
            assert model_field.fts_index == field.fts_index, err % (
                field_name, 'fts_index', model_field.fts_index,
                field.fts_index)
            assert model_field.get_attname_column()[1] == (field.db_column or
                                                           field_name), err % (
                field_name, 'db_column',
                model_field.model_field.get_attname_column()[1],
                field.db_column or field_name)

            out.append(self._create_fts_trigger_sql(model_field))

        return '\n'.join(out)

    def _create_fts_trigger_sql(self, vector):
        fields = []
        vectors = []
        dictionary = self._get_language_for_vector(vector.dictionary)
        for field, rank in vector._get_fields_and_ranks():
            fields.append('NEW.{0} <> OLD.{0}'.format(
                field.get_attname_column()[1]))
            vectors.append(self._get_vector_for_field(field, rank, dictionary))

        return self.sql_create_trigger.format(
            model=self.model._meta.db_table,
            fts_name=vector.get_attname_column()[1],
            fts_fields=' OR '.join(fields), vectors=' || '.join(vectors))

    def _get_vector_for_field(self, field, weight, dictionary):
        return "setweight(to_tsvector(%s, COALESCE(NEW.%s, '')), '%s')" % (
            dictionary, field.get_attname_column()[1], weight
        )

    def _get_language_for_vector(self, dictionary):
        try:
            dict_field = self.model._meta.get_field_by_name(dictionary)[0]
            return "NEW.%s::regconfig" % (dict_field.get_attname_column()[1])
        except:
            return "'%s'" % dictionary

    def _validate_fts_vectors(self):
        self.fields = (f for f in self.model._meta.get_all_field_names()
                       if isinstance(f, TSVectorField))

    def _create_index_sql(self):
        idxs = []
        for f, v in self.fts_vectors:
            if v.fts_index:
                idxs.append(self.sql_create_index.format(
                    model=self.model._meta.db_table,
                    fts_index=v.fts_index,
                    fts_name=v.get_attname_column()[1] or f
                ))
        return '\n'.join(idxs)

    def _delete_index_sql(self):
        return '\n'.join(self._get_name_fn(self.sql_delete_index))

    def _delete_trigger_sql(self):
        return '\n'.join(self._get_name_fn(self.sql_delete_trigger, True))

    def _get_name_fn(self, sql_str, trigger=False):
        return [sql_str.format(model=self.model._meta.db_table,
                               fts_name=v.get_attname_column()[1] or f)
                for f, v in self.fts_vectors if trigger or v.fts_index]


