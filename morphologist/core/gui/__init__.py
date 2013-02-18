import os
# XXX The qt_backend must be imported before any other qt imports (ie. anatomist)
import qt_backend
# XXX The ressources must be imported to load icons
import ressources

prefix = os.path.dirname(__file__)
ui_directory = os.path.join(prefix, 'ui')