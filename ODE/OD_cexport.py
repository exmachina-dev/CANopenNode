# -*- coding: utf-8 -*-

import logging

from OD import ObjectDirectory

# from OD_types import MemoryType as _MT
from OD_types import DataType as _DT
from OD_types import ObjectType as _OT
# from OD_types import AccessType as _AT
# from OD_types import PDOMapping as _PM

lg = logging.getLogger(__name__)


class CExport(object):
    def __init__(self, od):
        if not isinstance(od, ObjectDirectory):
            raise TypeError('od must be an {} instance.'.format(type(ObjectDirectory)))

        self.OD_info = {
            'reference': '',
        }
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
        for feature in self.OD.features:
            aobjs = []

            for aobj in feature.associated_objects:
                if aobj.index_step < 1:
                    aobj.index_step = 1
                if aobj.max_index:
                    nbr = 0
                    for i in range(aobj.index, aobj.max_index, aobj.index_step):
                        aobjs.append(i)
                        self.combined_objects[i] = {
                            'first_index': aobj.index,
                            'current_count': nbr,
                        }
                        nbr += 1
                        if nbr >= feature.value:
                            break

                    self.combined_objects[aobj.index]['count'] = nbr
                else:
                    aobjs.append(i)

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

            print(aobjs)

    def gen_objects(self):

        # CO_ODF(void*, UINT16…)
        self.OD_C_functions.append((
            'UNSIGNED32 CO_ODF{0.OD_info[reference]}(void*, UNSIGNED16, '
            'UNSIGNED8, UNSIGNED16*, UNSIGNED16, UNSIGNED8, void*, const void*);'
            '').format(self))

        for index, obj in self.OD.objects.items():
            print(index)
            var = {}

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

            cobj = {}

            if index in self.combined_objects.keys():
                cobj = self.combined_objects[index]
                if cobj['first_index'] == index:
                    cobj['name'] = obj.name
                    cobj['object_type'] = obj.object_type
                    cobj['sub_number'] = obj.sub_number
                    cobj['memory_type'] = obj.memory_type
                else:
                    fobj = self.combined_objects[cobj['first_index']]
                    try:
                        if fobj['name'] != obj.name:
                            raise ValueError('name')
                        if fobj['object_type'] != obj.object_type:
                            raise ValueError('object_type')
                        if fobj['sub_number'] != obj.sub_number:
                            raise ValueError('sub_number')
                        if fobj['memory_type'] != obj.memory_type:
                            raise ValueError('memory_type')

                        self.combined_objects[cobj['first_index']] = fobj
                    except ValueError as e:
                        lg.error((
                            'Error in object {0.index:#x}. This '
                            'object is combined with {1.index:#x}. {2!s} '
                            'must be the same').format(obj, fobj, e))

                self.combined_objects[index] = cobj

            if index not in self.combined_objects.keys():
                if obj.uid in self.OD_names:
                    raise ValueError((
                        'Duplicated name for object {0:#x}: {1.uid}'
                        '').format(index, obj))
                else:
                    self.OD_names.append(obj.uid)

            if obj.object_type == _OT.VAR:
                default_msize = obj.data_type.bsize

                _brackets = False

                if index not in self.combined_objects.keys():
                    cdt = obj.cdatatype
                    var['definition'] = (
                        '/* {:#x} */  {:<15};'
                        '').format(index, '{}[{}]'.format(
                            obj.uid, obj.clen if obj.data_type.is_array else ''))

                    self.OD_H_aliases.append((
                        '/* {:#x}, data type: {}{} */'
                        '').format(index, cdt, 'array' if '[' in cdt else ''))
                    self.OD_H_aliases.append((
                        '    #define OD{0[reference]}_{1.uid:<40}'
                        'CO{0[reference]}_OD_{1.memory_type}.{1.uid}'
                        '').format(self.OD_info, obj))

                elif self.combined_objects[index]['first_index'] == index:
                    cobj = self.combined_objects[index]
                    cobj['data_type'] = obj.data_type
                    cobj['access_type'] = obj.access_type
                    cobj['PDO_mapping'] = obj.PDO_mapping
                    cobj['default_msize'] = default_msize
                    _brackets = True
                    self.combined_objects[index] = cobj

                    self.OD_H_aliases.append('/* {:#x}, data type: {.name}{} */'.format(
                        index, obj.data_type,
                        ', array[{}]'.format(cobj) if cobj['count'] else ''))
                    self.OD_H_aliases.append(
                        '    #define OD{0[reference]}_{1.uid:<40}\
                        CO{0[reference]}_OD_{1.memory_type}.{1.uid}'.format(
                            self.OD_info, obj))
                else:   # Next combined objects
                    try:
                        if cobj['first_index']['data_type'] != obj.data_type:
                            raise ValueError('data_type')
                        if cobj['first_index']['access_type'] != obj.access_type:
                            raise ValueError('access_type')
                        if cobj['first_index']['PDO_mapping'] != obj.PDO_mapping:
                            raise ValueError('PDO_mapping')
                        if cobj['first_index']['default_msize'] != default_msize:
                            raise ValueError('length of default value')
                    except ValueError as e:
                        lg.error('Error in object {0.index:#x}. This \
                            object is combined with {1.index:#x}. {2!s} \
                            must be the same'.format(obj, fobj, e))

                var['init'] = '/* {0:#x} */ {2[0]}{{{1}}}{2[1]},'.format(
                    index, obj.cvalue, '{}' if _brackets else '  ')
                var['attribute'] = obj.cattribute

                if obj.data_type.is_array:
                    if (index not in self.combined_objects.keys() or
                            self.combined_objects[index]['first_index'] == index):

                        self.OD_H_aliases.append('      #define {:<50} {}'.format(
                            'ODL{0[reference]}_{1.uid}_stringLength'.format(self.OD_info, obj),
                            obj.clen))

                    var['pointer'] = (
                        '(void*)&CO{0[reference]}_OD_'
                        '{1.memory_type.name}.{1.uid}{2}[0];'
                        '').format(
                            self.OD_info, obj, cobj.get('current_count', ''))
                else:
                    var['pointer'] = (
                        '(void*)&CO{0[reference]}_OD_'
                        '{1.memory_type.name}.{1.uid}{2}[0];'
                        '').format(self.OD_info, obj,
                                   cobj.get('current_count', ''))

                if obj.data_type == _DT.DOMAIN:
                    self.OD_C_OD.append(
                        '{{0:#x}, 0x00, {1.cattribute:#x}, '
                        '{1.data_type.bsize}, {2.pointer}},");'.format(
                            index, obj, var))

                if (index not in self.combined_objects.keys() or
                        self.combined_objects[index]['first_index'] == index):

                    self.OD_C_OD.append('')
            elif obj.object_type == _OT.ARRAY:
                var['definition'] = '// ARRAY'
                var['init'] = '// ARRAY'
            elif obj.object_type == _OT.RECORD:
                var['definition'] = '// RECORD'
                var['init'] = '// RECORD'

            mt = obj.memory_type.name
            if index not in self.combined_objects:
                getattr(self, 'OD_H_{}'.format(mt)).append(var['definition'])
                getattr(self, 'OD_C_init{}'.format(mt)).append(var['init'])
            elif self.combined_objects[index]['first_index'] == index:
                getattr(self, 'OD_H_{}'.format(mt)).append(var['definition'])
                getattr(self, 'OD_C_init{}'.format(mt)).append(var['init'])
                self.combined_initializations[index] = len(getattr(self, 'OD_C_init{}'.format(mt)))
                # Add index to combined_init
            else:
                getattr(self, 'OD_C_init{}'.format(mt)).insert(
                    self.combined_objects['index']['first_index'], var['init'])
                # for i in range(0, len(self.combined_initializations)):
                #     if

    @property
    def is_populated(self):
        return self._populated
