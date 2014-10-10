import os
from setuptools import setup

with open(os.path.join(os.path.dirname(__file__), 'README.rst')) as readme:
    README = readme.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))


setup(
    name='django-pg_fts',
    version='0.1.1',
    packages=['pg_fts'],
    include_package_data=True,
    license='BSD License',
    description='Implementation of PostgreSQL Full Text Search for django 1.7',
    long_description=README,
    url='https://github.com/dvdmgl/django-pg-fts',
    author='dvdmgl',
    author_email='dvdmgl@gmail.com',
    requires=[
        'Django (>=1.7)',
        'psycopg2'
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 2.7',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
    keywords='django postgres postgresql pgsql full text search fts',
)
