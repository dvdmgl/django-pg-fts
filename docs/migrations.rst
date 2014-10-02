Migrations
==========


.. important::

    If you're not familiar with django Migrations, please check `django Migrations Documentation <https://docs.djangoproject.com/en/1.7/topics/migrations/>`_ 1st.


.. important::

    The order of Migrations.operations matters, you can only apply a index to a field if a field exists, if you delete a model/field you should remove any operation first before removing model/field.


BaseVectorOperation options
***************************

The following arguments are available to all FTSMigration types

``name``
--------

.. attribute:: CreateFTSTriggerOperation.name

Name of the model

``fts_vector``
--------------

.. attribute:: CreateFTSTriggerOperation.fts_vector

Name of the :class:`~pg_fts.fields.TSVectorField`


Creating
--------

Trigger
*******

For creating of trigger is provided :class:`~pg_fts.migrations.CreateFTSTriggerOperation`.

``CreateFTSTriggerOperation``
-----------------------------

.. class:: CreateFTSTriggerOperation(options**)

How it works
++++++++++++

The trigger only updates the :class:`~pg_fts.fields.TSVectorField` if data is changed in the fields that is indexing, with it's weight (default is 'D') and language.

Example for this model::

    class Article(models.Model):
        title = models.CharField(max_length=255)
        article = models.TextField()
        fts = TSVectorField(
            (('title', 'A'), 'article'),
            dictionary='portuguese'
        )

In Migrations::

    class Migration(migrations.Migration)
        dependencies = [
            ('article', '00XX_create_fts_field'),
        ]

        operations = [
            CreateFTSTriggerOperation(
                name='Article',
                fts_vector='fts',
            ),
        ]

Will create this trigger:

.. code-block:: sql

    CREATE FUNCTION article_article_fts_update() RETURNS TRIGGER AS $$
    BEGIN
        IF TG_OP = 'INSERT' THEN
            new.fts = setweight(to_tsvector('portuguese', COALESCE(NEW.title, '')), 'A') || setweight(to_tsvector('portuguese', COALESCE(NEW.article, '')), 'D');
        END IF;
        IF TG_OP = 'UPDATE' THEN
            IF NEW.title <> OLD.title OR NEW.article <> OLD.article THEN
                new.fts = setweight(to_tsvector('portuguese', COALESCE(NEW.title, '')), 'A') || setweight(to_tsvector('portuguese', COALESCE(NEW.article, '')), 'D');
            END IF;
        END IF;
    RETURN NEW;
    END;
    $$ LANGUAGE 'plpgsql';
    CREATE TRIGGER article_article_fts_update BEFORE INSERT OR UPDATE ON article_article
    FOR EACH ROW EXECUTE PROCEDURE article_article_fts_update();


.. important::

    Trigger will only work for future changes, for existing data use :class:`~pg_fts.migrations.UpdateVectorOperation`.

Index
*****

For creating of indexes is provided :class:`~pg_fts.migrations.CreateFTSIndexOperation`.


``index``
---------

.. attribute:: CreateFTSIndexOperation.index

Options:

- ``gin`` GIN (Generalized Inverted Index)-based index. Faster to build, slower to lookup.

- ``gist`` GiST (Generalized Search Tree)-based index. Faster to lookup, slower to build.

For information about the ``gin`` and ``gist`` indexes types consult :pg_docs:`PostgreSQL documentation 12.9. GiST and GIN Index Types <textsearch-indexes.html>`

Example::

    class Migration(migrations.Migration)
        dependencies = [
            ('article', '0003_fts_create_field'),
        ]

        operations = [
            CreateFTSIndexOperation(
                name='Article',
                fts_vector='fts_index',
                index='gin'
            ),
        ]


Migrating from existing application
-----------------------------------

For existing application with data is provided :class:`~pg_fts.migrations.UpdateVectorOperation`, this will update the vector.

Changing and Removing
---------------------

Changing Index
**************

If you have a existing index created by :class:`~pg_fts.migrations.CreateFTSIndexOperation` of type ``gin`` to migrate for ``gist`` you have to 1st remove the existing index with :class:`~pg_fts.migrations.DeleteFTSIndexOperation` and create a of type ``gist`` with :class:`~pg_fts.migrations.CreateFTSIndexOperation`.

Example::

    class Migration(migrations.Migration)
        dependencies = [
            ('article', '0003_fts_create_index_trigger'),
        ]

        operations = [
            DeleteFTSIndexOperation(
                name='Article',
                fts_vector='fts_index',
                index='gin'
            ),
            CreateFTSIndexOperation(
                name='Article',
                fts_vector='fts_index',
                index='gist'
            ),
        ]

Alterations on :class:`~pg_fts.fields.TSVectorField`
****************************************************

If you change :class:`~pg_fts.fields.TSVectorField` is fields, ranks or dictionary you have to:

1. remove the trigger with :class:`~pg_fts.migrations.DeleteFTSTriggerOperation` and only after you can create

2. a new trigger with :class:`~pg_fts.migrations.CreateFTSTriggerOperation`.

For updating :class:`~pg_fts.fields.TSVectorField` run :class:`~pg_fts.migrations.UpdateVectorOperation`.

.. hint::

    If the fields are the same (fields and rank) but you are updating to multiple dictionaries, for efficiency, keep the previous dictionary as default, as the lexemes and weight will be the same in :class:`~pg_fts.fields.TSVectorField`.
    There is no need to run :class:`~pg_fts.migrations.UpdateVectorOperation`

Removing Index
**************

For removing the index is provided :class:`~pg_fts.migrations.DeleteFTSIndexOperation`.


``index``
---------

.. attribute:: CreateFTSIndexOperation.index 

The previous index type, important for regressions.

Removing Trigger
****************

For removing the index is provided :class:`~pg_fts.migrations.DeleteFTSTriggerOperation`.
