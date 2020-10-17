.. _user_scripts:

User scripts
============

The developer can add more python scripts and import into _mk.py files.

.. image:: ../img/user_scripts.jpg
  :width: 300

For example in **func.py**:

.. code-block:: python

    # File func.py

    def log(msg):
        print(msg)

The **func.py** can import in **app_mk.py**:

.. code-block:: python

    from pybuild.Module import ModuleHandle
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

