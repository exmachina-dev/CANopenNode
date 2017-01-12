# -*- coding: utf-8 -*-

from OD_types import MemoryType as _MT
from OD_types import DataType as _DT
from OD_types import ObjectType as _OT
from OD_types import AccessType as _AT
from OD_types import PDOMapping as _PM


class Object(object):
    def __init__(self, **kwargs):
        self.parent = kwargs.get('parent', None)

        try:
            self.name = kwargs['name']
            obt = getattr(_OT, kwargs['object_type'])
            self.object_type = obt

        except KeyError as e:
            key = e.args[0]
            if 'name' in kwargs:
                raise ValueError(
                    'Missing required argument for \'{}\': {}'
                    .format(kwargs['name'], key))
            else:
                raise ValueError(
                    'Missing required argument: {}'''.format(key))
        except AttributeError as e:
            btype, = e.args
            raise ValueError('Bad type: \'{0}\''.format(btype))

        self.data_type = None
        self.access_type = None
        try:
            dt, at = kwargs['data_type'], kwargs['access_type']
            self.data_type = getattr(_DT, dt) if dt else None
            self.access_type = getattr(_AT, at) if at else None
        except KeyError as e:
            if obt is not _OT.RECORD:
                raise ValueError(
                    'Missing required argument for \'{}\': {}'
                    .format(kwargs['name'], key))

        self.memory_type = kwargs.get('memory_type', None)
        try:
            if self.memory_type:
                self.memory_type = getattr(_MT, self.memory_type)
        except AttributeError:
            raise ValueError('Bad memory type: \'{}\''.format(self.memory_type))

        self.description = kwargs.get('description', '')
        self.default = kwargs.get('default', None)
        self.disabled = kwargs.get('disabled', False)

        self.PDO_mapping = kwargs.get('PDO_mapping', None)
        self.TPDO_detect_COS = kwargs.get('TPDO_detect_COS', None)

        self._is_child = False

        self._children = {}

        if self.parent:
            self._is_child = True

        self.access_function_name = kwargs.get('access_function_name', None)
        self.access_function_precode = kwargs.get('access_function_precode', None)
        self.access_function_postcode = kwargs.get('access_function_postcode', None)

        if self.default is not None:
            self.default = self._detect_dt()

        self.value = self.default

    def add_child(self, subindex, **child):
        if self.is_child:
            raise Exception("Child object cannot contain children.")

        if subindex in self.children.keys():
            raise ValueError('Subindex already exists in \
                             object {!r}'.format(self))

        child.pop('parent', None)

        if 'data_type' not in child.keys():
            child['data_type'] = self.data_type.name

        if 'access_type' not in child.keys():
            child['access_type'] = self.access_type.name

        self._children[subindex] = Object(parent=self, **child)

    def dump(self):
        if not hasattr(self, 'data_type'):
            raise Exception

        return {
            'name': self.name,
            'description': self.description,
            'object_type': self.object_type.name or None,
            'data_type': self.data_type.name if self.data_type else None,
            'memory_type': self.memory_type.name if self.memory_type else None,
            'access_type': self.access_type.name if self.access_type else None,
            'PDO_mapping': self.PDO_mapping.name if self.PDO_mapping else None,
            'access_function_name': self.access_function_name if self.access_function_name else None,
            'access_function_precode': self.access_function_precode if self.access_function_precode else None,
            'access_function_postcode': self.access_function_postcode if self.access_function_postcode else None,
            'disabled': self.disabled,
            'default': self.default,
            'parent': self.parent,
        }

    @property
    def cdatatype(self):
        dt = self.data_type.cname

        if self.data_type in (_DT.VSTRING, _DT.OSTRING, _DT.USTRING):
            if self.value is None:
                dt += '[0]'
            else:
                dt += '[{:d}]'.format(len(self.value))

        return dt

    @property
    def clen(self):
        if self.data_type.is_signed_integer or self.data_type.is_unsigned_integer:
            return self.data_type.bsize
        elif self.data_type.is_array:
            return len(self.value) if self.value is not None else 0

    @property
    def cvalue(self):
        if self.data_type.is_signed_integer or self.data_type.is_unsigned_integer:
            max_range = 2 ** self.data_type.bsize

            if self.data_type.is_unsigned_integer:
                min_range = 0
            else:
                min_range = max_range * -1 - 1

            self.value = 0 if self.value is None else self.value
            if not min_range <= self.value <= max_range:
                raise ValueError('Invalid default value for {0.data_type}: \
                                 {0.default}'.format(self))
        elif self.data_type.is_array:
            return '{\'' + '\', \''.join(*self.default) + '\'}' if self.default is not None else '{}'

    @property
    def cattribute(self):
        attr = self.memory_type.value

        if self.access_type != _AT.WO:
            attr |= 0x04
        if self.access_type in (_AT.WO, _AT.RW):
            attr |= 0x08
        if self.PDO_mapping in (_PM.OPT, _PM.RPDO):
            attr |= 0x10
        if self.PDO_mapping in (_PM.OPT, _PM.TPDO):
            attr |= 0x20
        if self.TPDO_detect_COS:
            attr |= 0x40
        if self.data_type.bsize not in (-1, 1):
            attr |= 0x80

        return attr

    @property
    def uid(self):
        tokens = self.name.strip()
        tokens = tokens.split()
        uid = ''
        for token in tokens:
            if len(token) >= 2:
                utoken = token[0].upper() + token[1:]
            else:
                utoken = token
            uid += utoken

        return uid

    @property
    def children(self):
        return self._children

    @property
    def is_child(self):
        return self._is_child

    def _detect_dt(self):
        if '$NODEID+' in self.default.replace(' ', ''):
            self.add_nodeid = True
            self.default = self.default.replace(' ', '').replace('$NODEID+', '')

        if self.data_type in (_DT.INT8,):
            return int(self.default)

    def __str__(self):
        if self.is_child:
            return '{name:30}'.format(**self.dump())
        else:
            return '{name:30} ({children:d})'.format(children=len(self.children), **self.dump())


class ObjectDirectory(object):
    def __init__(self):
        self.features = {}
        self.objects = {}

    def add_feature(self, name):
        name = name.upper()

        if name in self.features.keys():
            raise ValueError('Feature {} already exists.'.format(name))

    def add_object(self, index, obj):
        if index in self.objects.keys():
            raise ValueError('Object with index {} already \
                             exists.'.format(index))

        if not isinstance(obj, Object):
            raise ValueError('Wrong type for {!r}'.format(obj))

        self.objects[index] = obj

    def tree(self):
        for index in self.objects.keys():
            obj = self.objects[index]
            print('├─ {:<#6x} {!s}'.format(index, obj))
            if obj.description:
                print('│  │      {}'.format(obj.description.splitlines()[0][0:33]))
            children = obj.children
            for subindex in children.keys():
                print('│  ├─ {:<#4x}  {!s}'.format(subindex, children[subindex]))

            print('│')
