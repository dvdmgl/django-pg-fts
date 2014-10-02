========
Tutorial
========

Getting started
===============

Create a new project like ``fooproject`` and ``article`` app::

    django-admin startproject fooproject
    cd fooproject
    django-admin startapp article


**Add ``pg_fts`` To ``INSTALLED_APPS``**

As with most django applications, you should add ``pg_fts`` to the ``INSTALLED_APPS`` in your ``settings.py`` file::

    INSTALLED_APPS = (
        'django.contrib.auth',
        # ...
        'pg_fts',
        'article'  # as an example app
    )
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            # ...
    }

.. caution::
    this is a PostgreSQL module be sure that your database ``ENGINE`` in  ``DATABASES`` is ``'django.db.backends.postgresql_psycopg2'``

Single dictionary example
-------------------------

Set up your article.models and add :class:`~pg_fts.fields.TSVectorField`::

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

The ``dictionary='portuguese'`` indicates that will be used the ``pg_catalog.portuguese`` dictionary.

For the option ``(('title', 'A'), 'article')`` the ``('title', 'A')`` ``'title'`` refers to the field ``title`` and ``'A'`` is the rank given to this field, ``'article'`` refers to the field ``article`` and it will be given the default rank value of ``'D'``.

.. caution::
    :class:`~pg_fts.fields.TSVectorField` option ``db_index`` cannot be used, as the correct type of index is *gin* or *gist* will be created in :class:`~pg_fts.migrations.CreateFTSIndexOperation`

Now create migrations for this module::

    python makemigrations article

Migrations create index and trigger
...................................

This will create the migration code to apply to your model, but before applying ``migrate`` lets edit the created migration and import::

    from pg_fts.migrations import CreateFTSIndexOperation, CreateFTSTriggerOperation

At the end of the array ``operations`` add operation :class:`~pg_fts.migrations.CreateFTSIndexOperation` to create the ``gin`` index for :class:`~pg_fts.fields.TSVectorField` ``fts_index``::

    CreateFTSIndexOperation(
        name='Article',
        fts_vector='fts_index',
        index='gin'
    ),

.. note::

    :class:`~pg_fts.migrations.CreateFTSTriggerOperation` only updates vector on future updates/inserts.

    For indexing the current data add to operations :class:`~pg_fts.migrations.UpdateVectorOperation`::

        UpdateVectorOperation(
            name='Article',
            fts_vector='fts_index',
        )

And also add :class:`~pg_fts.migrations.CreateFTSTriggerOperation` to create an automatic trigger for updating the ``fts_index``::

    CreateFTSTriggerOperation(
        name='Article',
        fts_vector='fts_index',
    ),

The complete code in ``migrations/0001_initial.py`` should be like this::

    class Migration(migrations.Migration):

        dependencies = [
        ]

        operations = [
            migrations.CreateModel(
                name='Article',
                fields=[
                    ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                    ('title', models.CharField(max_length=255)),
                    ('article', models.TextField()),
                    ('fts_index', pg_fts.fields.TSVectorField(editable=False, serialize=False, null=True, fields=(('title', 'A'), 'article'), dictionary='portuguese', default='')),
                ],
                options={
                },
                bases=(models.Model,),
            ),
            # create gin index to Article.fts_index
            CreateFTSIndexOperation(
                name='Article',
                fts_vector='fts_index',
                index='gin'
            ),
            # create trigger to Article.fts_index
            CreateFTSTriggerOperation(
                name='Article',
                fts_vector='fts_index'
            ),
        ]

To see the migration to be applied to your database, run::

    python manage.py sqlmigrate article 0001

It should display:

.. code-block:: sql

    BEGIN;

    CREATE TABLE "article_article" ("id" serial NOT NULL PRIMARY KEY, "title" varchar(255) NOT NULL, "article" text NOT NULL, "fts_index" tsvector NULL);
    CREATE INDEX article_article_fts_index ON article_article USING gin(fts_index);

    CREATE FUNCTION article_article_fts_index_update() RETURNS TRIGGER AS $$
    BEGIN
        IF TG_OP = 'INSERT' THEN
            new.fts_index = setweight(to_tsvector('portuguese', COALESCE(NEW.title, '')), 'A') || setweight(to_tsvector('portuguese', COALESCE(NEW.article, '')), 'D');
        END IF;
        IF TG_OP = 'UPDATE' THEN
            IF NEW.title <> OLD.title OR NEW.article <> OLD.article THEN
                new.fts_index = setweight(to_tsvector('portuguese', COALESCE(NEW.title, '')), 'A') || setweight(to_tsvector('portuguese', COALESCE(NEW.article, '')), 'D');
            END IF;
        END IF;
    RETURN NEW;
    END;
    $$ LANGUAGE 'plpgsql';
    CREATE TRIGGER article_article_fts_index_update BEFORE INSERT OR UPDATE ON article_article
    FOR EACH ROW EXECUTE PROCEDURE article_article_fts_index_update();


    COMMIT;


Now apply the migrations to your database::
    
    python manage.py migrate article

Using lookups
.............

With ``python manage.py shell``::

    >>> from testapp.models import Article
    >>> Article.objects.create(title='PHP', article='what a pain, the worst of c, c++, perl all mixed in one stupid thing')
    >>> Article.objects.create(title='Python', article='is awesome')
    >>> Article.objects.create(title='django', article='is awesome, made in python, multiple databases support, it has a ORM, class based views, template layer')
    >>> Article.objects.create(title='Wordpress', article="what a pain, made in PHP, it's ok if you just add a template and some plugins")
    >>> Article.objects.create(title='Javascript', article='A functional language, with c syntax. The braces nightmare')
    >>> Article.objects.filter(fts_index__search='django')
    [<Article: django>]
    >>> Article.objects.filter(fts_index__search='Python')
    [<Article: Python>, <Article: django>]
    >>> Article.objects.filter(fts_index__search='templates')
    [<Article: Wordpress>, <Article: django>]
    # postgress & and
    search = Article.objects.filter(fts_index__search='templates awesome')
    >>> print(search.query)
    SELECT "article_article"."id", "article_article"."title", "article_article"."article", "article_article"."fts_index" FROM "article_article" WHERE "article_article"."fts_index" @@ to_tsquery('portuguese', templates & awesome)
    print(search)
    [<Article: django>] # only django has template language AND is awesome
    isearch = Article.objects.filter(fts_index__isearch='templates awesome')
    >>> print(isearch.query)
    SELECT "article_article"."id", "article_article"."title", "article_article"."article", "article_article"."fts_index" FROM "article_article" WHERE "article_article"."fts_index" @@ to_tsquery('portuguese', templates | awesome)
    print(isearch)
    [<Article: Python>, <Article: Wordpress>, <Article: django>]
    # wordpress oh no and in 2nd position, let's rank the results

Ranking results
...............

To rank results :pg_docs:`12.3.3. Ranking Search Results <textsearch-controls.html#TEXTSEARCH-RANKING>` let's use django annotate.

For this lets use :class:`~pg_fts.ranks.FTSRank`, :class:`~pg_fts.ranks.FTSRankCd`

>>> from pg_fts.ranks import FTSRank, FTSRankCd
>>> ranks = Article.objects.annotate(rank=FTSRank(fts_index__isearch='templates awesome')).order_by('-rank')
>>> ranks
[<Article: django>, <Article: Python>, <Article: Wordpress>]
# that's better, wordpress has templates, but it's not awesome, but let's check ranks
>>> [(r.title, r.rank) for r in ranks]
[('django', 0.0607927), ('Python', 0.0303964), ('Wordpress', 0.0303964)]
# lucky for python appear before wordpress, let's normalize the results
>>> ranks_cd = Article.objects.annotate(rank=FTSRankCd(fts_index__isearch='awesome templates', normalization=[16|32])).order_by('-rank')
>>> [(r.title, r.rank) for r in ranks_cd]
[('Python', 0.047619), ('django', 0.0457674), ('Wordpress', 0.0234196)]

Python and django are awesome, check the postgres documentation for more about normalization

Multiple dictionary example
---------------------------

Multiple dictionary support::

    class ArticleMulti(models.Model):
        title = models.CharField(max_length=255)
        article = models.TextField()
        # dictionary field to be used in query and trigger
        dictionary = models.CharField(
            max_length=15,
            choices=(('english', 'english'), ('portuguese', 'portuguese')),
            default='english',
            db_index=True
        )

        fts_index = TSVectorField(
            (('title', 'A'), 'article'),
            dictionary='dictionary'  # refers to dictionary field in model
        )

        def __str__(self):
            return self.title

Migrations create index and trigger
...................................

Like before in Single dictionary example::

    from pg_fts.migrations import CreateFTSIndexOperation, CreateFTSTriggerOperation

At the end of the array ``operations``::

    CreateFTSIndexOperation(
        name='ArticleMulti',
        fts_vector='fts_index',
        index='gin'
    ),
    CreateFTSTriggerOperation(
        name='ArticleMulti',
        fts_vector='fts_index',
    ),

But running ``python manage.py sqlmigrate article 0002`` generates the appropriate trigger

.. code-block:: sql

    BEGIN;

    --- ...

    $$ LANGUAGE 'plpgsql';
    CREATE TRIGGER article_article_fts_index_update BEFORE INSERT OR UPDATE ON article_article
    FOR EACH ROW EXECUTE PROCEDURE article_article_fts_index_update();

    CREATE FUNCTION article_articlemulti_fts_index_update() RETURNS TRIGGER AS $$
    BEGIN
        IF TG_OP = 'INSERT' THEN
            new.fts_index = setweight(to_tsvector(NEW.dictionary::regconfig, COALESCE(NEW.title, '')), 'A') || setweight(to_tsvector(NEW.dictionary::regconfig, COALESCE(NEW.article, '')), 'D');
        END IF;
        IF TG_OP = 'UPDATE' THEN
            IF NEW.dictionary <> OLD.dictionary OR NEW.title <> OLD.title OR NEW.article <> OLD.article THEN
                new.fts_index = setweight(to_tsvector(NEW.dictionary::regconfig, COALESCE(NEW.title, '')), 'A') || setweight(to_tsvector(NEW.dictionary::regconfig, COALESCE(NEW.article, '')), 'D');
            END IF;
        END IF;
    RETURN NEW;
    END;
    $$ LANGUAGE 'plpgsql';
    CREATE TRIGGER article_articlemulti_fts_index_update BEFORE INSERT OR UPDATE ON article_articlemulti
    FOR EACH ROW EXECUTE PROCEDURE article_articlemulti_fts_index_update();
    
    --- ...

    COMMIT;

Now the ``INSERT`` and ``UPDATE`` uses ``NEW.dictionary::regconfig`` for getting the language from dictionary

Using lookups
.............

Now the lookup checks the :class:`~pg_fts.fields.DictionaryTransform` for dictionary transformations.

For English search::

    en = ArticleMulti.objects.filter(fts_index__english__search='django')

For Portuguese search::

    pt = ArticleMulti.objects.filter(fts_index__portuguese__search='django')

.. note::
    
    Should be applied the filter for the dictionary field::

        en.filter(dictionary='english')
        pt.filter(dictionary='portuguese')

>>> ArticleMulti.objects.create(title='PHP', article='what a pain, the worst of c, c++, perl all mixed in one stupid thing', dictionary='english')
>>> ArticleMulti.objects.create(title='Python', article='is awesome', dictionary='english')
>>> ArticleMulti.objects.create(title='django', article='is awesome, made in python', dictionary='english')
>>> ArticleMulti.objects.create(title='Wordpress', article="what a pain, made in PHP, it's ok if you just add a template and some plugins")
>>> ArticleMulti.objects.create(title='Javascript', article='A functional dictionary, with c syntax. The braces nightmare', dictionary='english')
## Portuguese
>>> ArticleMulti.objects.create(title='PHP', article='que dor, o pior do c, c++ e perl tudo junto para ser a coisa mais estupida', dictionary='portuguese')
>>> ArticleMulti.objects.create(title='Python', article='é Brutal', dictionary='portuguese')
>>> ArticleMulti.objects.create(title='django', article='é Altamente, feito em python', dictionary='portuguese')
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


Ranking results
...............

To rank results in case of multiple dictionaries, use the appropriate :class:`~pg_fts.ranks.FTSRankDictionary`, :class:`~pg_fts.ranks.FTSRankCdDictionary`

Works like the Single Dictionary but with Multiple lookups

>>> ArticleMulti.objects.filter(dictionary='portuguese').annotate(
    rank=(FTSRankDictionary(
        fts_index__portuguese__search='pesadelo')).order_by('rank')


Removing and updating migrations
--------------------------------

If you remove, rename, alter one off the fields related to :class:`~pg_fts.fields.TSVectorField`

Changing the single dictionary Article to a multiple dictionary Article instead of creating a ArticleMulti

reverse migration to 0001 so does not include ArticleMulti::

    python manage.py migrate article 0001

Delete the 0002 migration, remove ArticleMulti from models.py and add / change Article to::

    class Article(models.Model):
        title = models.CharField(max_length=255)
        article = models.TextField()

    dictionary = models.CharField(
        max_length=15,
        choices=(('english', 'english'), ('portuguese', 'portuguese')),
        default='english'
    )

    fts_index = TSVectorField(
        (('title', 'A'), 'article'),
        dictionary='dictionary'  # now it refers to the dictionary field
    )

    def __str__(self):
        return self.title

Let django find the model alterations for us::

    python manage.py makemigrations article

But we have to edit the migrations 0002 file before applying and add to operations :class:`~pg_fts.migrations.DeleteFTSTriggerOperation` and :class:`~pg_fts.migrations.DeleteFTSIndexOperation` **before** django auto migrations, and **at the end** of operations the :class:`~pg_fts.migrations.CreateFTSIndexOperation` and :class:`~pg_fts.migrations.CreateFTSTriggerOperation`.

The migrations 0002 file should be like this::

    # -*- coding: utf-8 -*-
    from __future__ import unicode_literals

    from django.db import models, migrations
    import pg_fts.fields
    from pg_fts.migrations import (CreateFTSIndexOperation,
                                   CreateFTSTriggerOperation,
                                   DeleteFTSIndexOperation,
                                   DeleteFTSTriggerOperation)


    class Migration(migrations.Migration):

        dependencies = [
            ('article', '0001_initial'),
        ]

        operations = [
            # remove previous created CreateFTSTriggerOperation
            DeleteFTSTriggerOperation(
                name='Article',
                fts_vector='fts_index'
            ),
            # remove previous created CreateFTSIndexOperation
            DeleteFTSIndexOperation(
                name='Article',
                fts_vector='fts_index',
                index='gin'
            ),
            # the django created changes
            migrations.AddField(
                model_name='article',
                name='dictionary',
                field=models.CharField(default='english', choices=[('english', 'english'), ('portuguese', 'portuguese')], max_length=15),
                preserve_default=True,
            ),
            migrations.AlterField(
                model_name='article',
                name='fts_index',
                field=pg_fts.fields.TSVectorField(dictionary='dictionary', serialize=False, default='', null=True, editable=False, fields=(('title', 'A'), 'article')),
            ),
            # add new index
            CreateFTSIndexOperation(
                name='Article',
                fts_vector='fts_index',
                index='gin'
            ),
            # and create new trigger
            CreateFTSTriggerOperation(
                name='Article',
                fts_vector='fts_index'
            ),

        ]

.. warning::

    Pay special attention to the order of creation and deleting.

    You can only apply :class:`~pg_fts.migrations.CreateFTSIndexOperation` and :class:`~pg_fts.migrations.CreateFTSTriggerOperation` after django created operations.

    The :class:`~pg_fts.migrations.DeleteFTSTriggerOperation` and :class:`~pg_fts.migrations.DeleteFTSIndexOperation` before django removing/altering operations

    Not to forget **USE AT YOUR OWN RISK**
