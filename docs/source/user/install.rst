.. _install:

Installation of pymaketool
==========================

This part of the documentation covers the installation of pymaketool.
The first step to using any software package is getting it properly installed.

Install
-------

To install pymaketool (only support for python 3), simply run this simple command in your terminal of choice.

.. code-block:: bash

   $ pip install pymaketool


Get the Source Code
-------------------

pymaketool is actively developed on GitHub, where the code is
`always available <https://github.com/ericsonj/pymaketool.git>`_.

You can either clone the public repository

.. code-block:: bash

    $ git clone https://github.com/ericsonj/pymaketool.git

Or, download the `tarball <https://github.com/ericsonj/pymaketool/tarball/master>`_

.. code-block:: bash
    $ curl -OL https://github.com/ericsonj/pymaketool/tarball/master
    # optionally, zipball is also available (for Windows users).

Once you have a copy of the source, you can embed it in your own Python
package, or install it into your site-packages easily

.. code-block:: bash
    $ cd pymaketool
    $ python -m pip install .