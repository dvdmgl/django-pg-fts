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
    Create index's `gin` or `gist`

`pg_fts.migrations.CreateFTSTriggerOperation`
    Create trigger for updating VectorField of fields options

`pg_fts.migrations.DeleteFTSIndexOperation`
    Remove index

`pg_fts.migrations.DeleteFTSTriggerOperation`
    Remove trigger


``TSVectorField``
-----------------

.. class:: TSVectorField([fields, dictionary='english', editable=False, serialize=False, default='', **options])

.. attribute:: TSVectorField.fields
    
    Tuple of `field names` or ('field_name', 'rank')
    Available ranks ('A', 'B', 'C', 'D'), default `D`

.. attribute:: TSVectorField.dictionary
    
    Name of the dictionary in postgresql or the name of the field for multidict with CharField with postgreSQL dictionaries as choices


``CreateFTSIndexOperation``
---------------------------

.. class:: CreateFTSIndexOperation(name, fts_vector, index)

.. attribute:: CreateFTSIndexOperation.name
    
    the name of the model

.. attribute:: CreateFTSIndexOperation.fts_vector

    the TSVectorField name

.. attribute:: CreateFTSIndexOperation.index

    the index can be `gist` or `gin`

``CreateFTSTriggerOperation``
---------------------------

.. class:: CreateFTSTriggerOperation(name, fts_vector)

.. attribute:: CreateFTSTriggerOperation.name
    
    the name of the model

.. attribute:: CreateFTSTriggerOperation.fts_vector

    the TSVectorField name


``DeleteFTSIndexOperation``
---------------------------

.. class:: DeleteFTSIndexOperation(name, fts_vector, index)

.. attribute:: DeleteFTSIndexOperation.name
    
    the name of the model

.. attribute:: DeleteFTSIndexOperation.fts_vector

    the TSVectorField name

.. attribute:: DeleteFTSIndexOperation.index

    the index can be `gist` or `gin`

``DeleteFTSTriggerOperation``
---------------------------

.. class:: DeleteFTSTriggerOperation(name, fts_vector)

.. attribute:: DeleteFTSTriggerOperation.name
    
    the name of the model

.. attribute:: DeleteFTSTriggerOperation.fts_vector

    the TSVectorField name



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
            dictionary='portuguese'
        )

        def __str__(self):
            return self.title

    class ArticleMulti(models.Model):
        title = models.CharField(max_length=255)
        article = models.TextField()
        # dictionary field to be used in query and trigger
        dictionary = models.CharField(
            max_length=15,
            choices=(('english', 'english'), ('portuguese', 'portuguese')),
            default='english'
        )

        fts_index = TSVectorField(
            (('title', 'A'), 'article'),
            dictionary='dictionary'  # refers to dictionary field in model
        )

        def __str__(self):
            return self.title

run `manage.py makemigrations testapp`

in the auto-generated migration

- migrations/0001_initial.py

.. code-block:: python

    from pg_fts.migrations import CreateFTSIndexOperation, CreateFTSTriggerOperation
    ...
    class Migration(migrations.Migration):
    ...
    operations = [
        migrations.CreateModel(
            name='Article',
            fields=[
                ('fts_index', pg_fts.fields.TSVectorField(editable=False, serialize=False, null=True, fields=(('title', 'A'), 'article'), dictionary='portuguese', default='')),
                ...
            ],
            ...
        ),
        migrations.CreateModel(
            name='ArticleMulti',
            fields=[
                ('dictionary', models.CharField(max_length=15, default='english', choices=[('english', 'english'), ('portuguese', 'portuguese')])),
                ('fts_index', pg_fts.fields.TSVectorField(editable=False, serialize=False, null=True, fields=(('title', 'A'), 'article'), dictionary='dictionary', default='')),
                ...
            ],
            ...
        ),
        # create gin index Article.fts_index
        CreateFTSIndexOperation(
            name='Article',
            fts_vector='fts_index',
            index='gin'
        ),
        # create insert and update trigger to Article.fts_index
        CreateFTSTriggerOperation(
            name='Article',
            fts_vector='fts_index',
        )
        # create gin index ArticleMulti.fts_index
        CreateFTSIndexOperation(
            name='ArticleMulti',
            fts_vector='fts_index',
            index='gin'
        ),
        # create insert and update trigger to ArticleMulti.fts_index
        CreateFTSTriggerOperation(
            name='ArticleMulti',
            fts_vector='fts_index',
        )
    ]

run `manage.py makemigrate testapp`

.. code-block:: python
    >>> from testapp.models import Article
    >>> Article.objects.create(title='PHP', article='what a pain, the worst of c, c++, perl all mixed in one stupid thing')
    >>> Article.objects.create(title='Python', article='is awesome')
    >>> Article.objects.create(title='Django', article='is awesome, made in python')
    >>> Article.objects.create(title='Wordpress', article="what a pain, made in PHP, it's ok if you just add a template and some plugins")
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

    ## Multidict
    >>> ArticleMulti.objects.create(title='PHP', article='what a pain, the worst of c, c++, perl all mixed in one stupid thing', dictionary='english')
    >>> ArticleMulti.objects.create(title='Python', article='is awesome', dictionary='english')
    >>> ArticleMulti.objects.create(title='Django', article='is awesome, made in python', dictionary='english')
    >>> ArticleMulti.objects.create(title='Wordpress', article="what a pain, made in PHP, it's ok if you just add a template and some plugins")
    >>> ArticleMulti.objects.create(title='Javascript', article='A functional dictionary, with c syntax. The braces nightmare', dictionary='english')
    ## Portuguese
    >>> ArticleMulti.objects.create(title='PHP', article='que dor, o pior do c, c++ e perl tudo junto para ser a coisa mais estupida', dictionary='portuguese')
    >>> ArticleMulti.objects.create(title='Python', article='é Brutal', dictionary='portuguese')
    >>> ArticleMulti.objects.create(title='Django', article='é Altamente, feito em python', dictionary='portuguese')
    >>> ArticleMulti.objects.create(title='Wordpress', article="que dor, feito em PHP, não é mau para quem usa os templates e plugins")
    >>> ArticleMulti.objects.create(title='Javascript', article='Uma linguagem funcional, mas tem sintaxe c para confundir. O pesadelo das chavetas', dictionary='portuguese')
    >>> django_pt = ArticleMulti.objects.filter(fts_index__portuguese__search='django', dictionary='portuguese')
    >>> ArticleMulti.objects.filter(fts_index__portuguese__search='pesadelo')
    [<ArticleMulti: Javascript>]
    >>> django_pt[0].article
    'é Altamente, feito em python'
    >>> django_en = ArticleMulti.objects.filter(fts_index__english__search='django', dictionary='english')
    >>> django_en[0].article
    'is awesome, made in python'
