import os
from configobj import ConfigObj, flatten_errors, get_extra_values
from validate import Validator


class MorphologistConfigValidator(Validator):
    AUTO = 'auto'
    AUTO_PREFIX = 'auto_or_'

    def __init__(self, *args, **kwargs):
        super(MorphologistConfigValidator, self).__init__(*args, **kwargs)

    def check(self, check, value, missing):
        if check.startswith(self.AUTO_PREFIX):
            if missing:
                value = self.AUTO
            if value == self.AUTO:
                return self.AUTO
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
        if os.path.exists(cls.filename):
            settings = ConfigObj(cls.filename, configspec=cls.configspec)
            check = cls._check_settings(settings)
        else:
            settings = cls.generate_default()
            cls.save(settings)
            check = True
        settings['settings_validation'] = check
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
     

settings = SettingsManager.load()
