# -*- coding: utf-8 -*-
from __future__ import unicode_literals


class PgFTSIntrospection(object):
    """
        Helper class the introspect the database
    """
    def get_dictionay_list(self, cursor):
        """
        introspects pg_catalog.pg_ts_config

        :returns: A list of dictionaries names installed in postgres
        """

        'SELECT cfgname FROM "pg_catalog"."pg_ts_config"'
        return [row[0] for row in cursor.fetchall()]

    def get_trigger_list(self, cursor):
        """
        introspects the database for triggers

        :returns: A list of triggers
        """

        cursor.execute("""
            SELECT DISTINCT trigger_name
            FROM information_schema.triggers
            WHERE trigger_schema NOT IN
                ('pg_catalog', 'information_schema');""")
        return [row[0] for row in cursor.fetchall()]

    def get_functions_list(self, cursor):
        """
        introspects the database for functions

        :returns: A list of functions
        """

        cursor.execute('''SELECT p.proname AS function_name
FROM   (SELECT oid, * FROM pg_proc p WHERE NOT p.proisagg) p
JOIN   pg_namespace n ON n.oid = p.pronamespace
WHERE  n.nspname = 'public'
''')
        return [row[0] for row in cursor.fetchall()]