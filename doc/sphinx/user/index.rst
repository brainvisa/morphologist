===============
Morphologist-UI
===============

Morphologist is a neuroimaging software dedicated to cortical analysis and sulcal morphometry. See http://brainvisa.info.

Morphologist-UI is a user-friendly interface to the Morphologist pipeline. It is based on the same processing chain, and offers interactive visualization using `anatomist <http://brainvisa.info>`_.

.. image:: _static/morphologist-ui.jpg

It allows:

* MRI segmentation
* Brain sulci extraction and automatic identification
* Sulcal morphometry
* Fast, interactive visualization of results to allow visual QC

Featuring:

* Runs in parallel on one or a set of MRI images
* Fast: about 10-15 minutes per subject for the full pipeline
* Robust: Morphologist has processed several tenths of thousands of brains
* Possibly using a remote processing cluster

Users
=====

Installation
------------

Users distributions are (will be) available on http://brainvisa.info

Starting the program
--------------------

Run the executable script ``morphologist-ui.py`` in the ``bin/`` directory of the BrainVisa/Morphologist distribution.

Configuration
-------------

Use the appropriate menu to setup your data locations and other options.

Processing
----------

Process several or all subjects. Run in parallel using `Soma-Workflow <http://brainvisa.info/soma/soma-workflow/index.html>`_.
Results appear in the display window at the time they are available.


Developers
==========

* :morphouidev:`Developers documentation <index.html>`


.. toctree::
  :hidden:



