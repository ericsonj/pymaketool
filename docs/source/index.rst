.. pymaketool documentation master file, created by
   sphinx-quickstart on Wed Oct  7 18:19:16 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

pymaketool
======================================

Release v\ |version|. (:ref:`Installation <install>`)

**pymaketool** is an elegant and simple tool to generate a C project with GNU Make files. 

----------------

**Behold, the power of pymaketool**::

   # app_mk.py
   from pymaketool.Module import ModuleHandle

   def getSrcs(m: ModuleHandle):
      return m.getAllSrcsC()
   
   def getIncs(m: ModuleHandle):
      return m.getAllIncsC()

**pymaketool** allow to you create C projects with anything structure extremely easily.
Use Eclipse IDE for open and edit your project, pymaketool generates the necessary files for this.

.. image:: ../../img/pymaketool.jpg
  :width: 450

.. toctree::
   :maxdepth: 2
   
   user/install

.. Indices and tables
.. ==================

.. * :ref:`genindex`
.. * :ref:`modindex`
.. * :ref:`search`
