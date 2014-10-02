# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import connection
from pg_fts.introspection import PgFTSIntrospection
from django.test import (override_settings, override_system_checks,
                         TestCase, TransactionTestCase)
from django.utils import six
from django.core.management import call_command

try:
    from django.db.backends import TableInfo
    table_info = True
except:
    table_info = False

__all__ = ('FTSTestBase', 'CreateOperationTestSQL',
           'TransactionsMigrationsTest')


class FTSTestBase(TransactionTestCase):
    '''tests for FTS'''

    introspection = PgFTSIntrospection()

    def assertIndexExists(self, index, table):
        with connection.cursor() as cursor:
            self.assertIn(
                index, connection.introspection.get_indexes(cursor, table))

    def assertIndexNotExists(self, index, table):
        with connection.cursor() as cursor:
            self.assertNotIn(
                index, connection.introspection.get_indexes(cursor, table))

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

    def assertTableExists(self, table):
        if table_info:
            table = TableInfo(name=table, type='t')
        with connection.cursor() as cursor:
            self.assertIn(table,
                          connection.introspection.get_table_list(cursor))

    def assertTableNotExists(self, table):
        if table_info:
            table = TableInfo(name=table, type='t')

        with connection.cursor() as cursor:
            self.assertNotIn(table,
                             connection.introspection.get_table_list(cursor))


class CreateOperationTestSQL(TestCase):
    # single dictionary
    @override_system_checks([])
    @override_settings(MIGRATION_MODULES={"testapp": "testapp.migrations_index"})
    def test_sql_migrate_creates_vector_field(self):
        stdout = six.StringIO()
        call_command('sqlmigrate', 'testapp', '0002', stdout=stdout)
        self.assertIn('"tsvector" tsvector null', stdout.getvalue().lower())
        self.assertIn(
            "UPDATE testapp_tsvectormodel SET tsvector = setweight(to_tsvector('english', COALESCE(title, '')), 'D') || setweight(to_tsvector('english', COALESCE(body, '')), 'D');",
            stdout.getvalue())

    @override_system_checks([])
    @override_settings(MIGRATION_MODULES={"testapp": "testapp.migrations_index"})
    def test_sql_fts_index(self):
        stdout = six.StringIO()
        call_command('sqlmigrate', 'testapp', '0003', stdout=stdout)
        self.assertIn(
            ('CREATE INDEX testapp_tsvectormodel_tsvector ON '
             'testapp_tsvectormodel USING gin(tsvector);'),
            stdout.getvalue())

    @override_system_checks([])
    @override_settings(MIGRATION_MODULES={"testapp": "testapp.migrations_index"})
    def test_sql_fts_trigger(self):
        stdout = six.StringIO()
        call_command('sqlmigrate', 'testapp', '0004', stdout=stdout)
        self.assertIn(
            """
CREATE FUNCTION testapp_tsvectormodel_tsvector_update() RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        new.tsvector = setweight(to_tsvector('english', COALESCE(NEW.title, '')), 'D') || setweight(to_tsvector('english', COALESCE(NEW.body, '')), 'D');
    END IF;
    IF TG_OP = 'UPDATE' THEN
        IF NEW.title <> OLD.title OR NEW.body <> OLD.body THEN
            new.tsvector = setweight(to_tsvector('english', COALESCE(NEW.title, '')), 'D') || setweight(to_tsvector('english', COALESCE(NEW.body, '')), 'D');
        END IF;
    END IF;
RETURN NEW;
END;
$$ LANGUAGE 'plpgsql';
CREATE TRIGGER testapp_tsvectormodel_tsvector_update BEFORE INSERT OR UPDATE ON testapp_tsvectormodel
FOR EACH ROW EXECUTE PROCEDURE testapp_tsvectormodel_tsvector_update();""",
            stdout.getvalue()
        )

    # multiple dictionaries
    @override_system_checks([])
    @override_settings(MIGRATION_MODULES={"testapp": "testapp.migrations_multidict"})
    def test_sql_migrate_creates_vector_field_multi(self):
        stdout = six.StringIO()
        call_command('sqlmigrate', 'testapp', '0002', stdout=stdout)
        self.assertIn('"tsvector" tsvector null', stdout.getvalue().lower())
        self.assertIn(
            "UPDATE testapp_tsvectormodel SET tsvector = setweight(to_tsvector(dictionary::regconfig, COALESCE(title, '')), 'D') || setweight(to_tsvector(dictionary::regconfig, COALESCE(body, '')), 'D');",
            stdout.getvalue())

    @override_system_checks([])
    @override_settings(MIGRATION_MODULES={"testapp": "testapp.migrations_multidict"})
    def test_sql_fts_index_multi(self):
        stdout = six.StringIO()

        call_command('sqlmigrate', 'testapp', '0003', stdout=stdout)
        self.assertIn(
            ('CREATE INDEX testapp_tsvectormodel_tsvector ON '
             'testapp_tsvectormodel USING gin(tsvector);'),
            stdout.getvalue())
        self.assertIn(
            ('CREATE INDEX testapp_tsvectormodel_tsvector ON '
             'testapp_tsvectormodel USING gin(tsvector);'),
            stdout.getvalue())

    @override_system_checks([])
    @override_settings(MIGRATION_MODULES={"testapp": "testapp.migrations_multidict"})
    def test_sql_fts_trigger_multi(self):
        stdout = six.StringIO()
        call_command('sqlmigrate', 'testapp', '0004', stdout=stdout)
        self.assertIn(
            """
CREATE FUNCTION testapp_tsvectormodel_tsvector_update() RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        new.tsvector = setweight(to_tsvector(NEW.dictionary::regconfig, COALESCE(NEW.title, '')), 'D') || setweight(to_tsvector(NEW.dictionary::regconfig, COALESCE(NEW.body, '')), 'D');
    END IF;
    IF TG_OP = 'UPDATE' THEN
        IF NEW.dictionary <> OLD.dictionary OR NEW.title <> OLD.title OR NEW.body <> OLD.body THEN
            new.tsvector = setweight(to_tsvector(NEW.dictionary::regconfig, COALESCE(NEW.title, '')), 'D') || setweight(to_tsvector(NEW.dictionary::regconfig, COALESCE(NEW.body, '')), 'D');
        END IF;
    END IF;
RETURN NEW;
END;
$$ LANGUAGE 'plpgsql';
CREATE TRIGGER testapp_tsvectormodel_tsvector_update BEFORE INSERT OR UPDATE ON testapp_tsvectormodel
FOR EACH ROW EXECUTE PROCEDURE testapp_tsvectormodel_tsvector_update();""",
            stdout.getvalue()
        )


class TransactionsMigrationsTest(FTSTestBase):

    # available_apps = ["testapp"]

    @override_system_checks([])
    @override_settings(MIGRATION_MODULES={"testapp": "testapp.migrations_index"})
    def test_migrate_forwards_backwards(self):
        stdout = six.StringIO()
        call_command('migrate', 'testapp', '0002', stdout=stdout)
        self.assertTableExists('testapp_tsvectormodel')
        self.assertIndexNotExists('tsvector',
                                  'testapp_tsvectormodel')
        call_command('migrate', 'testapp', '0003', stdout=stdout)
        self.assertIndexExists('tsvector', 'testapp_tsvectormodel')
        self.assertFunctionNotExists('testapp_tsvectormodel_tsvector_update')
        self.assertTriggerNotExists('testapp_tsvectormodel_tsvector_update')
        call_command('migrate', 'testapp', '0004', stdout=stdout)
        self.assertFunctionExists('testapp_tsvectormodel_tsvector_update')
        self.assertTriggerExists('testapp_tsvectormodel_tsvector_update')
        call_command('migrate', 'testapp', '0005', stdout=stdout)
        self.assertFunctionNotExists('testapp_tsvectormodel_tsvector_update')
        self.assertTriggerNotExists('testapp_tsvectormodel_tsvector_update')
        self.assertTableNotExists('testapp_tsvectormodel')
        call_command('migrate', 'testapp', '0004', stdout=stdout)
        self.assertFunctionExists('testapp_tsvectormodel_tsvector_update')
        self.assertTriggerExists('testapp_tsvectormodel_tsvector_update')
        self.assertTableExists('testapp_tsvectormodel')
        call_command('migrate', 'testapp', '0003', stdout=stdout)
        self.assertFunctionNotExists('testapp_tsvectormodel_tsvector_update')
        self.assertTriggerNotExists('testapp_tsvectormodel_tsvector_update')
        call_command('migrate', 'testapp', '0002', stdout=stdout)
        self.assertIndexNotExists('tsvector',
                                  'testapp_tsvectormodel')
        call_command('migrate', 'testapp', '0001', stdout=stdout)

    @override_system_checks([])
    @override_settings(MIGRATION_MODULES={"testapp": "testapp.migrations_index"})
    def test_migrate_forwards_backwards_multi(self):
        stdout = six.StringIO()
        call_command('migrate', 'testapp', '0002', stdout=stdout)
        self.assertTableExists('testapp_tsvectormodel')
        self.assertIndexNotExists('tsvector',
                                  'testapp_tsvectormodel')
        call_command('migrate', 'testapp', '0003', stdout=stdout)
        self.assertIndexExists('tsvector', 'testapp_tsvectormodel')
        self.assertFunctionNotExists('testapp_tsvectormodel_tsvector_update')
        self.assertTriggerNotExists('testapp_tsvectormodel_tsvector_update')
        call_command('migrate', 'testapp', '0004', stdout=stdout)
        self.assertFunctionExists('testapp_tsvectormodel_tsvector_update')
        self.assertTriggerExists('testapp_tsvectormodel_tsvector_update')
        call_command('migrate', 'testapp', '0005', stdout=stdout)
        self.assertFunctionNotExists('testapp_tsvectormodel_tsvector_update')
        self.assertTriggerNotExists('testapp_tsvectormodel_tsvector_update')
        self.assertTableNotExists('testapp_tsvectormodel')
        call_command('migrate', 'testapp', '0004', stdout=stdout)
        self.assertFunctionExists('testapp_tsvectormodel_tsvector_update')
        self.assertTriggerExists('testapp_tsvectormodel_tsvector_update')
        self.assertTableExists('testapp_tsvectormodel')
        call_command('migrate', 'testapp', '0003', stdout=stdout)
        self.assertFunctionNotExists('testapp_tsvectormodel_tsvector_update')
        self.assertTriggerNotExists('testapp_tsvectormodel_tsvector_update')
        call_command('migrate', 'testapp', '0002', stdout=stdout)
        self.assertIndexNotExists('tsvector',
                                  'testapp_tsvectormodel')
        call_command('migrate', 'testapp', '0001', stdout=stdout)
