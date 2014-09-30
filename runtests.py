#!/usr/bin/env python
import sys
from django.conf import settings, global_settings as default_settings
from django.core.management import execute_from_command_line
from django import setup


if not settings.configured:

    settings.configure(
        DEBUG = False,  # will be False anyway by DjangoTestRunner.
        TEMPLATE_DEBUG = True,
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.postgresql_psycopg2',
                'NAME': 'test',
                'USER': '',
                'PASSWORD': '',
                'HOST': 'localhost',
                'PORT': '',
            }
        },
        TEMPLATE_LOADERS = (
            'django.template.loaders.app_directories.Loader',
            'django.template.loaders.filesystem.Loader',
        ),
        INSTALLED_APPS = (
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'django.contrib.sites',
            'django.contrib.admin',
            'django.contrib.sessions',
            'pg_fts',
            'testapp'
        ),
        ROOT_URLCONF = 'testproject.urls',
        TEST_RUNNER='django.test.runner.DiscoverRunner',
        LANGUAGE_CODE = 'en',
        MIDDLEWARE_CLASSES=default_settings.MIDDLEWARE_CLASSES
    )


def runtests():
    setup()
    argv = sys.argv[:1] + ['test', 'testapp'] + sys.argv[1:]

    execute_from_command_line(argv)


if __name__ == '__main__':
    runtests()
