#!/usr/bin/env python2
import os
import re

from optparse import OptionParser


def main():
    parser = OptionParser(usage='concat csv file inputs\n'
                            '%prog -o output csv1 csv2 ...')
    parser.add_option('-o', '--output', dest='output_filepath',
        action='store', default=None,
        help='output filename: concatenation of all inputs')
    options, args = parser.parse_args()
    if len(args) == 1:
        parser.error('You must supply at least on csv file.')
    if options.output_filepath is None:
        parser.error('You must supply an output (--output).')
    concat_csv(options.output_filepath, args)


def concat_csv(output_filepath, input_filepaths):
    first_file = True
    fd_out = open(output_filepath, 'w')
    for input_filepath in input_filepaths:
        # XXX: it would be better to pass these information to the script
        # warning: high coupling with specific parameter template choices !
        subjectname, is_normalized = \
            subject_and_normalize_status_from_filepath(input_filepath)
        fd_in = open(input_filepath, 'r')
        lines = fd_in.readlines()
        header = lines[0]
        lines = lines[1:]
        if first_file:
            fd_out.write('subject normalized ' + header)
            first_file=False
        for line in lines:
            fd_out.write('%s %d ' % (subjectname, is_normalized))
            fd_out.write(line)


def subject_and_normalize_status_from_filepath(filepath):
    filename = os.path.basename(filepath)
    regexp = re.compile('(left|right)_%s_morphometry_%s.dat' % \
        ('(?P<normalized>(\w+))', '(?P<subjectname>\w+)'))
    match = regexp.match(filename)
    groupdict = match.groupdict()
    subjectname = groupdict['subjectname']
    if groupdict['normalized'] == 'normalized':
        is_normalized = 1
    else:
        is_normalized = 0
    return subjectname, is_normalized
        

if __name__ == '__main__': main()
