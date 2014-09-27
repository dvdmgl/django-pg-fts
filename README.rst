=============
django-pg-fts
=============

Implementation PostgeSQL for Full Text Search for Django >= 1.7

Features:

- FieldLookup's search, isearch, tsquery

- Ranking support with annotations results with normalization

- Migrations classes to help create and remove index's, support for 'gin' or 'gist'

- Migrations classes to help create and remove of trigger's

- Multiple dictionaries support with trigger and FieldLookup's

- Support for python 2.7, 3.3 and 3.4


With multiple dictionary support, index and trigger migrations

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

Install using pip from source::

    pip install .

Or using setup.py::

    python setup.py


.. caution::

    **USE AT YOUR OWN RISK**, django-pg-fts is at a very early stage of development



