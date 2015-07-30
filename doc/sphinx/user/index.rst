===============
Morphologist-UI
===============

Morphologist is a neuroimaging software dedicated to cortical analysis and sulcal morphometry. See http://brainvisa.info and :morphoproc:`the toolbox documentation in BrainVISA <categories/morphologist/category_documentation.html>`.

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

It is a simplified intercace, providing only the default parameters settings. For the sake of simplicity, there are no buttons, parameters, or other tuning which may affect processing: it is designed for "standard" processing.

Comparison with the regular Morphologist pipeline
-------------------------------------------------

* Morphologist-UI performs the processings of the classical Morphologist toolbox in BrainVISA, with a slightly modified files organization: it will write additional files for the "renormalization" step (second normalization after skull stripping to enforce the alignment robustness).

* Morphologist-UI relies on files existence to display results and re-run processing steps in case of interruptions, so files have to be written just once. This is not what the Morphologist toolbox does in BrainVISA (for historical and technical reasons). Hence the difference.

* Apart from these additional output files, Morphologist-UI and Morphologist produce the same results and are interchangeable. So if Morphologist-UI fails for some reason, it is always possible to use the clasical BrainVISA pipeline, with all its available parameters, to complete the processing.

* A restriction on file formats (images, meshes) also apply for Morphologist-UI: it can handle several formats, as Morphologist have always did, but the format is chosen globally: all files in a database should have a single same format for all images, or all meshes, others will not be recognized.


Installation
------------

Users distributions are available on http://brainvisa.info

Starting the program
--------------------

Run the executable script ``morphologist`` in the ``bin/`` directory of the BrainVisa/Morphologist distribution.

It can also be found in BrainVISA processes, in the Morphologist toolbox.

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



