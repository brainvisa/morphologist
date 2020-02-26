from __future__ import absolute_import
import os

class StepHelp(object):
    ''' Abstract class '''

    def __init__(self):
        self.name = 'unnamed step'
        self.description = ""
        self.help_message = ""

