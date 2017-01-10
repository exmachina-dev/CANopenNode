# -*- coding: utf-8 -*-

import configparser
import logging

import OD_types
import OD

logger = logging.getLogger(__name__)


def str_to_hex(string):
    return int('0x' + string, base=16)


def OD_from_file(fd):
    config = configparser.ConfigParser()
    config.read_file(fd)

    od = OD.ObjectDirectory()

    for section in config.sections():
        if '.' not in section:
            obj = OD.Object(**config[section])
            od.add_object(str_to_hex(section), obj)

    for section in config.sections():
        if '.' in section:
            index, subindex = map(str_to_hex, section.split('.'))
            obj = od.objects.get(index)
            if not obj:
                logger.warn('Missing index {:x} in OD, skipping {} object.'
                            .format(index, section))
            else:
                obj.add_child(subindex, **config[section])

    return od

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='''
        ODE is an Object Dictionnary Editor''')
    parser.add_argument('command', help='command to execute')
    parser.add_argument('--file', '-f', type=argparse.FileType('r'),
                        help='the file to read from')

    args = parser.parse_args()

    od = OD_from_file(args.file)

    if args.command == 'tree':
        od.tree()
    elif args.command == 'count':
        l = len(od.objects)
        for o in od.objects.values():
            l += len(o.children)

        print('Objects in this file: {:d}'.format(l))
