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

    def write(self, **kwargs):
        if not self.is_populated:
            self.populate()

        c_file = kwargs.get('c_file', None)
        h_file = kwargs.get('h_file', None)

        if c_file:
            with c_file as f:
                f.write(self.c_file)
        else:
            lg.warn('C file not specified, skipping.')

        if h_file:
            pass
        else:
            lg.warn('H file not specified, skipping.')

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

            lg.debug('{0.index:#x} {0.uid} c{0.is_combined:d} f{0.is_first:d} {0.feature}'.format(obj))
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
            var_init_fmt = '/* {index:<#8x} */ {value},'
            var_alias_comment_fmt = '/* {index:<#8x} data type: {type} */'
            var_alias_define_fmt = '    #define {name:<49} {value}'
            var_alias_define_fmt = '    #define {name:<49} {value}'
            var_typedefs_fmt = ('/* {index:<#8x} */  typedef '
                                'struct{{\n{sub_definitions}\n}} {type};')
            var_pointer_fmt = '(void*)&{name}'
            var_OD_record_fmt = ('/* {index:<#8x} */ const CO_OD_entryRecord_t {name} ='
                                 '{{\n{sub_structures}\n}};')
            var_OD_entry_fmt = '    {{{index:#x}, {length:#04x}, {attribute:#04x}, {mem_size:}, {pointer}}},'

            subvar_def_fmt = '        {type:<19} {name};'
            subvar_struct_fmt = '        {{{pointer}, {attribute:#04x}, {mem_size:}}}'

            # First, generate data for subobjects if any
            if ot is _OT.ARRAY:
                # First subobject in an array defines array size
                array_init = [sobj.cvalue for sobj in obj.children.values()][1:]
                # TODO: Check memory_size for combined objects
            elif ot is _OT.RECORD:
                record_init = [sobj.cvalue for sobj in obj.children.values()]
                record_definitions = []
                record_aliases = []
                record_struct = []
                for sobj in obj.children.values():
                    if sobj.uid in record_aliases:  # Check if subobject name is unique inside this object
                        raise ValueError(
                            'sub_object {:#x} must have a unique name in {:#x}'
                            .format(sobj.index, index))

                    record_aliases.append(sobj.uid)

                    socdt = '{}{}'.format(sobj.cdata_type,
                        '[{}]'.format(sobj.clen)
                        if sobj.data_type.is_array else '')
                    record_definitions.append(socdt)

                    if sobj.data_type is _DT.DOMAIN:
                        ptr = '0x00'
                    else:
                        ptr = var_pointer_fmt.format(
                            name='CO{0[reference]}_OD_{1}.{2}[{3}].{4}'.format(
                                odi, omt.name, ocname, obj.feature_position,
                                sobj.uid + ('[0]' if sobj.data_type.is_array else '')))

                    record_struct.append(subvar_struct_fmt.format(
                        pointer=ptr, attribute=sobj.cattribute, mem_size=sobj.clen))
            # End of subobjects generation

            if not obj.is_combined or obj.is_first:   # Not a combined object or first combined

                if obj.is_first:
                    self.OD_H_aliases.append(var_alias_comment_fmt.format(
                        index=index, type='{}{}'.format(ocdt,
                            (', array[{}]'.format(obj.feature.count))
                            if obj.feature.count > 1 else '')))
                    var['definition'] = var_def_fmt.format(
                        index='{:#6x}[{}]'.format(index, obj.feature.count),
                        type=ocdt, name='{}{}'.format(ocname,
                            '[{}]'.format(obj.feature.count)
                            if obj.feature.count > 1 else ''))
                else:
                    self.OD_H_aliases.append(var_alias_comment_fmt.format(
                        index=index, type=ocdt + (', array' if '[' in ocdt else '')))
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
                elif ot is _OT.ARRAY:
                    # Append array length to aliases
                    self.OD_H_aliases.append(var_alias_define_fmt.format(
                        name='ODL{0[reference]}_{1}_arrayLength'.format(odi, ocname),
                        value=len(obj.children) - 1))
                elif ot is _OT.RECORD:
                    self.OD_H_typedefs.append(var_typedefs_fmt.format(
                        index=index, sub_definitions='\n'.join(map(lambda x, y: subvar_def_fmt.format(type=y, name=x), record_aliases, record_definitions)),
                        type='OD{0[reference]}_{1}_t'.format(odi, ocname)))
            # End of not obj.is_combined or obj.is_first

            # Initialization for object and its subobjects
            if ot is _OT.VAR:
                init_value = ocvalue
            elif ot is _OT.ARRAY:
                _cvalue = ', '.join(array_init)
                init_value = '{{{}}}'.format(_cvalue)

                # Append aliase for suboject if name is unique
                gen_aliases = True
                snames = [sobj.uid for sobj in obj.children.values()]
                for sobj in list(obj.children.values())[1:]:
                    if snames.count(sobj.uid) > 1:
                        gen_aliases = False
                        break

                if gen_aliases:
                    self.OD_H_aliases += [var_alias_define_fmt.format(
                        name='ODA{0[reference]}_{1}_{2}'.format(odi, ocname, sobj.uid),
                        value=sobj.index - 1) for sobj in list(obj.children.values())[1:]]
                    # Substract 1 because the first element of an array is the size
            elif ot is _OT.RECORD:
                _cvalue = ', '.join(record_init)
                init_value = '{{{}}}'.format(_cvalue)

                self.OD_C_records.append(var_OD_record_fmt.format(
                    index=index, sub_structures=',\n'.join(record_struct),
                    name='OD{0[reference]}_record{1:X}[{2}]'.format(
                        odi, index, obj.clen)))

            if obj.is_first:
                init_value = '{' + init_value
            elif obj.is_last:
                init_value = init_value[:-1] + '}}'

            var['init'] = var_init_fmt.format(index=index, value=init_value)
            # End of initialization for object and its subobjects

            # Pointer generation
            if ot in (_OT.VAR, _OT.ARRAY):
                if odt is _DT.DOMAIN:
                    var_pointer = "0x00"
                else:
                    var_pointer = var_pointer_fmt.format(
                        name='CO{0[reference]}_OD_{1}.{2}{3}{4}'.format(
                            odi, omt.name, ocname, obj.feature_position if obj.feature_position else '',
                            ''.join(('[0]' if ot is _OT.ARRAY else '', '[0]' if odt.is_array else ''))
                        ))
            else:
                var_pointer = var_pointer_fmt.format(
                    name='CO{0[reference]}_record{1:X}'.format(odi, index))

            # # VAR
            # CO_OD_C_OD.push("{0x"+index+", 0x00, 0x"+g_byteToHexString(attribute)+",
            #         "+defaultValueMemorySize+", "+
            #     varPtr+"},");
            # # ARRAY
            # CO_OD_C_OD.push("{0x"+index+", 0x"+g_byteToHexString(subNumberVal-1)+",
            #         0x"+g_byteToHexString(attribute)+", "+subDefaultValueMemorySize+", "+
            #     varPtr+"},");
            # # RECORD
            # CO_OD_C_OD.push("{0x"+index+", 0x"+g_byteToHexString(subNumberVal-1)+", 0x00,  0, (void*)&"+
            #     "OD"+ODfileNameReference+"_record"+index+"},");

            # Add data to OD
            self.OD_C_OD.append(var_OD_entry_fmt.format(
                index=index, length=(len(obj.children) - 1) if obj.children else 0,
                attribute=obj.cattribute, mem_size=obj.clen if ot is not _OT.RECORD else 0,
                pointer=var_pointer))

            # Extralines
            if not obj.is_combined or obj.is_first:
                self.OD_C_OD.append('')         # Add extraline at the end of OD
                self.OD_H_aliases.append('')    # Add extraline at the end of aliases

            # Assign object its memory slot
            if not obj.is_combined:
                getattr(self, 'OD_H_{}'.format(omt.name)).append(var['definition'])
                getattr(self, 'OD_C_init{}'.format(omt.name)).append(var['init'])
            elif obj.is_first:
                getattr(self, 'OD_H_{}'.format(omt.name)).append(var['definition'])
                getattr(self, 'OD_C_init{}'.format(omt.name)).append(var['init'])
                # self.combined_initializations[index] = len(getattr(self, 'OD_C_init{}'.format(mt)))
                # Add index to combined_init
            else:
                getattr(self, 'OD_C_init{}'.format(omt.name)).insert(
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
