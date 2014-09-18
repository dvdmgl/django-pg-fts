import os
from setuptools import setup

with open(os.path.join(os.path.dirname(__file__), 'README.rst')) as readme:
    README = readme.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))


setup(
    name='django-pg_fts',
    version='0.1',
    packages=['pg_fts'],
    include_package_data=True,
    license='BSD License',  # example license
    description='Implementation of postgresql full text search',
    long_description=README,
    url='http://www.dvdmgl.com/',
    author='David Miguel',
    author_email='dvdmgl@gmail.com',
    requires=[
        'Django (>=1.7)',
        'psycopg2'
    ],
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.3',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
)
