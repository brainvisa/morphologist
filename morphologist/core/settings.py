from __future__ import print_function

__all__ = ['settings', 'AUTO']


import os
import copy
import multiprocessing
from configobj import ConfigObj, flatten_errors, get_extra_values
from validate import Validator


AUTO = 'auto'


class Settings(object):
    disk_configobj = None
    _cfg_handler = None

    @classmethod
    def _init_class(cls):
        cls._cfg_handler = ConfigobjSettingsHandler()

    def load(self):
        if Settings._cfg_handler is None:
            Settings._init_class()
        Settings.disk_configobj = Settings._cfg_handler.load()
        self._reset_on_configobj_changed()

    def load_default(self):
        if Settings._cfg_handler is None:
            Settings._init_class()
        Settings.disk_configobj = Settings._cfg_handler.generate_default()
        self._reset_on_configobj_changed()

    def _reset_on_configobj_changed(self):
        self._memory_configobj = self._cfg_handler.copy(\
                                Settings.disk_configobj)
        self.runner = RunnerSettings(self._memory_configobj)
        self.commandline = CommandLineSettings(self._memory_configobj)
        self.study_editor = StudyEditorSettings(self._memory_configobj)
        self.backends = BackendSettings(self._memory_configobj)
        self.tests = TestsSettings(self._memory_configobj)

    def are_valid(self):
        return self._cfg_handler.check_settings(self._memory_configobj)

    def save(self):
        self._cfg_handler.save(cls.disk_configobj)


class ConfigobjSettingsHandler(object):
    filepath = os.path.join(os.path.expanduser('~'), '.morphologist-ui.ini')
    _prefix = os.path.dirname(__file__)
    _configspec = os.path.join(_prefix, 'settings.configspec')

    @classmethod
    def generate_default(cls):
        settings = ConfigObj(configspec=cls._configspec)
        settings.filename = cls.filepath
        validator = MorphologistConfigValidator()
        settings.validate(validator, copy=True)
        return settings

    @classmethod
    def load(cls):
        settings = cls.generate_default()
        if not os.path.exists(cls.filepath):
            cls.save(settings) # save default settings
        else:
            user_settings = ConfigObj(cls.filepath, configspec=cls._configspec)
            settings.merge(user_settings)
        return settings

    @staticmethod
    def save(settings):
        settings.write()

    @staticmethod
    def copy(settings):
        copy_settings = ConfigObj(configspec=settings.configspec)
        copy_settings.filename = settings.filename
        # XXX: use a deepcopy since settings contains dictionnary references
        copy_settings.update(copy.deepcopy(settings))
        return copy_settings

    @staticmethod
    def check_settings(settings):
        validator = MorphologistConfigValidator()
        validation = settings.validate(validator, preserve_errors=True)
        settings_issues = flatten_errors(settings, validation)
        if settings_issues:
            print("Error: loading settings from file '%s'" % settings.filename)
            print("The following items have wrong values:")
            for sections, key, error in settings_issues:
                sections = '/'.join(sections)
                if key is None:
                    key = '[Missing section]'
                if error == False:
                    error = 'Missing value or section.'
                print("  - %s/%s: %s" % (sections, key, error))
            return False
        extra_values = get_extra_values(settings)
        if extra_values:
            print("Error: unknown additionnal items in setting file '%s'" %
                  settings.filename)
            for sections, name in extra_values:
                item = '/'.join(list(sections) + [name])
                print("  -", item)
            return False
        return True


class MorphologistConfigValidator(Validator):
    AUTO_PREFIX = 'auto_or_'

    def __init__(self, *args, **kwargs):
        super(MorphologistConfigValidator, self).__init__(*args, **kwargs)

    def check(self, check, value, missing):
        if check.startswith(self.AUTO_PREFIX):
            if missing:
                value = AUTO
            if value == AUTO:
                return AUTO
            check = check.replace(self.AUTO_PREFIX, "", 1)
        return super(MorphologistConfigValidator, self).check(check,
                                                    value, missing)


# use facade design pattern to propose new interfaces of configobj settings
class SettingsFacade(object):
    _settings_map = {}

    def __init__(self, configobj_settings):
        self._wrapped = configobj_settings

    def save(self):
        disk_settings = Settings.disk_configobj
        for section, setting in self._settings_map.itervalues():
            # XXX: this repr [section][setting] is a specificity of configobj
            disk_settings[section][setting] = self._wrapped[section][setting]
        disk_settings.write()

    def __setattr__(self, attr, value):
        if not self._settings_map.has_key(attr):
            return super(SettingsFacade, self).__setattr__(attr, value)
        section, setting = self._try_find_attr(attr)
        self._wrapped[section][setting] = value

    def __getattr__(self, attr):
        if not self._settings_map.has_key(attr):
            return super(SettingsFacade, self).__getattribute__(attr)
        section, setting = self._try_find_attr(attr)
        # XXX: this repr [section][setting] is a specificity of configobj
        return self._wrapped[section][setting]

    def _try_find_attr(self, attr):
        try:
            section, setting = self._settings_map[attr]
        except KeyError:
            cls = super(SettingsFacade, self).__getattribute__('__class__')
            msg = "'%s' object has no attribute '%s'" % (cls.__name__, attr)
            raise AttributeError(msg)
        else:
            return section, setting

    def __dir__(self):
        proxied_attr = self._settings_map.keys()
        return dir(self.__class__) + proxied_attr

    def copy(self):
        # make a copy as expected by a client which may ignore the fact that
        # this instance is a facade on another object
        configobj = ConfigobjSettingsHandler.copy(self._wrapped)
        return self.__class__(configobj)

    def update(self, settings_facade):
        # XXX: protected field _wrapped can be friendly access here
        self._wrapped.update(settings_facade._wrapped)


class CommandLineSettings(SettingsFacade):
    _settings_map = {
        "brainomics" : ('application', 'brainomics'),
        "mock" : ('debug', 'mock'),
     }


class RunnerSettings(SettingsFacade):
    _settings_map = {
        'selected_processing_units_n' : ('application', 'CPUs')
    }

    @property
    def selected_processing_units_n(self):
        attr = 'selected_processing_units_n'
        value = super(RunnerSettings, self).__getattr__(attr)
        if value == AUTO:
            value = self._auto_selected_processing_units_n()
            return AutoOrInt(value, auto=True)
        else:
            return AutoOrInt(value, auto=False)

    def _auto_selected_processing_units_n(self):
        total_processing_units_n = multiprocessing.cpu_count()
        return max(1, total_processing_units_n - 1)


class AutoOrInt(int):

    def __new__(cls, value, auto=False):
        i = int.__new__(cls, value)
        i._is_auto = auto
        return i

    @property
    def is_auto(self):
        return self._is_auto


class StudyEditorSettings(SettingsFacade):
    _settings_map = {
        "brainomics" : ('application', 'brainomics'),
     }


class BackendSettings(SettingsFacade):
    _settings_map = {
        "vector_graphics" : ('backends', 'vector_graphics'),
        "display" : ('backends', 'display'),
        "objects" : ('backends', 'objects'),
        "formats" : ('backends', 'formats'),
     }


class TestsSettings(SettingsFacade):
    _settings_map = {
        "start_qt_event_loop" : ('debug', 'start_qt_event_loop_for_tests'),
        "mock" : ('debug', 'mock'),
     }


settings = Settings()
settings.load()
