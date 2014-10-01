=============
django-pg-fts
=============

Implementation PostgeSQL for Full Text Search for Django 1.7, taking advantage of new features Migrations and Custom Lookups.


Features:

- FieldLookup's search, isearch, tsquery

- Ranking support with annotations results with normalization

- Migrations classes to help create and remove index's, support for 'gin' or 'gist'

- Migrations classes to help create and remove of trigger's

- Multiple dictionaries support with trigger and FieldLookup's

- Support for python 2.7, 3.3 and 3.4


With multiple dictionary support, index and trigger migrations

How it works
------------

For a existing model::

    class Article(models.Model):
        title = models.CharField(max_length=255)
        article = models.TextField()

You want to have full text search in fields title and article, and make give weight to title of 'A'.

Import TSVectorField::

    from pg_fts.fields import TSVectorField

Add to existing TSVectorField to model and tell the fields that you want to index and the dictionary::

    fts = TSVectorField(fields=(('title', 'A'), 'article'), dictionary='english')

Create migrations file::
    
    python manage.py makemigrations article

Open the new created migration and import CreateFTSIndexOperation, CreateFTSTriggerOperation, UpdateVectorOperation::

    from pg_fts.migrations import (CreateFTSIndexOperation, CreateFTSTriggerOperation,
                                   UpdateVectorOperation)

And add to the end of operations::

    # update vector for already existing data
    UpdateVectorOperation(
        name='Article',
        field='fts',    
    ),
    # create trigger for automatic insert and update vector
    CreateFTSTriggerOperation(
        name='Article',
        field='fts'
    ),
    # create gin index for vector
    CreateFTSIndexOperation(
        name='Article',
        field='fts',
        index='gin'
    )

Make the changes to your database::

    python manage.py migrate article

Now you have a full text search performance with a trigger that checks any changes in the tracked fields and updates vector field.

You can search will match all words:

>>> Article.objects.filter(fts_search='waz up')

Will result in sql something like:

.. code-block:: sql

    tsvector @@ to_tsquery('english', 'waz & up')

Or isearch will match some words:

>>> Article.objects.filter(fts_isearch='waz up')

Will result in sql something like:

.. code-block:: sql

    tsvector @@ to_tsquery('english', 'waz | up')

But you can make a raw tsquery:

>>> Article.objects.filter(fts_tsquery='waz & !up')

Will result in sql something like:

.. code-block:: sql

    tsvector @@ to_tsquery('english', 'waz & !up')

And also rank the results with normalization and order:

>>> from pg_fts.aggregates import FTSRank
>>> Article.objects.filter(
    rank=FTSRank(fts_search='waz up', normalization=[1,3])).order_by('-rank')

For multiple dictionaries and more advanced options, check the documentation.

Documentation
-------------

Documentation available in `Read The Docs <http://django-pg-fts.readthedocs.org/>`_

Installation
------------

Clone from GitHub::
    
    git clone git://github.com/dvdmgl/django-pg-fts.git django-pg-fts

You should run the tests::

    python runtests.py

Or running tox for py27, py33, py34::
    
    tox

Install using pip from github::

    pip install git+https://github.com/dvdmgl/django-pg-fts

Or using setup.py::

    python setup.py

