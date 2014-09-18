from django.test import TestCase, TransactionTestCase
from pg_fts.fields import TSVectorField
from pg_fts.introspection import PgFTSIntrospection
from pg_fts.migrations import CreateFTSIndexOperation
from django.db.migrations.state import ProjectState
from django.db import connection, models

__all__ = ('FTSTestBase', 'CreateFTSIndexOperationTest',
           'CreateFTSIndexOperationSQL', 'CreateFTSMultiIndexOperationSQL')


class FTSTestBase(TransactionTestCase):
    '''tests for FTS'''

    introspection = PgFTSIntrospection()

    def assertTriggerExists(self, trigger):
        with connection.cursor() as cursor:
            self.assertIn(trigger, self.introspection.get_trigger_list(cursor))

    def assertTriggerNotExists(self, trigger):
        with connection.cursor() as cursor:
            self.assertNotIn(trigger,
                             self.introspection.get_trigger_list(cursor))

    def assertFunctionExists(self, function):
        with connection.cursor() as cursor:
            self.assertIn(function,
                          self.introspection.get_functions_list(cursor))

    def assertFunctionNotExists(self, function):
        with connection.cursor() as cursor:
            self.assertNotIn(function,
                             self.introspection.get_functions_list(cursor))


class CreateFTSIndexOperationTest(FTSTestBase):

    def test_create_model(self):
        from testapp.models import TSVectorModel
        create_tg = CreateFTSIndexOperation(
            model=TSVectorModel,
            fts_vectors=[
                ('tsvector', TSVectorField(
                    editable=False, dictionary='english',
                    fts_index='gin', db_column='wtf',
                    fields=('title', 'body'), serialize=False,
                    db_index=True, null=True, default='')),
            ]
        )
        self.assertEqual(create_tg.describe(),
                         'Create trigger `tsvector` for model `TSVectorModel`')

        project_state = ProjectState()
        new_state = project_state.clone()

        self.assertFunctionNotExists('testapp_tsvectormodel_wtf_update')
        self.assertTriggerNotExists('testapp_tsvectormodel_wtf_update')

        with connection.schema_editor() as editor:
            create_tg.database_forwards("TSVectorModel", editor, project_state,
                                        new_state)

        self.assertFunctionExists('testapp_tsvectormodel_wtf_update')
        self.assertTriggerExists('testapp_tsvectormodel_wtf_update')

        with connection.schema_editor() as editor:
            create_tg.database_backwards("TSVectorModel", editor,
                                         project_state, new_state)

        self.assertFunctionNotExists('testapp_tsvectormodel_wtf_update')
        self.assertTriggerNotExists('testapp_tsvectormodel_wtf_update')


class CreateFTSIndexOperationSQL(TestCase):
    '''tests for TriggerSql'''
    def test_trigger_sql(self):
        self.assertEqual.__self__.maxDiff = None

        class TSTrigger(models.Model):
            title = models.CharField(max_length=50)

            tsvector = TSVectorField(
                (('title', 'A'),), fts_index='gin')

        class TSTrigger3(models.Model):
            title = models.CharField(max_length=50)

            tsvector = TSVectorField(
                (('title', 'A'),), db_column='xx')

        # ts_field = TSTrigger._meta.get_field('tsvector')

        migration = CreateFTSIndexOperation(
            model=TSTrigger,
            fts_vectors=[
                ('tsvector', TSVectorField(default='', null=True,
                                           dictionary='english',
                                           editable=False,
                                           fields=(('title', 'A'), ),
                                           fts_index='gin', serialize=False)),
            ]
        )
        self.assertEqual(migration._create_index_sql(),
                         "CREATE INDEX pg_fts_tstrigger_tsvector ON pg_fts_tstrigger"
                         " USING gin(tsvector);")
        self.assertEqual(migration._delete_index_sql(),
                         'DROP INDEX pg_fts_tstrigger_tsvector;')
        self.assertEqual(migration._delete_trigger_sql(),
                         ("DROP TRIGGER pg_fts_tstrigger_tsvector_update ON pg_fts_tstrigger;"
                          "DROP FUNCTION pg_fts_tstrigger_tsvector_update();"))
        self.assertEqual(
            migration._create_fts_triggers_sql(),
            """
CREATE FUNCTION pg_fts_tstrigger_tsvector_update() RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        new.tsvector = setweight(to_tsvector('english', COALESCE(NEW.title, '')), 'A');
    END IF;
    IF TG_OP = 'UPDATE' THEN
        IF NEW.title <> OLD.title THEN
            new.tsvector = setweight(to_tsvector('english', COALESCE(NEW.title, '')), 'A');
        END IF;
    END IF;
RETURN NEW;
END;
$$ LANGUAGE 'plpgsql';
CREATE TRIGGER pg_fts_tstrigger_tsvector_update BEFORE INSERT OR UPDATE ON pg_fts_tstrigger
FOR EACH ROW EXECUTE PROCEDURE pg_fts_tstrigger_tsvector_update();"""
        )

        migration2 = CreateFTSIndexOperation(
            model=TSTrigger,
            fts_vectors=[
                ('tsvector', TSVectorField(default='', null=True,
                                           dictionary='english', db_index=True,
                                           editable=False,
                                           fields=(('title', 'A'), ),
                                           fts_index=None, serialize=False,
                                           db_column='xx')),
            ]
        )
        self.assertEqual(migration2._create_index_sql(), '')
        self.assertEqual(migration2._delete_index_sql(), '')
        self.assertEqual(migration2._delete_trigger_sql(),
                         ("DROP TRIGGER pg_fts_tstrigger_xx_update ON pg_fts_tstrigger;"
                          "DROP FUNCTION pg_fts_tstrigger_xx_update();"))
        with self.assertRaises(AssertionError) as ex:
            migration2._create_fts_triggers_sql()
        self.assertEqual(str(ex.exception), 'Field tsvector `fts_index` not equal in model `gin` and migration `None`')

        migration3 = CreateFTSIndexOperation(
            model=TSTrigger3,
            fts_vectors=[
                ('tsvector', TSVectorField(default='', null=True,
                                           dictionary='english', db_index=True,
                                           editable=False,
                                           fields=(('title', 'A'), ),
                                           fts_index='gin', serialize=False,
                                           db_column='xx')),
            ]
        )

        self.assertEqual(
            migration3._create_fts_triggers_sql(),
            """
CREATE FUNCTION pg_fts_tstrigger3_xx_update() RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        new.xx = setweight(to_tsvector('english', COALESCE(NEW.title, '')), 'A');
    END IF;
    IF TG_OP = 'UPDATE' THEN
        IF NEW.title <> OLD.title THEN
            new.xx = setweight(to_tsvector('english', COALESCE(NEW.title, '')), 'A');
        END IF;
    END IF;
RETURN NEW;
END;
$$ LANGUAGE 'plpgsql';
CREATE TRIGGER pg_fts_tstrigger3_xx_update BEFORE INSERT OR UPDATE ON pg_fts_tstrigger3
FOR EACH ROW EXECUTE PROCEDURE pg_fts_tstrigger3_xx_update();"""
        )


class CreateFTSMultiIndexOperationSQL(TestCase):
    '''tests for TriggerSql'''
    def test_trigger_multi_sql(self):
        self.assertEqual.__self__.maxDiff = None

        class TSMultiTrigger(models.Model):
            title = models.CharField(max_length=50)
            dictionary = models.CharField(
                max_length=15,
                choices=(('english', 'english'), ('portuguese', 'portuguese')),
                default='english'
            )
            tsvector = TSVectorField((('title', 'A'),), fts_index='gin',
                                     dictionary='dictionary')

        migration = CreateFTSIndexOperation(
            model=TSMultiTrigger,
            fts_vectors=[
                ('tsvector', TSVectorField(default='', null=True,
                                           dictionary='dictionary',
                                           editable=False,
                                           fields=(('title', 'A'), ),
                                           fts_index='gin', serialize=False)),
            ]
        )
        self.assertEqual(migration._create_index_sql(),
                         "CREATE INDEX pg_fts_tsmultitrigger_tsvector ON pg_fts_tsmultitrigger"
                         " USING gin(tsvector);")
        self.assertEqual(migration._delete_index_sql(),
                         'DROP INDEX pg_fts_tsmultitrigger_tsvector;')
        self.assertEqual(migration._delete_trigger_sql(),
                         ("DROP TRIGGER pg_fts_tsmultitrigger_tsvector_update ON pg_fts_tsmultitrigger;"
                          "DROP FUNCTION pg_fts_tsmultitrigger_tsvector_update();"))
        self.assertEqual(
            migration._create_fts_triggers_sql(),
            """
CREATE FUNCTION pg_fts_tsmultitrigger_tsvector_update() RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        new.tsvector = setweight(to_tsvector(NEW.dictionary::regconfig, COALESCE(NEW.title, '')), 'A');
    END IF;
    IF TG_OP = 'UPDATE' THEN
        IF NEW.title <> OLD.title THEN
            new.tsvector = setweight(to_tsvector(NEW.dictionary::regconfig, COALESCE(NEW.title, '')), 'A');
        END IF;
    END IF;
RETURN NEW;
END;
$$ LANGUAGE 'plpgsql';
CREATE TRIGGER pg_fts_tsmultitrigger_tsvector_update BEFORE INSERT OR UPDATE ON pg_fts_tsmultitrigger
FOR EACH ROW EXECUTE PROCEDURE pg_fts_tsmultitrigger_tsvector_update();"""
        )
