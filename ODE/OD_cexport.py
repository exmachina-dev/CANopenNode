# -*- coding: utf-8 -*-

import logging
from collections import defaultdict

from OD import ObjectDirectory

# from OD_types import MemoryType as _MT
from OD_types import DataType as _DT
from OD_types import ObjectType as _OT
# from OD_types import AccessType as _AT
# from OD_types import PDOMapping as _PM

from OD_cfiles import CO_OD_C, CO_OD_H

lg = logging.getLogger(__name__)


class CExport(object):
    def __init__(self, od):
        if not isinstance(od, ObjectDirectory):
            raise TypeError('od must be an {} instance.'.format(type(ObjectDirectory)))

        self.OD_info = defaultdict(lambda: '???',)
        self.OD_info['reference'] = ''

        self.OD_H_macros = []
        self.OD_H_typedefs = []
        self.OD_H_RAM = []
        self.OD_H_EEPROM = []
        self.OD_H_ROM = []
        self.OD_H_aliases = []

        self.OD_C_initRAM = []
        self.OD_C_initEEPROM = []
        self.OD_C_initROM = []
        self.OD_C_records = []

        self.OD_C_functions = []
        self.OD_C_OD = []

        self.OD_names = []
        self.OD_device_info = ''

        self._populated = False

        self.combined_objects = {}

        self.OD = od

    def populate(self):
        self._populated = True

        self.gen_features()
        self.gen_objects()

    def export_to(self, **kwargs):
        if not self.is_populated:
            self.populate()

    def gen_features(self):
        for fname in self.OD.features:
            feature = self.OD.features[fname]
            aobjs = tuple(feature.indexes)

            for index in aobjs:
                if index in self.OD.objects:
                    self.OD.objects[index].add_feature(feature)

            if len(aobjs) > 16:
                aobjs_comment = '// Associated objects from \
                                {:#x} to {:#x} ({:#x})' \
                                .format(aobjs[0], aobjs[-1], len(aobjs))
            elif len(aobjs):
                aobjs_comment = '// Associated objects: {}'.format(
                    ', '.join(('{:#x}'.format(x) for x in aobjs)))
            else:
                aobjs_comment = ''

            self.OD_H_macros.append('    #define {:<25} {:<4}    {}'.format(
                'CO{0.OD_info[reference]}_NO_{1.macro_name}'
                .format(self, feature), feature.value, aobjs_comment))

    def gen_objects(self):

        # CO_ODF(void*, UINT16…)
        self.OD_C_functions.append(
            'UNSIGNED32 CO_ODF{0.OD_info[reference]}(void*, UNSIGNED16, '
            'UNSIGNED8, UNSIGNED16*, UNSIGNED16, UNSIGNED8, void*, const void*);'
            ''.format(self))

        for index, obj in self.OD.objects.items():
            var = {}

            _brackets = False

            ot = obj.object_type
            odt = obj.data_type
            omt = obj.memory_type
            odi = self.OD_info

            ocname = obj.uid
            ocdt = obj.cdata_type
            if ot is not _OT.RECORD:
                oclen = obj.clen
                ocvalue = obj.cvalue

            # Check if a custom function is defined
            if obj.access_function_name:
                # TODO: Add custom function
                # self.add_function(
                #     'UNSIGNED32 {0.access_function_name}(void*, UNSIGNED16, \
                #     UNSIGNED8, UNSIGNED16*, UNSIGNED16, UNSIGNED8, void*, \
                #     const void*);'.format(obj))
                pass
            elif obj.access_function_precode or obj.access_function_postcode:
                pass    # TODO: Add custom code functions
            else:
                obj.access_function_name = 'CO_ODF'

            print('{0.index:#x} {0.uid} c{0.is_combined:d} f{0.is_first:d} {0.feature}'.format(obj))
            # First check parameter consistency across combined objects
            if obj.is_combined:
                if not obj.is_first:
                    fobj = self.OD.objects[obj.first_index]
                    try:
                        if fobj.object_type != obj.object_type:
                            raise ValueError('object_type')
                        if fobj.memory_type != obj.memory_type:
                            raise ValueError('memory_type')

                        if odt in (_OT.VAR, _OT.ARRAY):
                            if fobj.name != obj.name:
                                raise ValueError('name')
                            if fobj.data_type != obj.data_type:
                                raise ValueError('data_type')
                            if fobj.access_type != obj.access_type:
                                raise ValueError('access_type')
                            if fobj.PDO_mapping != obj.PDO_mapping:
                                raise ValueError('PDO_mapping')
                        elif odt is _OT.RECORD:
                            if fobj.access_type != obj.access_type:
                                raise ValueError('access_type')
                            if fobj.PDO_mapping != obj.PDO_mapping:
                                raise ValueError('PDO_mapping')
                    except ValueError as e:
                        lg.error((
                            'Error in object {0.index:#x}. This '
                            'object is combined with {1.index:#x}. {2!s} '
                            'must be the same').format(obj, fobj, e))
                        import sys
                        sys.exit(1)

            # Check cname is unique
            if not obj.is_combined or obj.is_first:
                if ocname in self.OD_names:
                    raise ValueError((
                        'Duplicated name for object {0:#x}: {1}'
                        '').format(index, ocname))
                else:
                    self.OD_names.append(ocname)

            # Generate code for initialization, definitions, aliases and others
            var_def_fmt = '/* {index:<10} */ {type:<31} {name};'
            var_alias_comment_fmt = '/* {index:<#8x} data type: {type} */'
            var_alias_define_fmt = '    #define {name:<49} {value}'
            var_alias_define_fmt = '    #define {name:<49} {value}'
            var_typedefs_fmt = ('/* {index:<#8x} */  typedef '
                                'struct{{\n{sub_definitions}\n}} {type};')
            subvar_def_fmt = '        {name};'
            subvar_struct_fmt = '        {{{pointer}, {attribute}, {mem_size}}}'

            if not obj.is_combined or obj.is_first:   # Not a combined object

                if obj.is_first:
                    _brackets = True
                    self.OD_H_aliases.append(var_alias_comment_fmt.format(
                        index=index, type='{}{}'.format(ocdt,
                            ', array[{}]'.format(obj.feature.count)
                            if obj.feature.count > 1 else '')))
                    var['definition'] = var_def_fmt.format(
                        index='{:#6x}[{}]'.format(index, obj.feature.count),
                        type=ocdt, name='{}{}'.format(ocname,
                            '[{}]'.format(obj.feature.count)
                            if obj.feature.count > 1 else ''))
                else:
                    self.OD_H_aliases.append(var_alias_comment_fmt.format(
                        index=index, type=ocdt + ', array' if '[' in ocdt else ''))
                    var['definition'] = var_def_fmt.format(
                            index='{:#6x}'.format(index), type=ocdt,
                        name='{}{}'.format(ocname,
                            '[{}]'.format(oclen) if odt and odt.is_array else ''))

                self.OD_H_aliases.append(var_alias_define_fmt.format(
                    name='OD{0[reference]}_{1}'.format(odi, ocname),
                    value='CO{0[reference]}_OD_{1}.{2}'.format(
                        odi, omt.name, ocname)))

                if ot is _OT.VAR and odt.is_array:
                    self.OD_H_aliases.append('    #define {:<50}{}'.format(
                        'ODL{0[reference]}_{1}_stringLength'.format(odi, ocname),
                        obj.clen))

                if ot is _OT.ARRAY:
                    # Append array length to aliases
                    self.OD_H_aliases.append(var_alias_define_fmt.format(
                        name='ODL{0[reference]}_{1}_arrayLength'.format(odi, ocname),
                        value=len(obj.children) - 1))

                if ot is _OT.RECORD:
                    subv_defs = []
                    subv_attrs = []
                    subv_struct = []
                    subv_inits = []
                    for cindex in obj.children:
                        child = obj.children[cindex]
                        subv_defs.append(subvar_def_fmt.format(
                            name=child.cname + '[{}]'.format(child.clen)
                            if child.data_type.is_array else ''))
                        subv_attrs.append(child.cattribute)
                        if child.data_type is _DT.DOMAIN:
                            ptr = '0x00'
                        else:
                            ptr = '(void*)&CO{0[reference]}_OD_{1}.{2}.{3}'.format(
                                odi, omt.name, ocname,
                                child.cname + '[0]' if child.data_type.is_array else '')
                        subv_struct.append(subvar_struct_fmt.format(
                            pointer=ptr, attribute=child.cattribute,
                            mem_size=child.clen))
                        subv_inits.append(child.cvalue)

                    self.OD_H_typedefs.append(var_typedefs_fmt.format(
                        index=index, sub_definitions='\n'.join(subv_defs),
                        type='OD{0[reference]}_{1}_t'.format(odi, ocname)))
            # End of not obj.is_combined or obj.is_first

            if ot is _OT.VAR:
                var['init'] = '/* {0:<#8x} */ {2}{{{1}}}{3},'.format(
                    index, ocvalue, *('{', '}') if _brackets else ('', ''))
            elif ot is _OT.ARRAY:
                pass    # TODO: from output.js@468

            if ot is not _OT.RECORD:
                var['attribute'] = obj.cattribute

                var['pointer'] = (
                    '(void*)&CO{0[reference]}_OD_'
                    '{1}.{2}{3}[0];'
                    '').format(
                        self.OD_info, omt.name, ocname, obj.index)  # current_count == subindex ??
            else:
                var['pointer'] = (
                    '(void*)&CO{0[reference]}_OD_'
                    '{1}.{2}{3}[0];'
                    '').format(odi, omt.name, ocname,
                               obj.index)   # current_count == subindex ??

            if obj.data_type == _DT.DOMAIN:
                self.OD_C_OD.append(
                    '{{{0:#x}, 0x00, {1.cattribute:#x}, '
                    '{1.data_type.bsize}, {2.pointer}}},");'.format(
                        index, obj, var))

            if (index not in self.combined_objects.keys() or
                    self.combined_objects[index]['first_index'] == index):

                self.OD_C_OD.append('')

            # Assign object its memory slot
            mt = obj.memory_type.name
            if not obj.is_combined:
                getattr(self, 'OD_H_{}'.format(mt)).append(var['definition'])
                getattr(self, 'OD_C_init{}'.format(mt)).append(var['init'])
            elif obj.is_first:
                getattr(self, 'OD_H_{}'.format(mt)).append(var['definition'])
                getattr(self, 'OD_C_init{}'.format(mt)).append(var['init'])
                # self.combined_initializations[index] = len(getattr(self, 'OD_C_init{}'.format(mt)))
                # Add index to combined_init
            else:
                getattr(self, 'OD_C_init{}'.format(mt)).insert(
                    obj.first_index, var['init'])
                # for i in range(0, len(self.combined_initializations)):
                #     if

    def dump(self):
        d = dict(**self.__dict__)
        d['OD_H_macros'] = '\n'.join(self.OD_H_macros)
        d['OD_H_typedefs'] = '\n'.join(self.OD_H_typedefs)
        d['OD_H_RAM'] = '\n'.join(self.OD_H_RAM)
        d['OD_H_EEPROM'] = '\n'.join(self.OD_H_EEPROM)
        d['OD_H_ROM'] = '\n'.join(self.OD_H_ROM)
        d['OD_H_aliases'] = '\n'.join(self.OD_H_aliases)

        d['OD_C_initRAM'] = '\n'.join(self.OD_C_initRAM)
        d['OD_C_initEEPROM'] = '\n'.join(self.OD_C_initEEPROM)
        d['OD_C_initROM'] = '\n'.join(self.OD_C_initROM)
        d['OD_C_records'] = '\n'.join(self.OD_C_records)

        d['OD_C_functions'] = '\n'.join(self.OD_C_functions)
        d['OD_C_OD'] = '\n'.join(self.OD_C_OD)
        d['OD_C_OD_length'] = len(self.OD_C_OD)

        # d['OD_names'] = '\n'.join(self.OD_names)
        return d

    @property
    def is_populated(self):
        return self._populated

    @property
    def c_file(self):
        return CO_OD_C.format(**self.dump())

    @property
    def h_file(self):
        return CO_OD_H.format(**self.dump())
