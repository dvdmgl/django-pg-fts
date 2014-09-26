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

As with most Django applications, you should add ``pg_fts`` to the ``INSTALLED_APPS`` in your ``settings.py`` file::

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
    Field option ``db_index`` cannot be used, as index will be created in :class:`~pg_fts.migrations.CreateFTSIndexOperation`

Now create migrations for this module::

    python makemigrations article

This will create the migration code to apply to your model, but before running ``migrate`` lets edit the created migration and import::

    from pg_fts.migrations import CreateFTSIndexOperation, CreateFTSTriggerOperation

At the end of the array ``operations`` add operation :class:`~pg_fts.migrations.CreateFTSIndexOperation` to create the ``gin`` index for :class:`~pg_fts.fields.TSVectorField` ``fts_index``::

    CreateFTSIndexOperation(
        name='Article',
        fts_vector='fts_index',
        index='gin'
    ),

And also add :class:`~pg_fts.fields.TSVectorField` to create an automatic trigger for updating the ``fts_index``::

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

With ``python manage.py shell``::

    >>> from testapp.models import Article
    >>> Article.objects.create(title='PHP', article='what a pain, the worst of c, c++, perl all mixed in one stupid thing')
    >>> Article.objects.create(title='Python', article='is awesome')
    >>> Article.objects.create(title='Django', article='is awesome, made in python, multiple databases support, it has a ORM, class based views, template layer')
    >>> Article.objects.create(title='Wordpress', article="what a pain, made in PHP, it's ok if you just add a template and some plugins")
    >>> Article.objects.create(title='Javascript', article='A functional language, with c syntax. The braces nightmare')
    >>> Article.objects.filter(fts_index__search='django')
    [<Article: Django>]
    >>> Article.objects.filter(fts_index__search='Python')
    [<Article: Python>, <Article: Django>]
    >>> Article.objects.filter(fts_index__search='templates')
    [<Article: Wordpress>, <Article: Django>]
    # postgress & and
    search = Article.objects.filter(fts_index__search='templates awesome')
    >>> print(search.query)
    SELECT "article_article"."id", "article_article"."title", "article_article"."article", "article_article"."fts_index" FROM "article_article" WHERE "article_article"."fts_index" @@ to_tsquery('portuguese', templates & awesome)
    print(search)
    [<Article: Django>] # only django has template language AND is awesome
    isearch = Article.objects.filter(fts_index__isearch='templates awesome')
    >>> print(isearch.query)
    SELECT "article_article"."id", "article_article"."title", "article_article"."article", "article_article"."fts_index" FROM "article_article" WHERE "article_article"."fts_index" @@ to_tsquery('portuguese', templates | awesome)
    print(isearch)
    [<Article: Python>, <Article: Wordpress>, <Article: Django>]


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
            default='english'
        )

        fts_index = TSVectorField(
            (('title', 'A'), 'article'),
            dictionary='dictionary'  # refers to dictionary field in model
        )

        def __str__(self):
            return self.title
