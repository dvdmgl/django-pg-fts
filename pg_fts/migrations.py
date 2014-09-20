from django.db.migrations.operations.base import Operation
from django.db.models.loading import get_model
from pg_fts.fields import TSVectorField


__all__ = ('CreateFTSIndexOperation', 'CreateFTSTriggerOperation')


class CreateFTSTriggerOperation(Operation):
    sql_delete_trigger = ("DROP TRIGGER {model}_{fts_name}_update ON {model};"
                          "DROP FUNCTION {model}_{fts_name}_update()")
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
FOR EACH ROW EXECUTE PROCEDURE {model}_{fts_name}_update()"""
    reduces_to_sql = True
    reversible = True

    def __init__(self, name, fts_vector):
        self.name = name
        self.fts_vector = fts_vector

    def state_forwards(self, app_label, state):
        pass

    def database_forwards(self, app_label, schema_editor, from_state,
                          to_state):

        model = from_state.render().get_model(app_label, self.name)
        vector_field = model._meta.get_field_by_name(self.fts_vector)[0]
        trigger = self._create_fts_trigger_sql(
            model=model,
            vector_field=vector_field
        )

        if trigger:
            schema_editor.execute(trigger)

    def database_backwards(self, app_label, schema_editor, from_state,
                           to_state):

        model = from_state.render().get_model(app_label, self.name)
        vector_field = model._meta.get_field_by_name(self.fts_vector)[0]

        triggers = self.sql_delete_trigger.format(
            model=model._meta.db_table,
            fts_name=vector_field.get_attname_column()[1]
        )

        if triggers:
            schema_editor.execute(triggers)

    def describe(self):
        return "Create trigger `%s` for model `%s`" % (
            self.fts_vector, self.name
        )

    def _create_fts_trigger_sql(self, model, vector_field):
        fields = []
        vectors = []

        if not isinstance(vector_field, TSVectorField):
            raise AttributeError

        try:
            dict_field = model._meta.get_field_by_name(vector_field.dictionary)[0]
            dictionary = "NEW.%s::regconfig" % (
                dict_field.get_attname_column()[1])
            fields.append('NEW.{0} <> OLD.{0}'.format(vector_field.dictionary))
        except:
            dictionary = "'%s'" % vector_field.dictionary

        for field, rank in vector_field._get_fields_and_ranks():
            fields.append('NEW.{0} <> OLD.{0}'.format(
                field.get_attname_column()[1]))
            vectors.append(self._get_vector_for_field(field, rank, dictionary))

        return self.sql_create_trigger.format(
            model=model._meta.db_table,
            fts_name=vector_field.get_attname_column()[1],
            fts_fields=' OR '.join(fields),
            vectors=' || '.join(vectors)
        )

    def _get_vector_for_field(self, field, weight, dictionary):
        return "setweight(to_tsvector(%s, COALESCE(NEW.%s, '')), '%s')" % (
            dictionary, field.get_attname_column()[1], weight
        )


class CreateFTSIndexOperation(Operation):
    # http://www.postgresql.org/docs/9.3/static/textsearch-indexes.html
    sql_create_index = ("CREATE INDEX {model}_{fts_name} ON {model} "
                        "USING {fts_index}({fts_name})")

    sql_delete_index = 'DROP INDEX {model}_{fts_name}'
    INDEXS = ('gin', 'gist')
    reduces_to_sql = True

    reversible = True

    def __init__(self, name, fts_vector, index):
        assert index in self.INDEXS, "Invalid index '%s'. Options %s " % (
            index, ', '.join(self.INDEXS))
        self.name = name
        self.fts_vector = fts_vector
        self.index = index

    def state_forwards(self, app_label, state):
        pass

    def database_forwards(self, app_label, schema_editor, from_state,
                          to_state):

        model = from_state.render().get_model(app_label, self.name)
        vector_field = model._meta.get_field_by_name(self.fts_vector)[0]
        if not isinstance(vector_field, TSVectorField):
            raise AttributeError
        schema_editor.execute(self._create_index_sql(model, vector_field))

    def database_backwards(self, app_label, schema_editor, from_state,
                           to_state):

        model = from_state.render().get_model(app_label, self.name)
        vector_field = model._meta.get_field_by_name(self.fts_vector)[0]

        indexs = self.sql_delete_index.format(
            model=model._meta.db_table,
            fts_name=vector_field.get_attname_column()[1]
        )

        if indexs:
            schema_editor.execute(indexs)

    def describe(self):
        return "Create index `%s` for model `%s`" % (
            self.fts_vector, self.name
        )

    def _create_index_sql(self, model, fts_vector):
        return self.sql_create_index.format(
            model=model._meta.db_table,
            fts_index=self.index,
            fts_name=fts_vector.get_attname_column()[1]
        )
