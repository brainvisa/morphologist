from morphologist.core.utils import remove_all_extensions


class Subject(object):
    DEFAULT_GROUP = "group1"
    
    def __init__(self, name, groupname, filename):
        self.name = name 
        self.groupname = groupname
        self.filename = filename

    @classmethod
    def from_filename(cls, filename, groupname=DEFAULT_GROUP):
        subjectname = cls._define_subjectname_from_filename(filename)
        return cls(subjectname, groupname, filename)

    @staticmethod
    def _define_subjectname_from_filename(filename):
        return remove_all_extensions(filename)
 
    def id(self):
        return self.groupname + "-" + self.name
        
    def __repr__(self):
        s = "(%s, %s, %s)" % (self.groupname, self.name, self.filename)
        return s

    def __str__(self):
        return self.id()
    
    def __eq__(self, other):
        for attr in ['name', 'groupname', 'filename']:
            value = self.__getattribute__(attr)
            other_value = other.__getattribute__(attr)
            if value != other_value:
                return False
        return True

    def __ne__(self, other):
        return not self.__eq__(other)

    def serialize(self):
        serialized = {}
        serialized['subjectname'] = self.name
        serialized['groupname'] = self.groupname
        serialized['filename'] = self.filename
        return serialized

    @classmethod
    def unserialize(cls, serialized):
        subject = cls(name=serialized['subjectname'], 
                      groupname=serialized['groupname'],
                      filename=serialized['filename'])
        return subject

    def copy(self):
        return Subject(self.name, self.groupname, self.filename)
