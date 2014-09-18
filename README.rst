=============
django-pg-fts
=============

Implementation postgeSQL for Full Text Search for Django >= 1.7
With multiple dictionary support, index (trigger) creation support

Classes
^^^^^^^

`pg_fts.fields.VectorField`
    An tsvector index field which stores converted text into special format.
`pg_fts.migrations.CreateFTSIndexOperation`
    An migration tool to create index's


``TSVectorField``
-----------------

.. class:: TSVectorField([fields, dictionary='english', fts_index='gin', editable=False, serialize=False, default='', **options])

.. attribute:: TSVectorField.fields
    
    Tuple of `field names` or ('field_name', 'rank')
    Available ranks ('A', 'B', 'C', 'D'), default `D`

.. attribute:: TSVectorField.dictionary
    
    Name of the dictionary in postgresql or the name of the field for multidict with charfield and choices

.. attribute:: TSVectorField.fts_index
    
    Type of index can be 'gist' or 'gin'

``CreateFTSIndexOperation``
---------------------------

.. class:: CreateFTSIndexOperation([model, fts_vectors])

.. attribute:: CreateFTSIndexOperation.model
    
    Model for index creation

.. attribute:: CreateFTSIndexOperation.fts_vectors

    Array of tuples of TSVectorField in model with the field name and field with is properties.

    See examples


Usage examples:
^^^^^^^^^^^^^^^

- testapp/models.py

.. code-block:: python

    from pg_fts.fields import TSVectorField
    from django.db import models

    class Article(models.Model):
        title = models.CharField(max_length=255)
        article = models.TextField()

        fts_index = TSVectorField(
            (('title', 'A'), 'article'),
            fts_index='gin',
            dictionary='portuguese'
        )

        def __str__(self):
            return self.title


run `manage.py makemigrations testapp`

in the auto-generated migration

- migrations/0001_initial.py

.. code-block:: python

    from pg_fts.migrations import CreateFTSIndexOperation
    from testapp.models import Article
    ...
    class Migration(migrations.Migration):
    ...
    operations = [
        migrations.CreateModel(
        ...
        ('fts_index', pg_fts.fields.TSVectorField(default='', null=True, fts_index='gin', fields=(('title', 'A'), 'article'), serialize=False, dictionary='portuguese', editable=False)),
        ...
        ),
        # add CreateFTSIndexOperation
        CreateFTSIndexOperation(
        model=Article,
        fts_vectors=[
            ('fts_index', pg_fts.fields.TSVectorField(default='', null=True, fts_index='gin', fields=(('title', 'A'), 'article'), serialize=False, dictionary='portuguese', editable=False)),
        ]
        )
    ]

run `manage.py makemigrate testapp`

.. code-block:: python
    >>> from testapp.models import Article
    >>> Article.objects.create(title='PHP', article='what a pain, the worst of c, c++, perl all mixed in one stupid thing')
    >>> Article.objects.create(title='Python', article='is awesome')
    >>> Article.objects.create(title='Django', article='is awesome, made in python')
    >>> Article.objects.create(title='Wordpress', article='what a pain, made in PHP, it's ok if you just add a template and some plugins')
    >>> Article.objects.create(title='Javascript', article='A functional language, with c syntax. The braces nightmare')
    >>> Article.objects.filter(fts_index__search='django')
    [<Article: Django>]
    >>> Article.objects.filter(fts_index__search='Python')
    [<Article: Python>, <Article: Django>]
    # postgress & and
    >>> Article.objects.filter(fts_index__search='made in python')
    [<Article: Django>]
    # postgress | or
    >>> Article.objects.filter(fts_index__isearch='made in python')
    [<Article: Python>, <Article: Django>, <Article: Wordpress>]
    # it has wordpress in the results because of 'made'

