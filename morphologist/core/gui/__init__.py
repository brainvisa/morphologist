from __future__ import absolute_import
import os
import sys

import six

# XXX The qt_backend must be imported before any other qt imports (ie. anatomist)
from . import qt_backend
# XXX The resources must be imported to load icons
if qt_backend.qt_backend.get_qt_backend() == 'PyQt5':
    from . import resources_qt5 as resources
elif six.PY3:
    from . import resources_py3 as resources
from . import resources

prefix = os.path.dirname(__file__)
ui_directory = os.path.join(prefix, 'ui')
