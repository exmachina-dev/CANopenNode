# -*- coding: utf-8 -*-

import configparser
import logging

from utils import str_to_hex
import OD
import OD_cexport

logger = logging.getLogger(__name__)


def OD_from_file(fd):
    config = configparser.ConfigParser()
    config.read_file(fd)

    od = OD.ObjectDirectory()

    for section in config.sections():
        if 'feature.' in section:
            feature = OD.Feature(name=section.replace('feature.', ''),
                                 **config[section])
            od.add_feature(feature)
            config.remove_section(section)

    for section in config.sections():
        if '.' not in section:
            obj = OD.Object(index=str_to_hex(section), **config[section])
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
    parser.add_argument('--debug', '-d', action='store_true',
                        help='display raw data')

    args = parser.parse_args()

    od = OD_from_file(args.file)

    if args.command == 'tree':
        od.tree()
    elif args.command == 'count':
        l = len(od.objects)
        for o in od.objects.values():
            l += len(o.children)

        print('Objects in this file: {:d}'.format(l))
    elif args.command == 'generate_files':
        cex = OD_cexport.CExport(od)
        cex.populate()

        if args.debug:
            # print('# INFO', *cex.OD_info, sep='\n')

            # print('# MACROS', *cex.OD_H_macros, sep='\n')
            print('# TYPEDEFS', *cex.OD_H_typedefs, sep='\n')
            print('# H_RAM', *cex.OD_H_RAM, sep='\n')
            # print('# H_EEPROM', *cex.OD_H_EEPROM, sep='\n')
            print('# H_ROM', *cex.OD_H_ROM, sep='\n')
            print('# H_aliases', *cex.OD_H_aliases, sep='\n')

            # print('# initRAM', *cex.OD_C_initRAM, sep='\n')
            # print('# initEEPROM', *cex.OD_C_initEEPROM, sep='\n')
            # print('# initROM', *cex.OD_C_initROM, sep='\n')
            # print('# RECORDS', *cex.OD_C_records, sep='\n')

            # print('# C_FUNCTIONS', *cex.OD_C_functions, sep='\n')
            # print('# C_OD', *cex.OD_C_OD, sep='\n')

            # print('# OD_NAMES', *cex.OD_names, sep='\n')
        else:
            print(cex.h_file)
            print(cex.c_file)
