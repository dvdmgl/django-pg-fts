#!/usr/bin/env python
import sys
from django.conf import settings, global_settings as default_settings
from django.core.management import execute_from_command_line
from django import setup
from os import path


if not settings.configured:
    module_root = path.dirname(path.realpath(__file__))

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
        TEMPLATE_CONTEXT_PROCESSORS = default_settings.TEMPLATE_CONTEXT_PROCESSORS + (
            'django.core.context_processors.request',
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
        TEST_RUNNER='django.test.simple.DjangoTestSuiteRunner',
        LANGUAGE_CODE = 'en',
        MIDDLEWARE_CLASSES=default_settings.MIDDLEWARE_CLASSES + (
            'django.middleware.locale.LocaleMiddleware',
        ),
    )


def runtests():
    setup()
    argv = sys.argv[:1] + ['test', 'pg_fts'] + sys.argv[1:]

    execute_from_command_line(argv)


if __name__ == '__main__':
    runtests()
