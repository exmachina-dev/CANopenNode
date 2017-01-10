# -*- coding: utf-8 -*-

import OD_types as ODT


class Object(object):
    def __init__(self, **kwargs):
        self.parent = kwargs.get('parent', None)

        try:
            self.name = kwargs['name']
            obt = getattr(ODT.ObjectType, kwargs['object_type'])
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
            self.data_type = getattr(ODT.DataType, dt) if dt else None
            self.access_type = getattr(ODT.AccessType, at) if at else None
        except KeyError as e:
            if obt is not ODT.ObjectType.RECORD:
                raise ValueError(
                    'Missing required argument for \'{}\': {}'
                    .format(kwargs['name'], key))

        self.memory_type = kwargs.get('memory_type', None)
        try:
            if self.memory_type:
                self.memory_type = getattr(ODT.MemoryType, self.memory_type)
        except AttributeError:
            raise ValueError('Bad memory type: \'{}\''.format(self.memory_type))
        self.description = kwargs.get('description', '')
        self.default = kwargs.get('default', None)
        self._is_child = False

        self._children = {}

        if self.parent:
            self._is_child = True

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
            'default': self.default,
            'parent': self.parent,
        }

    @property
    def children(self):
        return self._children

    @property
    def is_child(self):
        return self._is_child

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
