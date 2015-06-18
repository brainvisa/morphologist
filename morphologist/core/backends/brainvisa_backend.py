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
                        for item in
                            list(aims.IOObjectTypesDictionary.formats(
                                'Volume', type))]
        # manage soma-io formats
        objects_types = aims.carto.IOObjectTypesDictionary().readTypes()
        formats += [item for type, items in objects_types.iteritems()
                    if type.startswith('carto_volume of ')
                        and type[16:] in cls._intra_analysis_acceptable_formats
                    for item in items]
        formats = sorted(set(formats))
        formats.remove('BMP')
        return formats

    @staticmethod
    def _find_extensions_from_format(formatname):
        finder = aims.Finder()
        extensions = finder.extensions(formatname)
        try:
            extensions.remove('')
        except ValueError:
            pass
        # also look in soma-io
        for data_type in \
                BrainvisaFormatsManager._intra_analysis_acceptable_formats:
            cls_name = 'FormatDictionary_Volume_%s' % data_type
            cls = getattr(aims.carto, cls_name, None)
            if cls is None:
                continue
            exts = cls.readExtensions()
            extensions += [ext for ext, formats in exts.iteritems()
                           if ext != '' and formatname in formats]
        extensions = list(set(extensions))
        return extensions
