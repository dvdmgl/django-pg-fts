.. django-pg-fts documentation master file, created by
   sphinx-quickstart on Mon Sep 22 15:48:58 2014.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to django-pg-fts's documentation!
=========================================

Implementation PostgeSQL for Full Text Search for Django >= 1.7

Features:
---------

- FieldLookup's search, isearch, tsquery

- Annotations (fake aggregates) for Ranking results with normalization

- Migrations classes to help create and remove index's, support for 'gin' or 'gist'

- Migrations classes to help create and remove of trigger's for updating and inserting

- Multiple dictionaries support with trigger and FieldLookup's


Contents:

.. toctree::
   :maxdepth: 4

   install
   tutorial
   pg_fts


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
