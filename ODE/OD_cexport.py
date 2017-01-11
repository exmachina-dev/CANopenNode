# -*- coding: utf-8 -*-

import logging

from OD import ObjectDirectory

from OD_types import MemoryType as _MT
from OD_types import DataType as _DT
from OD_types import ObjectType as _OT
from OD_types import AccessType as _AT
from OD_types import PDOMapping as _PM

lg = logging.getLogger(__name__)


class CExport(object):
    def __init__(self, od):
        if not isinstance(od, ObjectDirectory):
            raise TypeError('od must be an {} instance.'.format(type(ObjectDirectory)))

        self.OD_H_info = []
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
                    for i in range(aobj.index, aobj.max_index, aobj.index_step):
                        aobjs.append(i)
                        self.combined_objects[i] = {
                            'first_index': aobj.index,
                            'count': aobj.index - i,
                        }
                        if (aobj.index - i) >= feature.value:
                            break
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
                'CO{0.OD_H_info.reference}_NO_{1.macro_name}'
                .format(self, feature), feature.value, aobjs_comment))

    def gen_objects(self):

        # CO_ODF(void*, UINT16…)
        self.OD_C_functions.append(
            'UNSIGNED32 CO_ODF{0.OD_C_info.reference}(void*, UNSIGNED16, \
                    UNSIGNED8, UNSIGNED16*, UNSIGNED16, UNSIGNED8, void*, \
                    const void*);'.format(self))

        for index in self.OD.objects:
            obj = self.OD.objects[index]
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
                    except ValueError as e:
                        lg.error('Error in object {0.index:#x}. This \
                            object is combined with {1.index:#x}. {2!s} \
                            must be the same'.format(obj, fobj, e))

            if index not in self.combined_objects.keys():
                if obj.uid in self.OD_names:
                    raise ValueError('Duplicated name for object {0:#x}: \
                        {1.uid}'.format(index, obj))
                else:
                    self.OD_names.append(obj.uid)

            if obj.object_type == _OT.VAR:
                default_msize = obj.bsize

                # TODO: handle combined objects
                if index not in self.combined_objects.keys():
                    self.OD_H_aliases.append('/* {:#x}, data type: {.name} */'.format(
                        index, obj.data_type))
                elif self.combined_objects[index]['first_index'] == index:
                    cobj = self.combined_objects[index]
                    cobj['data_type'] = obj.data_type
                    cobj['access_type'] = obj.access_type
                    cobj['PDO_mapping'] = obj.PDO_mapping
                    cobj['default_msize'] = default_msize

                    self.OD_H_aliases.append('/* {:#x}, data type: {.name}{} */'.format(
                        index, obj.data_type,
                        ', array[{}]'.format(cobj) if cobj['count'] else ''))
                    self.OD_H_aliases.append(
                        '    #define OD{0.reference}_{1.uid:<40}\
                        CO{0.reference}_OD_{1.memory_type}.{1.uid}'.format(
                            self.OD_H_info, obj))
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

                var['init'] = '/* {:#x} */ {}{}/varI'   # TODO
            elif obj.object_type == _OT.ARRAY:
                pass
            elif obj.object_type == _OT.RECORD:
                pass

            if obj.memory_type is _MT.RAM:
                pass
            elif obj.memory_type is _MT.RAM:
                pass
            elif obj.memory_type is _MT.RAM:
                pass

    def get_value(self, obj):
        dt = obj.data_type

        max_range = 2 ** dt.bsize

        if obj.data_type in (_DT.UINT8, _DT.UINT16, _DT.UINT24, _DT.UINT32,
                             _DT.UINT40, _DT.UINT48, _DT.UINT56, _DT.UINT64):
            min_range = 0
        else:
            min_range = max_range * -1 - 1

        if not min_range <= obj.default <= max_range:
            raise ValueError('Invalid default value for {0.data_type}: \
                             {0.default}'.format(obj))

    def get_attr(self, obj):
        attr = obj.memory_type

        if obj.access_type != _AT.WO:
            attr |= 0x04
        if obj.access_type in (_AT.WO, _AT.RW):
            attr |= 0x08
        if obj.PDO_mapping in (_PM.OPT, _PM.RPDO):
            attr |= 0x10
        if obj.PDO_mapping in (_PM.OPT, _PM.TPDO):
            attr |= 0x20
        if obj.TPDO_detect_COS:
            attr |= 0x40
        if obj.data_type.bsize not in (-1, 1):
            attr |= 0x80

        return attr

    @property
    def is_populated(self):
        return self._populated
