.. _install:

Installation of pymaketool
==========================

This part of the documentation covers the installation of pymaketool.
The first step to using any software package is getting it properly installed.


Install
-------

To install pymaketool, simply run this simple command in your terminal of choice::

    $ pip install git+https://github.com/ericsonj/pymaketool.git

Get the Source Code
-------------------

pymaketool is actively developed on GitHub, where the code is
`always available <https://github.com/ericsonj/pymaketool.git>`_.

You can either clone the public repository::

    $ git clone https://github.com/ericsonj/pymaketool.git

Or, download the `tarball <https://github.com/ericsonj/pymaketool/tarball/master>`_::

    $ curl -OL https://github.com/ericsonj/pymaketool/tarball/master
    # optionally, zipball is also available (for Windows users).

Once you have a copy of the source, you can embed it in your own Python
package, or install it into your site-packages easily::

    $ cd pymaketool
    $ python -m pip install .