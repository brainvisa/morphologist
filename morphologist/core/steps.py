import os

from morphologist.core.analysis import Parameters


class StepHelp(object):
    ''' Abstract class '''

    def __init__(self):
        self.name = 'unnamed step'
        self.description = ""
        self.help_message = ""

