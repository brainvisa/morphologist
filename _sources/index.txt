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

* For this and other reasons, Morphologist-UI does not use nor feed BrainVisa databases, so if you are to use the "regular" brainvisa after running Morphologist-UI, you should create or update an appropriate database for the study directory.

* Apart from these additional output files, Morphologist-UI and Morphologist produce the same results and are interchangeable. So if Morphologist-UI fails for some reason, it is always possible to use the clasical BrainVISA pipeline, with all its available parameters, to complete the processing.

* A restriction on file formats (images, meshes) also apply for Morphologist-UI: it can handle several formats, as Morphologist have always did, but the format is chosen globally: all files in a database should have a single same format for all images, or all meshes, others will not be recognized.


Installation
------------

* Users distributions are available on http://brainvisa.info
* The normalization step may make use of external software, that has to be installed separately. If none is installed, the normalization defaults to the AimsMIRegister (mutual informaton) method, which is not the best tested one and might suffer from robustness issues. If installed and configured (see configuration options), the following software may be used instead, in that order:

    * `SPM (FIL, UK) <http://www.fil.ion.ucl.ac.uk/spm/>`_. It needs to be installed separately and setup in Morphologist configuration. SPM8 or SPM12 are supported, both with either the regular matlab version or the *standalone* compiled one.
    * `FSL flirt (FMRIB, UK) <http://fsl.fmrib.ox.ac.uk/fsl>`_. It needs to be installed separately and setup in Morphologist configuration.
    * Baladin (Inria, France). You will probably not use it, since this software is not freely available.


Starting the program
--------------------

Run the executable script ``morphologist`` in the ``bin/`` directory of the BrainVisa/Morphologist distribution.

It can also be found in BrainVISA processes, in the Morphologist toolbox.


Configuration
-------------

There are actually three configuration sets in Morphologist-UI.

* One is the :axonusr:`BrainVisa configuration (preferences) <axon_manual.html#preferences-window>`, which have to be setup since BrainVisa processes are still running under the hood. They are accessed via the **Settings / BrainVISA configuration** menu, or from the brainvisa software itself (it is the same configuration).
  Especially, external software configuration (SPM, FSL) should be configured there.

* Other options are **Morphologist study configuration**. They include description of the data to be processed (subjects, images...), and also a few processing options which are managed by `CAPSUL <http://neurospin.github.io/capsul/>`_, the future new pipelining system which will replace BrainVISA internals in the future.

.. Some of these options are redundant with BrainVisa ones, and are linked to them.

These configuration options are linked to the "study" directory: a study contains all needed configuration, and two different studies may have completely different configurations.

So, see the next section, :ref:`Study`.

* Last, the **Calculations settings** allow to select the computing resource and processors to be used for calculation (**Settings / Calculations** menu). It should be noted that for non-local computing resources, resources have to be setup and declared in :somaworkflow:`soma-workflow configuration <install_config.html>` first.


Study
-----

A study is both the working data directory and all configuration settings needed to run the processings.

Configuration
+++++++++++++

Configuration options include:

* **Study directory**: where all data will be stored and processed, and the study file (configuration, data list) will be stored.

* **Volumes and meshes formats**: file formats used during processing. If these formats are changed after data have been written, all existing data will be converted to the new formats.

* **Computing resource**: for processing distribution. It defaults to the local machine, but computing resources configured in Soma-Workflow may be used. They have to be setup in soma-workflow config first. See `Soma-Workflow documentation <http://brainvisa.info/soma/soma-workflow/index.html>`_.

Subjects list
+++++++++++++

Subjects may be added or removed from a study.

New subjects will be imported (copied into the study directory).

Study importation
+++++++++++++++++

This option enables to create a complete study from a directory tree containing organized data. It may be a BrainVisa database directory, or a directory with a different organization (well, this is not supported yet, actually...).

With BrainVisa databases, subjects may be either used in-place (reusing the existing database directory to work in it and share data with BrainVisa/Morphologist), or by copying raw T1 images in a new study directory.


Processing
----------

Process several or all subjects. Run in parallel using `Soma-Workflow <http://brainvisa.info/soma/soma-workflow/index.html>`_.
Results appear in the display window at the time they are available.

Processing steps currently running are visible in the subjects state (right panel in the interface). It is also always possible to monitor the workflow execution via the :somaworkflow:`soma_workglow_gui <gui.html>` program.


Troubleshooting
---------------

Morphologist-UI is a very simplified interface for running Morphologist analyses, and provides no options or tuning in processing steps. When things go wrong on some images, the simplified user interface will not allow users to fix problems and re-run the processings with modified settings.

At least not for now.

In this case, users should use the older (and complete) BrainVisa toolbox to overcome problems: as it is compatible, and provides many processing options, it is possible to run specific steps with modified settings using BrainVisa.


Current state of Morphologist-UI
--------------------------------

This is a first release of Morphologist-UI. It currently supports the main segmentation steps, sulci extraction, and sulcal morphometric measurements extraction. The morphometric step is whole brain, and there is currently no choice and no statistical analysis provided.

In the future, Morphologist-UI will be extended for inter-subject statistical analysis on sulcal morphometric features.

Other improvements in specialized steps visualization windows are planed, especially for processing parameters edition, and manual correction of processed data, as in BrainVisa editors.


Use cases
---------

See My BrainVISA processed data using Morphologist-UI
+++++++++++++++++++++++++++++++++++++++++++++++++++++

* Run ``morphologist``
* Use the **Study / Import** option. Use the BrainVisa database directory, keeping files in place (leave the "Create the study in this directory" option ON).
* In the study specification, make sure you set the same files formats as the ones which were used in brainvisa.
* When the study is validated, you should see the existing data.

Reprocess Morphologist-UI results using the BrainVisa Morphologist
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

* Run ``brainvisa``
* In the **Preferences**, setup a database to be the study directory of Morphologist-UI.
* If it already existed, you will have to update the database (using the pocess **Data management / Update databases**, if not already prompted to do so).
* That's it, you should see the data.


Developers
==========

* :morphouidev:`Developers documentation <index.html>`


.. toctree::
  :hidden:



