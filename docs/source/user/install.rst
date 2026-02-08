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

Installation with Poetry
------------------------

`Poetry <https://python-poetry.org/>`_ is a modern Python dependency management tool 
that provides consistent environments and simplified package management.

Install Poetry:

.. code-block:: bash

    $ curl -sSL https://install.python-poetry.org | python3 -

Add pymaketool to your project:

.. code-block:: bash

    $ poetry add pymaketool
    $ poetry install

Verify the installation:

.. code-block:: bash

    $ poetry run pymaketool -v

Setting Up a C Project with Poetry
----------------------------------

You can manage your C project's Python dependencies using Poetry for better reproducibility.

Create and set up the project:

.. code-block:: bash

    $ poetry run pynewproject CLinuxGCC
    $ cd your_project_name
    $ poetry init --name your_project_name --dependency pymaketool
    $ poetry install

Or create a **pyproject.toml** manually:

.. code-block:: toml

    [project]
    name = "your_project_name"
    version = "0.1.0"
    description = "My C project using pymaketool"
    authors = [{ name = "Your Name", email = "your@email.com" }]
    requires-python = ">=3.10"
    dependencies = ["pymaketool"]

    [build-system]
    requires = ["poetry-core>=2.0.0"]
    build-backend = "poetry.core.masonry.api"

Build using Poetry:

.. code-block:: bash

    # Clean the project
    $ poetry run make clean

    # Build the project
    $ poetry run make

    # Run the executable
    $ ./Release/your_project_name

Benefits of using Poetry:

* **Reproducible builds**: Lock files ensure the same dependencies across all machines
* **Isolated environments**: Virtual environments prevent conflicts with system packages
* **Easy CI/CD integration**: Simple commands for continuous integration pipelines
* **Dependency resolution**: Automatic resolution of compatible package versions