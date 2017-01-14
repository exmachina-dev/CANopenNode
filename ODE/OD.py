# -*- coding: utf-8 -*-

from utils import str_to_hex
from OD_types import MemoryType as _MT
from OD_types import DataType as _DT
from OD_types import ObjectType as _OT
from OD_types import AccessType as _AT
from OD_types import PDOMapping as _PM


class _AObj(object):
    def __init__(self, index=None, max_index=None, step_index=None):
        self.index = index
        self.max_index = max_index or 0
        self.step_index = step_index or 1
        self.first_index = None
        self.indexes = (index,)

    @property
    def indexes(self):
        return self._indexes

    @indexes.setter
    def indexes(self, value):
        if not isinstance(value, (list, tuple)):
            raise ValueError

        self._indexes = tuple(sorted(value))
        if len(self._indexes):
            self.first_index = self._indexes[0]
        else:
            self.first_index = None


class Feature(object):
    def __init__(self, **kwargs):
        self.parent = kwargs.get('parent', None)

        try:
            self.name = kwargs['name']
            self.value = int(kwargs['value'])
        except KeyError as e:
            key = e.args[0]
            if 'name' in kwargs:
                raise ValueError(
                    'Missing required argument for \'{}\': {}'
                    .format(kwargs['name'], key))
            else:
                raise ValueError(
                    'Missing required argument: {}'''.format(key))

        self.description = kwargs.get('description', '')
        self.label = kwargs.get('label', '')

        self._associated_objects = kwargs.get('associated_objects', {})

        if not self._associated_objects:
            for key in sorted(kwargs.keys()):
                if 'associated_object.' in key:
                    value = kwargs.get(key)
                    i = str_to_hex(key.replace('associated_object.', '')
                                   .replace('.max_index', '')
                                   .replace('.step_index', ''))

                    if i not in self._associated_objects.keys():
                        self._associated_objects[i] = _AObj(i)

                    if '.max_index' in key:
                        mindex = str_to_hex(value)
                        if mindex <= i:
                            raise ValueError(
                                'max_index cannot be <= than index: {:#x} <= {:#x}'
                                .format(mindex, i))
                        self._associated_objects[i].max_index = str_to_hex(value)
                    elif '.step_index' in key:
                        self._associated_objects[i].step_index = int(value)

        # Append all possible indexes to associated object
        for aobj in self._associated_objects.values():
            if aobj.max_index:
                if self.value:
                    max_index = aobj.index + (self.value * aobj.step_index) + 1
                    aobj.indexes = list(range(aobj.index, max_index, aobj.step_index))
                else:
                    aobj.indexes = list(range(aobj.index, aobj.max_index, aobj.step_index))

        self.first_indexes = [aobj.first_index for aobj in self.associated_objects.values()]

    def dump(self):
        return {
            'name': self.name,
            'description': self.description,
            'label': self.label or None,
            'associated_objects': self.associated_objects,
            'value': self.value,
        }

    def is_combined(self, index):
        return index in self.indexes

    def is_first(self, index):
        return index in self.first_indexes

    def first_index_of(self, index):
        for aobj in self._associated_objects.values():
            if index in aobj.indexes:
                return aobj.first_index

    def index_of(self, index):
        for aobj in self._associated_objects.values():
            try:
                return aobj.indexes.index(index)
            except ValueError:
                continue

    @property
    def associated_objects(self):
        return self._associated_objects

    @property
    def count(self):
        if self.value <= self.max_count:
            return self.value
        return self.max_count

    @property
    def max_count(self):
        c = 0
        for aobj in self._associated_objects.values():
            c += len(aobj.indexes)
        return c

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
    def macro_name(self):
        return self.uid

    @property
    def indexes(self):
        indexes = list()
        for aobj in self.associated_objects.values():
            for i in aobj.indexes:
                indexes.append(i)
        return indexes

    def __contains__(self, item):
        if item in self.indexes:
            return True
        return False

    def __str__(self):
        return '{name:30} ({count})'.format(count=self.count, **self.dump())


class Object(object):
    def __init__(self, **kwargs):
        self._is_child = False
        self.parent = kwargs.get('parent', None)
        if self.parent:
            self._is_child = True

        try:
            self.name = kwargs['name']
            self.index = kwargs['index']
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
            dt = kwargs.get('data_type', self.parent.data_type if self.is_child else None)
            at = kwargs.get('access_type', self.parent.access_type if self.is_child else None)
            if dt is None:
                raise KeyError('data_type')
            if at is None:
                raise KeyError('access_type')

            self.data_type = getattr(_DT, dt) if dt else None
            self.access_type = getattr(_AT, at) if at else None
        except KeyError as e:
            if obt is not _OT.RECORD:
                raise ValueError(
                    'Missing required argument for \'{}\': {}'
                    .format(kwargs['name'], key))

        self.memory_type = kwargs.get('memory_type',
            self.parent.memory_type.name if self.is_child else None)
        try:
            if self.memory_type:
                self.memory_type = getattr(_MT, self.memory_type)
        except AttributeError:
            raise ValueError('Bad memory type: \'{}\''.format(self.memory_type))

        self.description = kwargs.get('description', '')
        self.default = kwargs.get('default', None)
        self.value = kwargs.get('value', None)
        self.disabled = kwargs.get('disabled', False)

        self.PDO_mapping = kwargs.get('PDO_mapping', None)
        self.TPDO_detect_COS = kwargs.get('TPDO_detect_COS', None)

        self._is_child = False

        self._children = {}
        self._feature = None

        self.access_function_name = kwargs.get('access_function_name', None)
        self.access_function_precode = kwargs.get('access_function_precode', None)
        self.access_function_postcode = kwargs.get('access_function_postcode', None)

        if self.default is not None:
            self.default = self._detect_dt(self.default)

        if self.value is not None:
            self.value = self._detect_dt(self.value)
        else:
            self.value = self.default

    def add_feature(self, feature):
        if self.feature is not None:
            raise Exception("Object is already part of a feature.")

        if not isinstance(feature, Feature):
            raise ValueError("Unexpected type for feature.")

        self._feature = feature

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

        self._children[subindex] = Object(index=subindex, parent=self, **child)

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
    def feature(self):
        return self._feature

    @property
    def is_first(self):
        return self.is_combined and self.feature.is_first(self.index)

    @property
    def is_combined(self):
        if self.feature is not None:
            return self.feature.is_combined(self.index)
        return False

    @property
    def feature_position(self):
        if self.feature:
            return self.feature.index_of(self.index)
        return 0

    @property
    def first_index(self):
        if self.feature is not None:
            return self.feature.first_index_of(self.index)

    @property
    def cdata_type(self):
        if self.object_type is _OT.RECORD:  # data_type is custom for RECORDS
            return 'OD_{}_t'.format(self.uid)

        return self.data_type.cname

    @property
    def clen(self):
        if self.object_type is _OT.RECORD:
            return len(self.children)
        elif self.data_type.is_signed_integer or self.data_type.is_unsigned_integer:
            return self.data_type.bsize
        elif self.data_type is _DT.VSTRING:
            return len(self.value) if self.value is not None else 0
        elif self.data_type in (_DT.OSTRING, _DT.USTRING):
            return len(self.value.split(' ')) if self.value is not None else 0

    @property
    def cvalue(self):
        if self.object_type is _OT.RECORD:
            return str(self.value)
        elif self.data_type.is_integer:
            max_range = 2 ** (8 * self.data_type.bsize)

            if self.data_type.is_unsigned_integer:
                min_range = 0
            else:
                min_range = max_range * -1 - 1

            self.value = 0 if self.value is None else self.value

            if not min_range <= self.value:
                raise ValueError('Invalid value for {0.data_type}: '
                                 '{0.default} < {1}'.format(self, min_range))
            elif not self.value <= max_range:
                raise ValueError('Invalid value for {0.data_type}: '
                                 '{0.default} > {1}'.format(self, max_range))

            if self.data_type.bsize >= 8:
                return '{:#014x}L'.format(self.value)
            elif self.data_type.bsize >= 4:
                return '{:#010x}'.format(self.value)
            elif self.data_type.bsize >= 2:
                return '{:#006x}'.format(self.value)
            else:
                return '{:#04x}'.format(self.value)
        elif self.data_type.is_array:
            if self.data_type is _DT.OSTRING:
                octets = ['{:#04x}'.format(str_to_hex(x)) for x in self.value.split(' ')]
                return '{{{}}}'.format(', '.join(octets))
            return '{{\'{}\'}}'.format('\', \''.join(tuple(self.value))) if self.value is not None else '{}'

    @property
    def cattribute(self):
        try:
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
        except AttributeError:
            attr = 0x00

        return attr

    @property
    def uid(self):
        tokens = self.name.strip().replace('-', ' ').replace('_', ' ')
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

    def _detect_dt(self, v):
        if '$NODEID+' in v.replace(' ', ''):
            self.add_nodeid = True
            v = v.replace(' ', '').replace('$NODEID+', '')

        if self.data_type.is_integer:
            if v[0:2].lower() == '0x':
                return str_to_hex(v)
            else:
                return int(v)

        return v

    def __str__(self):
        if self.is_child:
            return '{name:30}'.format(**self.dump())
        else:
            return '{name:30} ({children:d})'.format(children=len(self.children), **self.dump())


class ObjectDirectory(object):
    def __init__(self):
        self.features = {}
        self.objects = {}

    def add_feature(self, feature):
        if feature.name in self.features.keys():
            raise ValueError('Feature {} already exists.'.format(feature.name))

        if not isinstance(feature, Feature):
            raise ValueError('Wrong type for {!r}'.format(feature))

        self.features[feature.name] = feature

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
            print('├─ {0:<#6x} {1!s} {1.object_type.name}'.format(index, obj))
            if obj.description:
                print('│  │      {}'.format(obj.description.splitlines()[0][0:33]))
            children = obj.children
            for subindex in children.keys():
                print('│  ├─ {:<#4x}  {!s}'.format(subindex, children[subindex]))

            print('│')
