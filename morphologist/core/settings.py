__all__ = ['settings', 'AUTO']


import os
import copy
from configobj import ConfigObj, flatten_errors, get_extra_values
from validate import Validator


AUTO = 'auto'


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


class SettingsManager(object):
    prefix = 'morphologist/core'
    configspec = os.path.join(prefix, 'settings.configspec')
    filename = os.path.join(os.path.expanduser('~'), '.morphologist-ui.ini')

    @classmethod
    def generate_default(cls):
        settings = ConfigObj(configspec=cls.configspec)
        settings.filename = cls.filename
        validator = MorphologistConfigValidator()
        settings.validate(validator, copy=True)
        return settings

    @classmethod
    def load(cls):
        settings = cls.generate_default()
        if not os.path.exists(cls.filename):
            cls.save(settings) # save default settings
            check = True
        else:
            user_settings = ConfigObj(cls.filename, configspec=cls.configspec)
            check = cls._check_settings(user_settings)
            settings.merge(user_settings)
        settings['settings_are_valid'] = check
        return settings

    @classmethod
    def save(cls, settings):
        settings.write()

    @classmethod
    def _check_settings(cls, settings):
        validator = MorphologistConfigValidator()
        validation = settings.validate(validator, preserve_errors=True)
        settings_issues = flatten_errors(settings, validation)
        if settings_issues:
            print "Error: loading settings from file '%s'" % settings.filename
            print "The following items have wrong values:"
            for sections, key, error in settings_issues:
                sections = '/'.join(sections)
                if key is None:
                    key = '[Missing section]'
                if error == False:
                    error = 'Missing value or section.'
                print "  - %s/%s: %s" % (sections, key, error)
            return False
        extra_values = get_extra_values(settings)
        if extra_values:
            print "Error: unknown additionnal items in setting file '%s'" % \
                                                            settings.filename
            for sections, name in extra_values:
                item = '/'.join(list(sections) + [name])
                print "  -", item
            return False
        return True
     

# use facade design pattern to propose new interfaces of configobj settings
class SettingsFacade(object):
    _settings_map = {}

    def __init__(self, configobj_settings):
        self._wrapped = configobj_settings

    def save(self):
        for section, setting in self._settings_map.itervalues():
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
        return self.__class__(copy.deepcopy(self._wrapped))

    def update(self, settings_facade):
        # XXX: protected field _wrapped can be friendly access here
        self._wrapped.update(settings_facade._wrapped)


class CommandLineSettings(SettingsFacade):
    _settings_map = {
        "brainomics" : ('application', 'brainomics'),
        "mock" : ('debug', 'mock'),
     }

    def __init__(self, configobj_settings):
        super(CommandLineSettings, self).__init__(configobj_settings)
        self._read_only = False

    def __setattr__(self, attr, value):
        if self._settings_map.has_key(attr) and self._read_only:
            raise AttributeError("can't set attribute")
        else:
            super(CommandLineSettings, self).__setattr__(attr, value)

    def set_read_only(self):
        object.__setattr__(self, "_read_only", True)


class RunnerSettings(SettingsFacade):
    _settings_map = {
        'selected_processing_units_n' : ('application', 'CPUs')
    }
    def __init__(self, configobj_settings):
        super(RunnerSettings, self).__init__(configobj_settings)
        # TODO: for cpu_count(), ask Runner backend instead
        import multiprocessing
        self._total_processing_units_n = multiprocessing.cpu_count()

    @property
    def selected_processing_units_n(self):
        value = super(SettingsFacade, self).__getattr__(attr)
        if value == AUTO:
            return self._auto_selected_processing_units_n()
        else:
            return value

    def auto_select_processing_units(self):
        value = self._auto_selected_processing_units_n() 
        self.selected_processing_units_n = value
        return value

    def _auto_selected_processing_units_n(self):
        return max(1, self._total_processing_units_n - 1)

    @property
    def total_processing_units_n(self):
        return self._total_processing_units_n


class StudyEditorSettings(SettingsFacade):
    _settings_map = {
        "brainomics" : ('application', 'brainomics'),
     }

    def __init__(self, configobj_settings):
        super(StudyEditorSettings, self).__init__(configobj_settings)


class BackendSettings(SettingsFacade):
    _settings_map = {
        "vector_graphics" : ('backend', 'vector_graphics'),
        "display" : ('backend', 'display'),
        "objects" : ('backend', 'objects'),
        "formats" : ('backend', 'formats'),
     }

    def __init__(self, configobj_settings):
        super(BackendSettings, self).__init__(configobj_settings)


class TestsSettings(SettingsFacade):
    _settings_map = {
        "start_qt_event_loop" : ('debug', 'start_qt_event_loop_for_tests'),
        "mock" : ('debug', 'mock'),
     }

    def __init__(self, configobj_settings):
        super(TestsSettings, self).__init__(configobj_settings)


class Settings(object):

    def __init__(self, configobj_settings):
        self._configobj_settings = configobj_settings
        self.runner = RunnerSettings(configobj_settings)
        self.commandline = CommandLineSettings(configobj_settings)
        self.study_editor_settings = StudyEditorSettings(configobj_settings)
        self.backends = BackendSettings(configobj_settings)
        self.tests = TestsSettings(configobj_settings)

    def are_valid(self):
        return self._configobj_settings['settings_are_valid']
        

# low level internal (only this file) configobj settings
disk_settings = SettingsManager.load()
memory_settings = disk_settings.copy()

# high level client-code-oriented settings
settings = Settings(memory_settings)
