.. django-pg-fts documentation master file, created by
   sphinx-quickstart on Mon Sep 22 15:48:58 2014.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to django-pg-fts's documentation!
=========================================

Implementation PostgeSQL for Full Text Search for django 1.7, taking advantage of new features Migrations and Custom Lookups.

Features:
---------

- FieldLookup's search, isearch, tsquery

- Ranking support with normalization, and weights using annotations

- Migrations classes to help create and remove index's, support for 'gin' or 'gist'

- Migrations classes to help create and remove of trigger's

- Multiple dictionaries support with trigger and FieldLookup's

- Support for python 2.7, 3.3 and 3.4


Contents:

.. toctree::
   :maxdepth: 4

   install
   tutorial
   migrations
   pg_fts


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

