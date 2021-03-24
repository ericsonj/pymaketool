.. _install:

Installation of pymaketool
==========================

This part of the documentation covers the installation of pymaketool.
The first step to using any software package is getting it properly installed.

Ubuntu/debian
-------------

.. code-block:: bash

    $ sudo apt install -y python3 python3-pip python3-gi python3-gi-cairo gir1.2-gtk-3.0 git time zip
    $ pip3 install pymaketool

Fedora
------

.. code-block:: bash

    $ sudo dnf install python3-gobject gtk3
    $ sudo dnf install python3-pip
    $ pip3 install pymaketool

Arch Linux
----------

.. code-block:: bash

    $ sudo pacman -S python-gobject gtk3
    $ sudo pacman -S python-pip
    $ pip install pymaketool

macOS
-----

.. code-block:: bash

    $ brew install pygobject3 gtk+3
    $ brew install python3
    $ pip3 install pymaketool

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