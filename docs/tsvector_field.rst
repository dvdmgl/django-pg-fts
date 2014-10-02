TSVector
========

``TSVectorField``
-----------------

.. class:: TSVectorField(fields, dictionary)


.. attribute:: TSVectorField.fields

A tuple containing a tuple of fields and rank to be indexed, it can be only the field name the default the rank 'D' will be added

Example::

    ('field_name', ('field_name2', 'A'))

Will result in::

    (('field_name', 'D'), ('field_name2', 'A'))

.. attribute:: TSVectorField.dictionary

- Can be string with the dictionary name ``pg_catalog.pg_ts_config`` consult :pg_docs:`PostgreSQL documentation 12.6. Dictionaries <textsearch-dictionaries.html>`

- A CharField with choices in case of multiple dictionaries.

.. caution::

    Dictionary(ies) used must be installed in your database, check ``pg_catalog.pg_ts_config``

Will raise exception exceptions.FieldError if lookup isn't tsquery, search or isearch or not a valid option dictionary (in case of multiple dictionaries)

.. caution::

    TSVectorField does not support iexact, it will raise an exception


``FTSLookups``
--------------

search
******

Only return results that match all the lexemes.

isearch
*******

Return results if match any of the lexemes.

tsquery
*******

Raw tsquery, for full control over PostgreSQL to_tsquery. Check PostgreSQL documentation :pg_docs:`12.3.2. Parsing Queries <textsearch-controls.html#TEXTSEARCH-PARSING-QUERIES`


Single dictionary examples
--------------------------

.. code-block:: python

    class Article(models.Model):
        title = models.CharField(max_length=255)
        article = models.TextField()
        fts = TSVectorField(
            (('title', 'A'), 'article'),
            dictionary='portuguese'
        )

        def __str__(self):
            return self.title


>>> Article.objects.bulk_create([
    Article(title='Python', article='The python programing language')
    Article(title='Monty Python', article='British surreal comedy group')
    Article(title="Monty Python's Flying Circus", article="Monty Python's Flying Circus was a series created by Monty Python comedy group")
])


Using ``search`` for *python programing* and *python comedy*:

>>> Article.objects.filter(fts__search='python programing')
[<Article: Python>]
>>> Article.objects.filter(fts__search='comedy group')
[<Article: Monty Python's Flying Circus>, <Article: Monty Python>]
>>> Article.objects.filter(fts__search='PHP')
[]


If you use ``isearch`` will search for any of the lexemes:

>>> Article.objects.filter(fts__isearch='python programing')
[<Article: Python>, <Article: Monty Python's Flying Circus>, <Article: Monty Python>]
>>> Article.objects.filter(fts__isearch='PHP')
[]

.. seealso::

    For ordering results use :doc:`Ranking </ranks>`


``DictionaryTransform``
-----------------------

Preforms a transformation for dictionary for searching with *portuguese* lexemes ``fts__portuguese__search``

It checks if the dictionary is in options, only works with multiple dictionaries.


Multiple dictionaries examples
------------------------------

.. code-block:: python

    class Article(models.Model):
        title = models.CharField(max_length=255)
        article = models.TextField()
        
        dicts = models.CharField(  # the dictionary field
            max_length=15,
            choices=(('english', 'english'), ('portuguese', 'portuguese')),
            default='english',
            db_index=True
        )

        fts = TSVectorField(
            (('title', 'A'), 'article'),
            dictionary='dicts'  # refers to the dictionary field
        )

        def __str__(self):
            return '%s in %s' % (self.title, self.language)


>>> Article.objects.bulk_create([
    Article(title='Python', article='The python programing language', language='english')
    Article(title='Monty Python', article='British surreal comedy group', language='english')
    Article(title="Monty Python's Flying Circus", article="Monty Python's Flying Circus was a series created by Monty Python comedy group", language='english')
    Article(title='Python', article='A linguagem de programação python', language='portuguese')
    Article(title='Monty Python', article='Um grupo de comédia britânico', language='portuguese')
    Article(title="Os Malucos do Circo", article="Os Malucos do Circo ou Monty Python's Flying Circus no titulo orignial foi criada pelo grupo de comédia Monty Python", language='portuguese')
])

Use the dictionary transform, also we should filter by the dictionary used:

>>> Article.objects.filter(fts__english__search='python programing', dicts='english')
[<Article: Python in english>]
>>> Article.objects.filter(fts__english__search='monty python', dicts='portuguese')
[<Article: Monty Python in portuguese>, <Article: Os Malucos do Circo in portuguese>]

.. note::

    Not filtering the results by it's dictionary is possible, but results won't be reliable:

    >>> Article.objects.filter(fts__english__search='python programing')
    [<Article: Python in english>]  # nothing strange
    >>> Article.objects.filter(fts__portuguese__search='python programing')
    []  # no results

.. note::

    The :class:`~pg_fts.fields.DictionaryTransform` only accepts dictionaries that are defined in options.
