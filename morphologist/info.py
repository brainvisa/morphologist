
version_major = 1
version_minor = 1
version_micro = 1
version_extra = ''

# Format expected by setup.py and doc/source/conf.py: string of form "X.Y.Z"
__version__ = "%s.%s.%s%s" % (version_major,
                              version_minor,
                              version_micro,
                              version_extra)
CLASSIFIERS = ['Development Status :: 4 - Beta',
               'Environment :: X11 Applications ',
               'Intended Audience :: Developers',
               'Intended Audience :: Science/Research',
               'Intended Audience :: Education',
               'Operating System :: OS Independent',
               'Programming Language :: Python',
               'Programming Language :: Python :: 2',
               'Programming Language :: Python :: 2.7',
               'Programming Language :: Python :: 3',
               'Topic :: Scientific/Engineering',
               ]


description = 'Morphologist UI: graphical interface for Morphologist (http://brainvisa.info)'

long_description = """
===============
Morphologist UI
===============

graphical interface for Morphologist (http://brainvisa.info): brain segmentation from T1 MRI images, sulci extraction and morphometry.
"""

# versions for dependencies
SPHINX_MIN_VERSION = '1.0'
SOMA_WORKFLOW_MIN_VERSION = "2.8.0"
SOMA_BASE_MIN_VERSION = "4.6.0"
CAPSUL_MIN_VERSION = "2.1.0"

# Main setup parameters
NAME = 'morphologist-ui'
PROJECT = 'morphologist'
ORGANISATION = "CEA"
MAINTAINER = "CEA"
MAINTAINER_EMAIL = ""
DESCRIPTION = description
LONG_DESCRIPTION = long_description
URL = "http://brainvisa.info/morphologist-ui"
DOWNLOAD_URL = "http://brainvisa.info"
LICENSE = "CeCILL-B"
CLASSIFIERS = CLASSIFIERS
AUTHOR = "Morphologist UI developers"
AUTHOR_EMAIL = ""
PLATFORMS = "OS Independent"
PROVIDES = ["morphologist-ui"]
REQUIRES = [
    "soma-workflow>=%s" % SOMA_WORKFLOW_MIN_VERSION,
    "capsul>=%s" % CAPSUL_MIN_VERSION,
    "soma-base>=%s" % SOMA_BASE_MIN_VERSION,
    # anatomist
    # morphologist
    # axon
]
EXTRA_REQUIRES = {
    "doc": ["sphinx>=" + SPHINX_MIN_VERSION],
}

