===============
ShpEscape
===============

.. contents:: Contents

Introduction
=============

ShpEscape allows users to upload shapefiles for import into Google Fusion
Tables.  It currently uses GeoDjango (you will want a spatially enabled db,
and associated dependencies like GEOS, GDAL, Proj4).

The Site
--------

A demo site can be found at http://www.shpescape.com

Installation
============

.. parsed-literal::

    cd <installation-directory>
    virtualenv env-shpescape
    source env-shpescape/bin/activate
    hg clone https://shpescape.googlecode.com/hg/ shpescape 
    cd shpescape
    pip install -r requirements.txt

Customizing Local Settings
==========================

Create a local_settings.py, and add in the database settings and all the other
local_settings parameters noted in the main settings.py.  Then do::

    python manage.py syncdb
    
Starting the development server
===============================

    python manage.py runserver

    #also run the background task that processes uploads
    python shapeft/ft_insert.py . settings &


Credits
=======

This application was written, in a hurry, by Josh Livni (jlivni@google.com).
See the LICENSE file for information on the license.
