Ranking
=======

.. .. module:: pg_fts.ranks
..    :synopsis: Built-in rank types.

RankBase options
****************

The following arguments are available to all FTSRank types

``lookup``
----------

.. attribute:: FTSRank.lookup

The :class:`~pg_fts.fields.TSVectorField` and its available lookup's ``search``, ``isearch`` and ``tsquery``.

Will raise exception if lookup isn't valid.

.. seealso::

    For :class:`~pg_fts.fields.TSVectorField` lookups check :doc:`TSVectorField lookups</tsvector_field>`

``normalization``
-----------------

.. attribute:: FTSRank.normalization

A list or tuple of integers with the normalization values, can be used a bit mask
``[1,2]`` will be converted to ``1|2`` in sql.


Accepted Values = 0, 1, 2, 4, 8, 16, 32

Default is PostgresSQL function default.

Will raise exception if ``normalization`` isn't valid.

``weights``
-----------

.. attribute:: FTSRank.weights

A list or tuple of integers/floats [D-weight, C-weight, B-weight, A-weight] with the weight values ``[0.1, 0.2, 0.4, 1]`` will be converted to ``{0.1, 0.2, 0.4, 1.0}`` in sql.

Default is PostgresSQL function default.

Will raise exception if ``weights`` isn't valid.

.. seealso::
    
    More about ``normalization`` and ``weights`` check PostgreSQL documentation :pg_docs:`12.3.3. Ranking Search Results <textsearch-controls.html#TEXTSEARCH-RANKING>`


``FTSRank``
***********

.. class:: FTSRank(**options)

Uses PostgreSQL ``ts_rank`` function, ranks on frequency of matching lexemes.

Examples:

Search and order by rank::

    Article.objects.annotate(
        rank=(FTSRank(fts__search='once upon a time'))).order_by('-rank')

Search and with normalization::

    Article.objects.annotate(
        normalized=(FTSRank(
            fts__search='once upon a time',
            noramlization=(1,2)
        ))).order_by('-normalized')


``FTSRankCd``
*************

.. class:: FTSRankCd(**options)

Uses PostgreSQL ``ts_rank_cd`` function, ranks over cover density.

Usage is the same as FTSRank, just with this class.

Multiple dictionaries support
*****************************

For this case there are two classes ``FTSRankDictionay``, ``FTSRankCdDictionary``.

The usage is the same as normal ``FTSRank`` or ``FTSRankCd``, was added the special support for lookups with dictionary transformation.
