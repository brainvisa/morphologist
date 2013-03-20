from soma import aims

from morphologist.core.formats import Format, FormatsManager


class BrainvisaFormatsManager(FormatsManager):
    _intra_analysis_acceptable_formats = set(['FLOAT', 'U8', 'ULONG', 'DOUBLE',
                                             'CDOUBLE', 'S16', 'LONG', 'S32',
                                             'LONG', 'S8', 'U16', 'CFLOAT'])

    @classmethod
    def _fill_formats_and_extensions(cls):
        available_formats = cls._create_available_volume_formats()
        for formatname in available_formats:
            if not len(formatname): continue
            extensions = cls._find_extensions_from_format(formatname)
            if len(extensions) == 0: continue
            format = Format(formatname)
            format.extensions = extensions
            cls._formats.append(format)

    # FIXME : add protected
    @classmethod
    def _create_available_volume_formats(cls):
        objects_types = aims.IOObjectTypesDictionary().objectsTypes()
        aims_volume_types = set(objects_types['Volume'])
        volume_types = aims_volume_types.intersection(\
                            cls._intra_analysis_acceptable_formats)

        formats = [item for type in volume_types \
                        for item in list(aims.IOObjectTypesDictionary.formats('Volume', type))]
        formats = sorted(set(formats))
        formats.remove('BMP')
        formats.remove('DICOM') #XXX: aims I/O are not reliable
        return formats

    @staticmethod
    def _find_extensions_from_format(formatname):
        finder = aims.Finder()
        extensions = finder.extensions(formatname)
        try:
            extensions.remove('')
        except ValueError:
            pass
        return extensions
