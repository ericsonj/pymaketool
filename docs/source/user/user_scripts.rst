.. _user_scripts:

User scripts
============

Developers can add more Python scripts and import them into _mk.py files.

.. image:: ../img/user_scripts.jpg
  :width: 300
  :alt: user_script

For example in **func.py**:

.. code-block:: python

    # File func.py

    def log(msg):
        print(msg)

**func.py** can be imported in **app_mk.py**:

.. code-block:: python

    from pymakelib.module import ModuleHandle
    import scripts.func as f


    def init(mh: ModuleHandle):
        f.log('Init module app')


    def getSrcs(mh: ModuleHandle):
        return [
            'app/app.c'
        ]


    def getIncs(mh: ModuleHandle):
        return [
            'app'
        ]

